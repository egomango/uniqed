"""Regression test on the authors' published simulation files.

The CSVs under examples/data/simulations are the 100 realisations per dataset
that Table 1 of Benkő, Bábel, Somogyvári, Sci. Rep. 12:227 (2022) was computed
on. They are stored in git LFS. Run through this package with E=3, tau=1 and
the Table 1 neighbour counts they reproduce Table 1 to three decimals, so the
tolerance here is tight (0.005). The simulated-ECG files are the paper's own
10x-downsampled output (SI, "Simulated ECG datasets"); run as they are with
E=3, tau=1, k=2 they give 0.931, so the row is tested here and the Ryzhii
generator is not needed (decision 2026-09-06).

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
from uniqed.runners.tof_run import detect_outlier

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
    "sim_ecg": ("sim-ECG-tachy", 0.931, None),
}

ECG_F1_FILES = 15  # Fig. S5 used N = 15
ECG_F1_THRESHOLD = 1100  # SI, "Embedding-parameter dependence"
ECG_F1_K = 4  # SI, F1 screening used k = 4 for TOF
ECG_F1_REQUIRED = 0.82  # the paper's hand-set E=3, tau=1 (Fig. S5 C); the chooser measured 0.86


def _read_published(path):
    """The sim_ecg files carry a leading time column; the others do not."""
    data_df = pd.read_csv(path)
    return data_df[["value", "is_anomaly"]]


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
        data_df = _read_published(SIMULATIONS_DIR / folder / f"{i}.csv")
        if preprocess is not None:
            data_df = preprocess(data_df)
        aucs.append(tof_roc_auc(data_df, k))
    mean_auc = float(np.mean(aucs))
    assert abs(mean_auc - expected_auc) <= TOLERANCE, (
        f"{name}: mean ROC AUC over {N_FILES} published files is {mean_auc:.3f}, "
        f"expected {expected_auc:.3f} (tolerance {TOLERANCE}, "
        f"E={EMBEDDING_DIMENSION}, tau={EMBEDDING_DELAY}, k={k})"
    )


@pytest.mark.slow
def test_chosen_embedding_beats_hand_set_on_simulated_ecg():
    """Story A1 definition of done (revised 2026-09-06): the chooser's own (E, tau) beats the
    paper's hand-set E=3, tau=1 (F1 0.82) on the simulated ECG. The Fig. S5 optimum (7, 6),
    0.94, came from a labelled grid search and no label-free rule reaches it; the chooser
    measured 0.86 with the dimension floor of 3, 0.78 without."""
    from sklearn.metrics import f1_score

    _ensure_lfs_payload()
    f1s, choices = [], []
    for i in range(ECG_F1_FILES):
        data_df = _read_published(SIMULATIONS_DIR / "sim_ecg" / f"{i}.csv")
        res_df = detect_outlier(data_df[["value"]], cutoff_n=ECG_F1_THRESHOLD, k=ECG_F1_K)
        scored = res_df["TOF_score"].notna().values
        f1s.append(
            f1_score(
                data_df["is_anomaly"].values[scored],
                res_df["TOF"].values[scored].astype(int),
            )
        )
        emb = res_df.attrs["embedding"]
        choices.append((emb["dimension"], emb["delay"], emb["method"], round(f1s[-1], 3)))
    mean_f1 = float(np.mean(f1s))
    assert mean_f1 >= ECG_F1_REQUIRED, (
        f"mean F1 {mean_f1:.3f} over {ECG_F1_FILES} files; per file (E, tau, method, F1): {choices}"
    )
