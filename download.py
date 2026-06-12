"""
Fetches and caches the Bitcoin OTC trust dataset from SNAP.
The raw file is kept in data/ and is excluded from git.
"""

import gzip
import urllib.request
from pathlib import Path

from config import DATA_DIR, DATASET_URL

RAW_PATH = Path(DATA_DIR) / "soc-sign-bitcoinotc.csv"
GZ_PATH = Path(DATA_DIR) / "soc-sign-bitcoinotc.csv.gz"


def fetch() -> Path:
    """Return path to the local CSV, downloading it if necessary."""
    Path(DATA_DIR).mkdir(exist_ok=True)

    if RAW_PATH.exists():
        print(f"[download] Using cached dataset at {RAW_PATH}")
        return RAW_PATH

    print(f"[download] Fetching {DATASET_URL} ...")
    urllib.request.urlretrieve(DATASET_URL, GZ_PATH)

    print(f"[download] Decompressing ...")
    with gzip.open(GZ_PATH, "rb") as f_in, open(RAW_PATH, "wb") as f_out:
        f_out.write(f_in.read())

    GZ_PATH.unlink()
    print(f"[download] Saved to {RAW_PATH}")
    return RAW_PATH
