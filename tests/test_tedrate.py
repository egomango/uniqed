"""TEDRATE stands in for LIBOR (decision 2026-09-06, see CLAUDE.md).

The paper routed the differenced LIBOR series to the differential-entropy method
because the intrinsic-dimension estimate never left the diagonal (SI Figs. S11-S12).
The same must happen on the differenced TEDRATE series. Fetched at test time, never
vendored; skipped when offline.
"""

import io
import urllib.error
import urllib.request

import numpy as np
import pandas as pd
import pytest

from uniqed.embedding import choose_embedding

TEDRATE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=TEDRATE"
EXPECTED_ROWS = 9407  # daily rows 1986-01-02 to 2022-01-21
EXPECTED_NUMERIC = 8853  # 554 rows are empty (market holidays and the like)


def _fetch_tedrate():
    try:
        with urllib.request.urlopen(TEDRATE_URL, timeout=30) as response:
            text = response.read().decode()
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        pytest.skip(f"TEDRATE not reachable: {err}")
    df = pd.read_csv(io.StringIO(text), na_values=".")
    assert len(df) == EXPECTED_ROWS
    return df["TEDRATE"].dropna().to_numpy()


def test_differenced_tedrate_routes_to_entropy_ratio():
    x = _fetch_tedrate()
    assert len(x) == EXPECTED_NUMERIC
    # Differenced over the observed sequence; a gap counts as one step, as the
    # paper's monthly LIBOR differencing did.
    choice = choose_embedding(np.diff(x))
    assert choice.method == "entropy-ratio", choice
    assert 2 <= choice.dimension <= 8
