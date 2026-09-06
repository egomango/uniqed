.. image:: https://img.shields.io/pypi/v/uniqed.svg
  :target: https://pypi.org/project/uniqed/
  :alt: PyPI version

.. image:: https://github.com/egomango/uniqed/actions/workflows/test.yml/badge.svg
  :target: https://github.com/egomango/uniqed/actions/workflows/test.yml
  :alt: Tests

.. image:: https://img.shields.io/badge/license-BSD--2--Clause-blue.svg
  :target: https://github.com/egomango/uniqed/blob/master/LICENSE.txt
  :alt: License


uniqed
======

Finds the moments when a system is in a state it has never been in before.

Most monitoring flags values that are too high or too low. It cannot flag a pattern
that stays inside the normal range but has never happened before: a slow drift, a new
rhythm, a state the system has never visited. ``uniqed`` scores every moment of a time
series by asking when else the system was in this state. A normal state has visits
spread across the whole history; a first-time state has visits from one short window.
It needs no training period, no model of what normal looks like and no labels, only
the history. The method is the Temporal Outlier Factor of Benkő, Bábel and Somogyvári
(*Scientific Reports* 12:227, 2022) [1]_.

Who it is for
-------------

Slow-sampled signals with a long history: one reading per minute or slower, months
of it. Historian tags, SCADA telemetry, meter intervals, substation and network data,
long physiological recordings reviewed offline, slow economic series. Runtime is
about four hours per million points on a laptop, so faster data is downsampled to the
rate its slowest rhythm needs.

It is not an outlier detector and it is not for spikes. A reading far from the rest is
an outlier; a first-time state can sit entirely inside the normal range, and a fault
that recurs every month is not first-time. Run it beside your existing tools.

Install
-------

.. code-block:: bash

    pip install uniqed

Example
-------

.. code-block:: python

    from uniqed.data.gen_logmap import generate_logmapdata
    from uniqed.runners.tof_run import detect_outlier

    data_df = generate_logmapdata(rseed=359)          # a logistic map with one inserted segment
    res_df = detect_outlier(data_df[["value"]], cutoff_n=80)   # cutoff_n: longest event, in samples

    print(res_df.query("TOF == 1").index.min(), res_df.query("TOF == 1").index.max())
    print(res_df.attrs["embedding"])                  # the embedding it chose, and by which rule

``res_df`` is the input with two columns added: ``TOF_score`` (lower is more unusual)
and ``TOF`` (1 where the score passes the threshold set by ``cutoff_n``). The plotting
script behind the picture is ``examples/example_tof_run.py``.

.. image:: https://raw.githubusercontent.com/egomango/uniqed/master/examples/example_run.png

Since 0.1.0 the time-delay embedding is chosen from the data when you do not give it,
by the procedure the paper's supplement describes: the delay from the first zero
crossing of the autocorrelation, the dimension from where the intrinsic-dimension
estimate stops tracking the embedding dimension (never below 3), and Gautama's
entropy-ratio criterion for signals with no such plateau. You can still set either
value yourself, and explicit values give the same output as earlier releases:

.. code-block:: python

    from uniqed.embedding import choose_embedding

    choice = choose_embedding(data_df["value"].values)
    print(choice)   # dimension, delay, method, delay_rule, dimension_profile, window, ...

    res_df = detect_outlier(data_df[["value"]], cutoff_n=80,
                            embedding_dimension=3, embedding_delay=1)

Limits
------

- **Needs history.** Tens of cycles of the slowest rhythm in the signal. The chooser
  needs about 500 samples beyond the embedding window and more than one cycle; on
  shorter series, on series with too few cycles, and on series whose values repeat
  exactly, it raises and tells you to pass the embedding explicitly.
- **Blind to short events.** Anything shorter than a few samples is invisible. Pair it
  with a spike detector.
- **Marks part of an event, not every point of it.** Measure events caught, not points.
- **Lag.** The score at a moment needs several samples after it, half the embedding
  window plus the neighbour count. A live detector cannot score a moment until they
  arrive.
- **Runtime** grows faster than linearly with length: about four hours per million
  points.
- **A first-time state is not a fault.** It can be a transition, an operator's change, a
  new season, a recalibrated sensor. The score cannot tell these apart; a reviewer can.

Evidence
--------

The paper reports results on four simulated test sets, one sleep-apnea ECG recording,
the GW150914 gravitational-wave strain and the differenced USD LIBOR series. Nothing on
process-plant data, on multi-channel input or in a live setting yet. This repository
tests every release against Table 1 of the paper, on the authors' published simulation
files and on datasets regenerated from the supplement, and ``docs/log.md`` records one
paragraph per finished story: what was tried, the number, what failed.

Citation
--------

.. [1] Benkő, Z., Bábel, T., & Somogyvári, Z. (2022). How to find a unicorn: a novel
   model-free, unsupervised anomaly detection method for time series. *Scientific
   Reports* 12, 227. https://doi.org/10.1038/s41598-021-03526-y (arXiv:2004.11468)

BSD 2-Clause licence, copyright the authors. Maintained at
https://github.com/egomango/uniqed; issues and pull requests there.
