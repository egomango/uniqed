"""Regression test on the authors' published simulation files.

The CSVs under examples/data/simulations are the 100 realisations per dataset
that Table 1 of Benkő, Bábel, Somogyvári, Sci. Rep. 12:227 (2022) was computed
on. They are stored in git LFS. Run through this package with E=3, tau=1 and
the Table 1 neighbour counts they reproduce Table 1 to three decimals, so the
tolerance here is tight (0.005). The simulated-ECG files exist but are not
tested: their reference value depends on preprocessing the paper does not
specify.

Marked ``slow``: it needs the LFS payload (about 50 MB with the ECG files)
and is deselected by default. If the files are still LFS pointers the test
tries ``git lfs pull`` and skips when git-lfs is unavailable or the pull fails.
"""

import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tests.test_regression_paper import (
    EMBEDDING_DELAY,
    EMBEDDING_DIMENSION,
    TABLE_1,
    log_difference,
    tof_roc_auc,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SIMULATIONS_DIR = REPO_ROOT / "examples" / "data" / "simulations"
N_FILES = 100
TOLERANCE = 0.005
LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"

# Table 1 rows reproduced by the published files: folder -> (name, mean AUC
# measured on the files, preprocessing)
PUBLISHED = {
    "logmap_tent": ("logmap-tent", 0.939, None),
    "logmap_linear": ("logmap-linear", 0.994, None),
    "rw_linear": ("randwalk-linear", 0.987, log_difference),
}


def _is_lfs_pointer(path):
    with open(path, "rb") as f:
        return f.read(len(LFS_POINTER_PREFIX)) == LFS_POINTER_PREFIX


def _ensure_lfs_payload():
    sample = SIMULATIONS_DIR / "logmap_tent" / "0.csv"
    if not sample.exists():
        pytest.skip(f"{sample} is missing")
    if not _is_lfs_pointer(sample):
        return
    try:
        subprocess.run(
            ["git", "lfs", "pull", "--include", "examples/data/simulations/**"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as err:
        pytest.skip(f"git lfs pull failed, files are still LFS pointers: {err}")
    if _is_lfs_pointer(sample):
        pytest.skip("git lfs pull did not replace the LFS pointers")


@pytest.mark.slow
@pytest.mark.parametrize("folder", list(PUBLISHED))
def test_published_files_reproduce_table_1(folder):
    _ensure_lfs_payload()
    name, expected_auc, preprocess = PUBLISHED[folder]
    k, _ = TABLE_1[name]
    aucs = []
    for i in range(N_FILES):
        data_df = pd.read_csv(SIMULATIONS_DIR / folder / f"{i}.csv")
        if preprocess is not None:
            data_df = preprocess(data_df)
        aucs.append(tof_roc_auc(data_df, k))
    mean_auc = float(np.mean(aucs))
    assert abs(mean_auc - expected_auc) <= TOLERANCE, (
        f"{name}: mean ROC AUC over {N_FILES} published files is {mean_auc:.3f}, "
        f"expected {expected_auc:.3f} (tolerance {TOLERANCE}, "
        f"E={EMBEDDING_DIMENSION}, tau={EMBEDDING_DELAY}, k={k})"
    )
