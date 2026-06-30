# Spotify Review Discovery Engine

An AI-powered pipeline that collects, analyzes, and visualizes user feedback from multiple public sources to surface insights about Spotify's music discovery and recommendation quality.

## Project Structure

```
Spotify Review Analysis/
├── Docs/                    # Architecture, implementation plan, problem statement
├── config/
│   └── sources.yaml         # Config-driven source definitions
├── src/
│   ├── ingestion/           # Phase 1 — data collectors
│   ├── processing/          # Phase 2 — cleaning & normalization
│   ├── storage/             # Phase 3 — DB & vector store
│   ├── ai/                  # Phase 4 — LLM/NLP enrichment
│   ├── insights/            # Phase 5 — aggregation
│   └── pipeline.py          # CLI orchestration
├── dashboard/               # Phase 6 — Streamlit UI
├── data/                    # Runtime data (gitignored)
├── tests/
├── requirements.txt
└── .env.example
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
playwright install chromium
cp .env.example .env            # fill in API keys
```

## Running the Pipeline

```bash
# Run individual phases
python -m src.pipeline ingest
python -m src.pipeline clean
python -m src.pipeline enrich
python -m src.pipeline aggregate

# Run all phases end-to-end
python -m src.pipeline all
```

## Dashboard

```bash
streamlit run dashboard/app.py
```

## Data Sources

| Source | Method |
|--------|--------|
| Google Play Store Reviews | `google-play-scraper` |
| YouTube Comments | YouTube Data API v3 |
| Spotify Community Discussions | Playwright + BeautifulSoup |
| Hacker News Discussions | HN Algolia API |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key (for LLM enrichment) |
| `ANTHROPIC_API_KEY` | Anthropic API key (alternative LLM) |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key |
| `LLM_PROVIDER` | `openai` or `anthropic` |
| `DB_URL` | SQLAlchemy DB URL (default: `sqlite:///data/reviews.db`) |
