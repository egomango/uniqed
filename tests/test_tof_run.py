from unittest import TestCase
from pandas import DataFrame
import numpy as np
from uniqed.runners.tof_run import detect_outlier


class Test(TestCase):
    def test_detect_outlier(self):
        x = DataFrame(np.random.rand(10000))
        df1 = detect_outlier(x, cutoff_n=1000)
        df2 = detect_outlier(x, cutoff_n=1, in_percent=True)




import numpy as np
import pandas as pd

from tests.systems import lorenz
from uniqed.runners.tof_run import detect_outlier


def test_explicit_embedding_is_unchanged_and_attrs_say_given():
    rng = np.random.RandomState(0)
    df = pd.DataFrame({"value": rng.rand(500)})
    res = detect_outlier(df, cutoff_n=50, embedding_dimension=3, embedding_delay=1)
    assert res.attrs["embedding"]["dimension"] == 3
    assert res.attrs["embedding"]["delay"] == 1
    assert res.attrs["embedding"]["method"] == "given"
    assert res["TOF_score"].isna().sum() == 2  # first and last raw rows, as in 0.0.3


def test_auto_embedding_on_lorenz_picks_three():
    df = pd.DataFrame({"value": lorenz(8000)})
    res = detect_outlier(df, cutoff_n=200)
    emb = res.attrs["embedding"]
    assert emb["dimension"] == 3
    assert emb["method"] == "saturation"
    assert emb["window"] == 2 * emb["delay"]
    assert len(res) == len(df)


def test_only_delay_given_chooses_dimension():
    df = pd.DataFrame({"value": lorenz(8000)})
    res = detect_outlier(df, cutoff_n=200, embedding_delay=8)
    assert res.attrs["embedding"]["delay"] == 8
    assert res.attrs["embedding"]["delay_rule"] == "given"
    assert res.attrs["embedding"]["dimension"] == 3
