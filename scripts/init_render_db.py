"""Initialize the Render persistent-disk DB from the committed snapshot JSON.

Called automatically by the FastAPI lifespan when the insights table is empty.
Can also be run manually:

    python scripts/init_render_db.py

The snapshot is read from DATA_DIR/insights_snapshot.json (default: data/).
On Render, DATA_DIR=/data (persistent disk mount).
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Snapshot is always committed in the repo's `data/` folder (not the persistent disk).
# We locate it relative to this script file (project_root/data/insights_snapshot.json).
_REPO_ROOT = Path(__file__).parent.parent
SNAPSHOT_PATH = Path(os.getenv("INSIGHTS_SNAPSHOT", str(_REPO_ROOT / "data" / "insights_snapshot.json")))


def import_snapshot(snapshot: Path = SNAPSHOT_PATH) -> int:
    """Read snapshot JSON and upsert all insight rows.

    Returns the number of rows imported.
    Raises FileNotFoundError if the snapshot doesn't exist.
    """
    if not snapshot.exists():
        raise FileNotFoundError(
            f"Snapshot not found at {snapshot}. "
            "Run `python scripts/export_insights.py` locally and commit the file."
        )

    records = json.loads(snapshot.read_text(encoding="utf-8"))
    if not records:
        logger.warning("Snapshot is empty — nothing to import.")
        return 0

    from src.storage.db import get_engine
    from src.storage.models import Base
    from src.storage.repository import save_insight

    # Ensure tables exist
    engine = get_engine()
    Base.metadata.create_all(engine)

    imported = 0
    for rec in records:
        value = json.loads(rec["value_json"])
        filters = json.loads(rec["filters_json"]) if rec.get("filters_json") else None
        save_insight(rec["metric"], value, filters or None)
        imported += 1

    logger.info("Imported %d insight records from %s", imported, snapshot)
    return imported


if __name__ == "__main__":
    n = import_snapshot()
    if n:
        sys.exit(0)
    else:
        sys.exit(1)
