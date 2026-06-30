# Architecture — Spotify Review Discovery Engine

This document describes the end-to-end, phase-wise architecture for the **AI-powered Review Discovery Engine** defined in [`Problemstatment.md`](./Problemstatment.md). The system collects user feedback from multiple public sources, processes it with LLM/NLP techniques, and surfaces insights through an interactive dashboard.

---

## High-Level Architecture

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Phase 1    │   │  Phase 2    │   │  Phase 3    │   │  Phase 4    │   │  Phase 5    │
│ Ingestion   │──▶│ Processing  │──▶│  Storage    │──▶│ AI / NLP    │──▶│  Insights   │
│ (Collectors)│   │ (Clean/Norm)│   │ (Data Lake) │   │ (LLM Layer) │   │ (Aggregate) │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘   └──────┬──────┘
                                                                                │
                                                                                ▼
                                                                        ┌─────────────┐
                                                                        │  Phase 6    │
                                                                        │  Dashboard  │
                                                                        │   (UI/API)  │
                                                                        └─────────────┘
```

| Layer | Responsibility | Tech |
|-------|----------------|------|
| Ingestion | Collect raw feedback from each source | Python, Playwright, official/3rd-party APIs |
| Processing | Clean, deduplicate, normalize, language-detect | Pandas, spaCy, langdetect |
| Storage | Persist raw + processed data | SQLite, Parquet, ChromaDB |
| AI / NLP | Sentiment, themes, segmentation, summaries | **Groq — Llama 3.3 70B Versatile**, sentence-transformers |
| Insights | Aggregate, score, rank pain points & opportunities | Python analytics, pandas |
| Dashboard | Visualize results interactively | **Next.js** (App Router, TypeScript) + FastAPI |

---

## Phase 1 — Data Ingestion

**Goal:** Reliably collect raw user feedback from all four sources into a unified raw schema.

### Collectors

| Source | Method | Notes |
|--------|--------|-------|
| Google Play Store Reviews | `google-play-scraper` library | Paginate by score & date; capture rating, text, timestamp, app version |
| YouTube Comments | YouTube Data API v3 (`commentThreads`) | Iterate over the 5 video IDs; capture comment, likes, author, replies |
| Spotify Community | Web scraping (Playwright/Scrapy) | Parse threads, posts, replies, kudos |
| Hacker News | HN Firebase/Algolia API | Fetch item + nested comment tree by ID |

### Unified Raw Schema

```json
{
  "id": "string",
  "source": "google_play | youtube | spotify_community | hacker_news",
  "source_url": "string",
  "author": "string | null",
  "text": "string",
  "rating": "number | null",
  "likes": "number | null",
  "created_at": "ISO-8601 timestamp",
  "metadata": { "app_version": "string", "parent_id": "string" },
  "ingested_at": "ISO-8601 timestamp"
}
```

### Design Considerations
- **Rate limiting & retries** with exponential backoff per source.
- **Incremental ingestion** using high-water marks (last seen timestamp/ID) to avoid re-fetching.
- **Idempotency**: dedupe on `(source, id)`.
- **Config-driven sources** so new URLs/videos can be added without code changes.

**Output:** `raw_reviews` table / `raw/*.parquet`

---

## Phase 2 — Data Processing & Cleaning

**Goal:** Convert noisy raw text into clean, analysis-ready records.

### Steps
1. **Deduplication** — remove exact and near-duplicate texts (hashing + fuzzy matching).
2. **Language detection** — tag language; optionally translate non-English to English.
3. **Text cleaning** — strip HTML, emojis (retain sentiment signal), URLs, markup; normalize whitespace.
4. **Spam/noise filtering** — drop empty, bot, or promotional content.
5. **Tokenization & normalization** — lowercasing, lemmatization for keyword analysis.
6. **PII handling** — redact emails/usernames where appropriate.

**Output:** `clean_reviews` table with added fields: `language`, `clean_text`, `token_count`, `is_spam`.

---

## Phase 3 — Storage Layer

**Goal:** Persist data at every stage and enable fast retrieval for AI and analytics.

### Stores
- **Relational DB (PostgreSQL/SQLite):** structured raw + clean + enriched records.
- **Object store / Parquet:** cheap, columnar archive of raw payloads.
- **Vector database (Chroma/FAISS/pgvector):** embeddings of `clean_text` for semantic search, clustering, and RAG.

### Core Tables
- `raw_reviews` — immutable source-of-truth.
- `clean_reviews` — processed records.
- `enriched_reviews` — AI/NLP outputs (sentiment, themes, segment).
- `insights` — aggregated, dashboard-ready metrics.

---

## Phase 4 — AI / NLP Processing

**Goal:** Apply LLM/NLP techniques to extract meaning from each review.

### LLM Provider
**Groq — Llama 3.3 70B Versatile** (free tier)
- API: `api.groq.com`, Python library: `groq`
- Free limits: 30 RPM / 14,400 RPD / 131,072 TPM
- Structured JSON output via `response_format: {"type": "json_object"}`
- Response cache keyed by `(prompt_version, text_hash)` in `data/enriched/llm_cache.json`

### Per-Review Enrichment
| Task | Technique | Output |
|------|-----------|--------|
| Sentiment analysis | Groq Llama 3.3 70B (JSON mode) | `positive / neutral / negative` + score 0–1 |
| Theme/topic extraction | Groq Llama 3.3 70B (JSON mode) | list of canonical themes |
| Feature request detection | Groq Llama 3.3 70B (JSON mode) | boolean + extracted request text |
| Pain point extraction | Groq Llama 3.3 70B (JSON mode) | structured pain point sentence |
| User segment inference | Groq Llama 3.3 70B + heuristics | `casual / power_user / new_user / churn_risk` |
| Intent / emotion | Groq Llama 3.3 70B (JSON mode) | frustration, delight, confusion, etc. |

### Aggregate AI Tasks
- **Theme clustering** across the full corpus via HDBSCAN on ChromaDB embeddings.
- **Cluster labeling** — Groq Llama 3.3 70B names each HDBSCAN cluster.
- **Summarization** — Groq Llama 3.3 70B summaries per theme and per source.
- **Pain-point ranking** by frequency × severity × sentiment.

### Design Considerations
- **Mini-batching** (5 reviews per LLM call) to maximise throughput within 30 RPM limit.
- **Response caching** — re-runs skip already-processed reviews; cache persisted as JSON.
- **Structured outputs** (JSON mode) for reliability; parsed and validated before DB insert.
- **Prompt versioning** (`PROMPT_VERSION = "v1.0"`) for reproducibility.
- **Embeddings reused** from Phase 3 ChromaDB store — no re-embedding needed.

**Output:** `enriched_reviews` table.

---

## Phase 5 — Insights & Aggregation

**Goal:** Turn enriched records into the answers the dashboard must surface.

### Computed Insights
- Sentiment distribution overall, by source, and over time.
- Top themes and their trend lines.
- Most frequent feature requests (ranked).
- Recurring pain points (ranked by impact).
- User-segment breakdowns and segment-specific challenges.
- Cross-source agreement on unmet needs.
- AI-generated **product opportunity recommendations** mapped to evidence.

Each insight maps directly to a Dashboard Objective question in the problem statement.

**Output:** `insights` table / cached JSON for the dashboard.

---

## Phase 6 — Interactive Dashboard

**Goal:** Present a clean, insight-driven experience for Spotify's Growth Product team.

### Components
- **Overview**: KPIs (total feedback, sentiment split, source mix).
- **Themes Explorer**: interactive theme clusters with drill-down to source quotes.
- **Sentiment Trends**: time-series and source comparisons.
- **Pain Points & Feature Requests**: ranked, filterable tables.
- **User Segmentation**: behavior and challenge breakdown per segment.
- **AI Summaries**: narrative insights per theme/source.
- **Product Recommendations**: prioritized opportunities with supporting evidence.

### Stack
- **Frontend:** Next.js (App Router, TypeScript)
- **Charts:** Recharts / Chart.js
- **API layer:** FastAPI (Python) — serves aggregated insights from the `insights` table as JSON endpoints
- **Styling:** Tailwind CSS

### Cross-Cutting
- Filters by source, date, segment, sentiment, theme.
- Export to PDF/CSV for stakeholder sharing.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Orchestration | Prefect/Airflow or a simple CLI pipeline (`ingest → clean → enrich → aggregate`) |
| Configuration | `.env` + YAML source registry |
| Secrets | Environment variables / secret manager for API keys |
| Logging & monitoring | Structured logs per phase, run metrics |
| Cost control | LLM call caching, batching, model tiering |
| Reproducibility | Versioned prompts, deterministic seeds, data snapshots |
| Testing | Unit tests for collectors/cleaners, golden-set tests for AI outputs |

---

## Suggested Repository Structure

```
Spotify Review Analysis/
├── Docs/
│   ├── Problemstatment.md
│   └── Architecture.md
├── config/
│   └── sources.yaml
├── src/
│   ├── ingestion/        # Phase 1 collectors
│   ├── processing/       # Phase 2 cleaning
│   ├── storage/          # Phase 3 DB/vector access
│   ├── ai/               # Phase 4 LLM/NLP
│   ├── insights/         # Phase 5 aggregation
│   └── pipeline.py       # orchestration entrypoint
├── dashboard/            # Phase 6 UI
├── data/
│   ├── raw/
│   ├── clean/
│   └── enriched/
├── tests/
├── requirements.txt
└── README.md
```

---

## Phase 7 — Backend Deployment (Render)

**Goal:** Host the FastAPI backend and the full Python pipeline on [Render](https://render.com) so the dashboard can be accessed publicly without running a local server.

### Services

| Render Service | Type | Purpose |
|---|---|---|
| `spotify-api` | **Web Service** | FastAPI app (`dashboard/api/main.py`) served via Uvicorn |
| `spotify-pipeline` | **Cron Job** (optional) | Re-run `ingest → clean → enrich → aggregate` on a schedule |

### Deployment Steps

1. **Dockerfile** (or `render.yaml` native Python) — specify Python 3.11 runtime.
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:** `uvicorn dashboard.api.main:app --host 0.0.0.0 --port $PORT`
4. **Environment variables** on Render dashboard:
   - `GROQ_API_KEY`
   - `YOUTUBE_API_KEY`
   - `DB_URL` — point to a persistent disk or managed PostgreSQL (upgrade from SQLite for production)
5. **Persistent disk** — mount at `/data` so `reviews.db`, `chroma/`, and Parquet files survive deploys.
6. **CORS** — update `allow_origins` in `main.py` to include the Vercel production URL.

### Design Considerations
- Use **Render's managed PostgreSQL** (free tier) to replace SQLite for concurrent access.
- Keep ChromaDB on the persistent disk (or migrate to a hosted vector DB like Pinecone for scale).
- Set `DB_URL=postgresql://...` via environment variable — SQLAlchemy handles the switch transparently.

**Output:** `https://spotify-api.onrender.com` — public FastAPI instance.

---

## Phase 8 — Frontend Deployment (Vercel)

**Goal:** Deploy the Next.js dashboard to [Vercel](https://vercel.com) for a public, CDN-hosted URL with zero-config CI/CD on every `git push`.

### Deployment Steps

1. **Push** `dashboard/web/` code to GitHub (or the full monorepo).
2. **Import** the repository into Vercel — set **Root Directory** to `dashboard/web`.
3. **Environment variables** on Vercel dashboard:
   - `NEXT_PUBLIC_API_URL=https://spotify-api.onrender.com`
4. **Framework preset:** Next.js (auto-detected).
5. Vercel auto-deploys on every push to `main`; preview deployments on PRs.

### `next.config.ts` update for production

```ts
// Replace localhost rewrite with env-driven API URL
async rewrites() {
  return [
    {
      source: "/api/:path*",
      destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
    },
  ];
},
```

### Design Considerations
- **Edge caching** — Vercel caches `fetch()` responses; `revalidate: 30` is already set on all pages.
- **Preview URLs** — each PR gets its own Vercel preview linked to the same Render backend.
- **Custom domain** — add via Vercel dashboard if needed.

**Output:** `https://spotify-review-analysis.vercel.app` — public Next.js dashboard.

---

## Execution Flow Summary

1. **Ingest** raw feedback from Google Play, YouTube, Spotify Community, and Hacker News.
2. **Clean & normalize** into analysis-ready records.
3. **Store** raw, clean, and enriched data plus embeddings.
4. **Enrich** each review with sentiment, themes, segments, and requests via LLM/NLP.
5. **Aggregate** into ranked insights answering the dashboard questions.
6. **Visualize** in an interactive Next.js dashboard for data-driven product decisions.
7. **Deploy backend** to Render (FastAPI + persistent disk + optional PostgreSQL).
8. **Deploy frontend** to Vercel (Next.js, CDN-hosted, CI/CD on every push).
