from dataclasses import asdict

import pandas as pd

from uniqed.embedding import EmbeddingChoice, choose_embedding
from uniqed.models.tof import TOF
from uniqed.transformers.transformers import (
    TimeDelayEmbedder,
    TransformYTrue,
    _make_result_df,
)


def detect_outlier(
    time_series,
    cutoff_n=1.0,
    k=None,
    in_percent=False,
    embedding_dimension=None,
    embedding_delay=None,
    **other_method_kwargs
):
    """Detects outliers with TOF

    :param pandas.DataFrame time_series: pandas dataframe with the time series
    :param float cutoff_n: the threshold for the detector
                            (max event length, or % of #datapoints)
    :param int k: numbert of neighbors to use (default is embedding)dimension+1)
    :param bool in_percent: if True then the threshold is draw at the given percentage not in event length
    :param int embedding_dimension: embedding dimension (>=1), or None to choose it from the data [default: None]
    :param int embedding_delay: embedding delay (>=1), or None to choose it from the data [default: None]
    :return: result DataFrame; ``result.attrs["embedding"]`` records the embedding used and how it was chosen
    :rtype: pandas.DataFrame
    """

    # Conversion to numpy array
    np_time_series = time_series.values[:, 0]

    if embedding_dimension is None or embedding_delay is None:
        choice = choose_embedding(
            np_time_series, dimension=embedding_dimension, delay=embedding_delay
        )
    else:
        choice = EmbeddingChoice(
            embedding_dimension,
            embedding_delay,
            "given",
            "given",
            (),
            (embedding_dimension - 1) * embedding_delay,
        )
    embedding_dimension, embedding_delay = choice.dimension, choice.delay

    # Time series embedding, and new time axis
    embededd_time_series = TimeDelayEmbedder(
        d=embedding_dimension, tau=embedding_delay
    ).fit_transform(np_time_series)
    new_time_axis = TransformYTrue(
        d=embedding_dimension, tau=embedding_delay
    ).fit_transform(time_series.index)
    new_time_axis = pd.DataFrame(new_time_axis).values

    # initialize method object
    mytof = TOF(cutoff_n=cutoff_n, k=k, **other_method_kwargs)
    mytof = mytof.fit(embededd_time_series)
    if in_percent:
        mytof.cutoff_ = mytof._compute_perc_cutoff(cutoff_n)
    y_pred = mytof.predict(embededd_time_series)

    # locally scoring outlierness for each time series points
    outlier_score = mytof.outlier_score_

    res_df = _make_result_df(
        new_time_axis, outlier_score, y_pred, inv_it=True, prefix="TOF"
    )
    result = pd.concat([time_series, res_df], axis=1, sort=False)
    result.attrs["embedding"] = asdict(choice)
    return result
