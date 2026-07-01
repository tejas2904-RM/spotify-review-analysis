# Implementation Plan — Spotify Review Discovery Engine

This document turns the phase-wise design in [`Architecture.md`](./Architecture.md) into an actionable, step-by-step implementation plan. It covers the tech stack decision, milestones, per-phase tasks with deliverables, file-level scaffolding, and an end-to-end build sequence.

---

## 0. Guiding Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python 3.11+ | Best ecosystem for scraping + NLP + LLMs |
| Dashboard | **Next.js** (App Router, TypeScript) + FastAPI | Production-grade UI with full component control |
| Database (MVP) | SQLite | Zero-setup; swap to PostgreSQL later |
| Vector store | ChromaDB (local) | Simple, file-based, good for embeddings |
| LLM provider | **OpenAI GPT-4o-mini** | Fast, cheap (~$0.12/full run), reliable JSON output; 500 RPM paid tier |
| Embeddings | `sentence-transformers` (local) | Free, offline, fast for clustering |
| Orchestration (MVP) | CLI pipeline (`pipeline.py`) | Airflow/Prefect later if needed |

> The plan is built so the MVP stack (Streamlit + SQLite + Chroma) can be upgraded to the production stack (Next.js + FastAPI + PostgreSQL) without rewriting core logic.

---

## 1. Milestones & Timeline

| Milestone | Scope | Est. Effort |
|-----------|-------|-------------|
| **M0 — Project Setup** | Repo, env, config, schemas | 0.5 day |
| **M1 — Ingestion** | All 4 collectors writing to `raw_reviews` | 2–3 days |
| **M2 — Processing** | Cleaning pipeline → `clean_reviews` | 1–2 days |
| **M3 — Storage** | DB models + vector store wired in | 1 day |
| **M4 — AI/NLP** | Enrichment → `enriched_reviews` | 3–4 days |
| **M5 — Insights** | Aggregations → `insights` | 1–2 days |
| **M6 — Dashboard** | Next.js + FastAPI dashboard | 2–3 days |
| **M7 — Backend Deploy** | FastAPI on Render | 0.5 day |
| **M8 — Frontend Deploy** | Next.js on Vercel | 0.5 day |

**Total estimate:** ~2–3 weeks for a single developer MVP.

---

## 2. Milestone 0 — Project Setup

### Tasks
1. Initialize repo structure (see Architecture "Suggested Repository Structure").
2. Create `requirements.txt`:

```
requests
google-play-scraper
google-api-python-client
playwright
beautifulsoup4
pandas
langdetect
spacy
sentence-transformers
chromadb
sqlalchemy
groq
python-dotenv
pyyaml
streamlit
plotly
pytest
```

3. Create `.env.example`:

```
GROQ_API_KEY=
YOUTUBE_API_KEY=
DB_URL=sqlite:///data/reviews.db
```

4. Create `config/sources.yaml` (config-driven sources):

```yaml
youtube:
  video_ids: [pGntmcy_HX8, JPXgCGaqreA, Ulipm6IckyE, Og_nwXhAeeA, Q8W2IGiSdhc]
google_play:
  app_id: com.spotify.music
  lang: en
  country: in
spotify_community:
  urls:
    - https://community.spotify.com/t5/Live-Ideas/Bring-back-broader-discovery-in-Discover-Weekly-less-genre/idi-p/7411990
    - https://community.spotify.com/t5/Your-Library/Resetting-Discover-Weekly/td-p/4885105
    - https://community.spotify.com/t5/Content-Questions/Why-does-the-Discover-Weekly-list-not-reflect-the-music-I-am/td-p/6459020
hacker_news:
  item_ids: [41109882, 48600236, 48297632, 36907504]
```

5. Define the shared data models in `src/storage/models.py` (SQLAlchemy) matching the schemas in Architecture phases 1–5.

**Deliverable:** Runnable skeleton repo with `python -m src.pipeline --help`.

---

## 3. Milestone 1 — Ingestion

Implement one collector module per source under `src/ingestion/`. Each exposes `fetch() -> list[RawReview]`.

### 3.1 Google Play (`src/ingestion/google_play.py`)
- Use `google-play-scraper`'s `reviews_all` / `reviews` with sort + continuation token.
- Map to unified schema; set `source="google_play"`, capture `rating`, `app_version`.

### 3.2 YouTube (`src/ingestion/youtube.py`)
- Use YouTube Data API v3 `commentThreads.list` per video ID.
- Page through `nextPageToken`; capture top-level comments + replies (parent_id).

### 3.3 Spotify Community (`src/ingestion/spotify_community.py`)
- Use Playwright to render threads; parse posts/replies with BeautifulSoup.
- Handle pagination within a thread.

### 3.4 Hacker News (`src/ingestion/hacker_news.py`)
- Use Algolia API (`/items/{id}`) to fetch the full comment tree recursively.

### Shared Concerns
- Common `RawReview` dataclass + `to_dict()`.
- Retry/backoff helper in `src/ingestion/utils.py`.
- Upsert with dedupe on `(source, id)`.

**Deliverable:** `python -m src.pipeline ingest` populates `raw_reviews`. Verify counts per source.

---

## 4. Milestone 2 — Processing & Cleaning

Implement `src/processing/clean.py`:

### Tasks
1. Load `raw_reviews` not yet in `clean_reviews`.
2. Dedup (hash exact + fuzzy near-duplicate via `rapidfuzz`).
3. Language detect (`langdetect`); flag/translate non-English (optional via LLM).
4. Clean text: strip HTML/URLs/markup, normalize whitespace, preserve emojis.
5. Spam filter heuristics (length, repetition, promo keywords).
6. Compute `token_count`; lemmatize for keyword fields (spaCy).
7. Write `clean_reviews` with `language`, `clean_text`, `is_spam`.

**Deliverable:** `python -m src.pipeline clean` produces a clean dataset; log dropped/kept counts.

---

## 5. Milestone 3 — Storage

Implement `src/storage/`:
- `db.py` — SQLAlchemy engine/session from `DB_URL`.
- `models.py` — `raw_reviews`, `clean_reviews`, `enriched_reviews`, `insights`.
- `vector.py` — ChromaDB collection for `clean_text` embeddings (store id + metadata).
- Repository helpers: `upsert`, `get_unprocessed`, `bulk_insert`.

**Deliverable:** All phases read/write through the storage layer; embeddings persisted in Chroma.

---

## 6. Milestone 4 — AI / NLP

Implement `src/ai/`:

### 6.1 LLM Client (`src/ai/llm.py`)
- **OpenAI** client using the `openai` Python library, model `gpt-4o-mini`. Falls back to Gemini 2.0 Flash or Groq Llama 3.3 70B if `OPENAI_API_KEY` is absent.
- Structured JSON output via `response_format: {"type": "json_object"}`, retries with exponential backoff, response caching keyed by `md5(system[:100] + user_prompt)` in `data/enriched/llm_cache.json`.
- Rate-limit guard: sliding 60-second window capped at 28 RPM (2 RPM headroom).

### 6.2 Per-Review Enrichment (`src/ai/enrich.py`)
For each clean review, produce:
- `sentiment` (+ score)
- `themes` (list)
- `is_feature_request` + `feature_request_text`
- `pain_point` (structured)
- `user_segment`
- `emotion/intent`

Use **mini-batching** (5 reviews per LLM call) to stay within 30 RPM; persist to `enriched_reviews`.

### 6.3 Embeddings & Clustering (`src/ai/cluster.py`)
- Generate embeddings with `sentence-transformers`.
- Cluster with HDBSCAN/KMeans → canonical theme labels (LLM names each cluster).

### 6.4 Summarization (`src/ai/summarize.py`)
- LLM summaries per theme and per source over representative samples.

**Deliverable:** `python -m src.pipeline enrich` fills `enriched_reviews` + theme clusters + summaries.

---

## 7. Milestone 5 — Insights & Aggregation

Implement `src/insights/aggregate.py` to compute, for each Dashboard Objective:
- Sentiment distribution (overall / by source / over time).
- Top themes + trend lines.
- Ranked feature requests.
- Ranked pain points (frequency × severity × sentiment).
- User-segment breakdowns.
- Cross-source unmet-need agreement.
- LLM-generated **product opportunity recommendations** with linked evidence IDs.

Persist results to `insights` (or cached JSON) keyed by metric + filters.

**Deliverable:** `python -m src.pipeline aggregate` produces dashboard-ready insights.

---

## 8. Milestone 6 — Dashboard

**Stack:** Next.js (App Router, TypeScript) + FastAPI backend + Recharts + Tailwind CSS.

### Structure
```
dashboard/
├── api/                  # FastAPI app — serves insight JSON endpoints
│   ├── main.py
│   └── routers/
│       ├── sentiment.py
│       ├── themes.py
│       ├── pain_points.py
│       ├── segments.py
│       └── opportunities.py
└── web/                  # Next.js app
    ├── app/
    │   ├── page.tsx              # Overview / landing
    │   ├── themes/page.tsx
    │   ├── sentiment/page.tsx
    │   ├── pain-points/page.tsx
    │   ├── segments/page.tsx
    │   ├── summaries/page.tsx
    │   └── opportunities/page.tsx
    ├── components/
    └── lib/api.ts               # fetch helpers for FastAPI endpoints
```

### Pages / Sections
1. **Overview** — KPI cards (total feedback, sentiment split, source mix).
2. **Themes Explorer** — ranked theme cards with drill-down to source quotes.
3. **Sentiment Trends** — time-series line chart + source comparison (Recharts).
4. **Pain Points & Feature Requests** — ranked, filterable tables.
5. **User Segmentation** — segment distribution + per-segment challenges.
6. **AI Summaries** — narrative insights per theme and source.
7. **Product Recommendations** — prioritized opportunities with supporting evidence.

### Cross-Cutting
- Global filters: source, date range, segment, sentiment, theme.
- Dark / light mode (Tailwind).
- Export to CSV.

**Deliverable:** `uvicorn dashboard/api/main:app` + `npm run dev` in `dashboard/web/`.

---

## 9. Milestone 7 — Polish & Hardening

- **Tests** (`tests/`): unit tests for collectors/cleaners; golden-set tests for AI outputs; aggregation correctness.
- **Orchestration:** `pipeline.py` supports `ingest | clean | enrich | aggregate | all`.
- **Cost/perf:** verify caching, batching, model tiering.
- **Docs:** finalize `README.md` with setup + run instructions.
- **Reproducibility:** version prompts, snapshot data, pin dependencies.

---

## 10. End-to-End Build Sequence

```bash
# 1. Setup
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
playwright install
copy .env.example .env   # fill in keys

# 2. Run the full pipeline
python -m src.pipeline ingest
python -m src.pipeline clean
python -m src.pipeline enrich
python -m src.pipeline aggregate
# or
python -m src.pipeline all

# 3. Launch API + dashboard
uvicorn dashboard.api.main:app --reload   # FastAPI on :8000
# In a separate terminal:
cd dashboard/web && npm run dev           # Next.js on :3000
```

---

## 9. Milestone 7 — Backend Deployment (Render)

Deploy the FastAPI backend to [Render](https://render.com).

### Tasks

1. **Create `render.yaml`** in the project root:

```yaml
services:
  - type: web
    name: spotify-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn dashboard.api.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GROQ_API_KEY
        sync: false
      - key: YOUTUBE_API_KEY
        sync: false
      - key: DB_URL
        sync: false
    disk:
      name: data
      mountPath: /data
      sizeGB: 1
```

2. **Update `DB_URL`** to either:
   - Keep SQLite: `sqlite:////data/reviews.db` (persistent disk)
   - Upgrade: `postgresql://...` (Render managed PostgreSQL free tier)

3. **Update CORS** in `dashboard/api/main.py`:
```python
allow_origins=["https://your-project.vercel.app", "http://localhost:3000"]
```

4. Push to GitHub → connect repo to Render → **deploy**.

**Deliverable:** `https://spotify-api.onrender.com/api/health` returns `{"status": "ok"}`.

---

## 10. Milestone 8 — Frontend Deployment (Vercel)

Deploy the Next.js dashboard to [Vercel](https://vercel.com).

### Tasks

1. **Update `next.config.ts`** to use env-driven API URL:

```ts
async rewrites() {
  return [
    {
      source: "/api/:path*",
      destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
    },
  ];
},
```

2. **Add `.env.production`** in `dashboard/web/`:

```
NEXT_PUBLIC_API_URL=https://spotify-api.onrender.com
```

3. **Import to Vercel:**
   - Connect GitHub repo
   - Set **Root Directory** → `dashboard/web`
   - Add env var: `NEXT_PUBLIC_API_URL=https://spotify-api.onrender.com`
   - Click **Deploy**

4. Vercel auto-deploys on every push to `main`. Preview deployments are created for every PR.

**Deliverable:** `https://spotify-review-analysis.vercel.app` — live public dashboard.

---

## 11. End-to-End Build Sequence (Updated)

```bash
# 1. Setup
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
playwright install
copy .env.example .env   # fill in keys

# 2. Run the full pipeline
python -m src.pipeline ingest
python -m src.pipeline clean
python -m src.pipeline relevance
python -m src.pipeline store
python -m src.pipeline enrich
python -m src.pipeline cluster
python -m src.pipeline summarize
python -m src.pipeline aggregate

# 3. Local development
uvicorn dashboard.api.main:app --reload   # FastAPI on :8000
cd dashboard/web && npm run dev           # Next.js on :3000

# 4. Deploy
# Push to GitHub
# Render: connect repo → auto-deploy FastAPI
# Vercel: connect repo → set root to dashboard/web → auto-deploy Next.js
```

---

## 12. Task Checklist

- [x] M0: Repo, env, config, models scaffolded
- [x] M1: Google Play collector
- [x] M1: YouTube collector
- [x] M1: Spotify Community collector
- [x] M1: Hacker News collector
- [x] M2: Cleaning pipeline
- [x] M3: Storage + vector store
- [x] M4: LLM client + per-review enrichment (OpenAI GPT-4o-mini)
- [x] M4: Embeddings, clustering, summarization
- [x] M5: Insight aggregations
- [x] M6: Next.js + FastAPI dashboard
- [ ] M7: Backend deployment (Render)
- [ ] M8: Frontend deployment (Vercel)

---

## 13. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scraping breakage (Spotify Community) | Missing data | Robust selectors, snapshot HTML, fallback parsing |
| YouTube/LLM API quotas & cost | Stalls, overruns | Caching, batching, quota monitoring |
| Inconsistent LLM outputs | Bad insights | Structured outputs, validation, golden tests |
| Low-quality/spam reviews | Skewed insights | Spam filtering, dedup, confidence thresholds |
| Multilingual content | Missed signals | Language detection + optional translation |
