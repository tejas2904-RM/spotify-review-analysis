"""Export all computed insights from the local SQLite DB to a snapshot JSON file.

Run this LOCALLY after the full pipeline has finished (enrich → cluster → summarize → aggregate):

    python scripts/export_insights.py

The output file (data/insights_snapshot.json) should be committed to the repo.
Render reads it on first boot to populate a fresh DB without re-running the pipeline.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.storage.repository import get_all_insights   # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Always write to the repo's data/ folder so the file can be committed.
_REPO_ROOT = Path(__file__).parent.parent
OUTPUT_PATH = Path(os.getenv("INSIGHTS_SNAPSHOT", str(_REPO_ROOT / "data" / "insights_snapshot.json")))


def export_snapshot(output: Path = OUTPUT_PATH) -> None:
    insights = get_all_insights()
    if not insights:
        logger.warning("No insights found in the database — run the pipeline first.")
        sys.exit(1)

    records = [
        {
            "metric": row.metric,
            "filters_json": row.filters_json,
            "value_json": row.value_json,
            "computed_at": row.computed_at.isoformat() if row.computed_at else None,
        }
        for row in insights
    ]

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, indent=2), encoding="utf-8")
    logger.info("Exported %d insight records → %s", len(records), output)


if __name__ == "__main__":
    export_snapshot()
