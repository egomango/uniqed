
.. image:: https://readthedocs.org/projects/uniqed/badge/?version=latest
  :target: https://uniqed.readthedocs.io/en/latest/?badge=latest
  :alt: Documentation Status

.. image:: https://travis-ci.com/phrenico/uniqed.svg?branch=master
  :target: https://travis-ci.com/phrenico/uniqed

.. image:: https://coveralls.io/repos/github/phrenico/uniqed/badge.svg?branch=master
  :target: https://coveralls.io/github/phrenico/uniqed?branch=master



The uniqed package
==================

Simple python implementation of the Temporal Outlier Factor [1]_ (TOF) anomaly detection method.


Installation instructions
-------------------------

Install it directly from PyPI:

.. code-block:: bash

    pip install uniqed


Simple example
--------------
This is a simple example:

.. code-block:: python

    from uniqed.data.gen_logmap import generate_logmapdata
    from uniqed.runners.tof_run import detect_outlier
    import matplotlib.pyplot as plt
    
    # Generate some data
    data_df = generate_logmapdata(rseed=359)
    
    # Detect outliers. The embedding (dimension and delay) is chosen from the data;
    # res_df.attrs["embedding"] says what was chosen and by which rule.
    res_df = detect_outlier(data_df[['value']], cutoff_n=80)
    print(res_df.attrs["embedding"]["dimension"], res_df.attrs["embedding"]["delay"])
    
    
    # plot the results
    fig, axs = plt.subplots(2, 1, sharex=True)
    fig.suptitle('TOF anomaly detection demo')
    
    axs[0].plot(res_df['value'], color='tab:blue', label='time series')
    axs[0].plot(res_df['value'].loc[data_df.query("is_anomaly==1").index.values],
             color='tab:green', label='anomaly')
    axs[0].plot(res_df.query("TOF==1")['value'], lw=0, marker='o',
             color='tab:orange', label='TOF detections')
    axs[0].set_ylabel('values')
    axs[0].legend(loc='upper left', framealpha=1)
    
    
    axs[1].plot(res_df['TOF_score'], color='k', label='TOF score')
    axs[1].plot(res_df['TOF_score'].loc[data_df.query("is_anomaly==1").index.values],
             color='tab:green', label='anomaly')
    axs[1].plot(res_df.query("TOF==1")['TOF_score'], lw=0, marker='o',
             color='tab:orange', label='TOF')
    axs[1].set_ylabel('TOF score')
    axs[1].set_xlabel('t')
    axs[1].legend(['TOF score', 'anomaly', 'TOF detections'],
                  loc='upper left',
                  framealpha=1)
    
    axs[1].set_xlim(0, 2000)
    axs[0].grid(True)
    axs[1].grid(True)
    
    fig.tight_layout(rect=[0, 0, 1, 1], pad=1, h_pad=0, w_pad=0)
    fig.savefig("example_run.png")
    plt.show()


.. image:: https://raw.githubusercontent.com/phrenico/uniqed/master/examples/example_run.png

Choosing the embedding
----------------------
Since 0.1.0 the embedding is chosen from the data when you do not give it: the delay
from the first zero crossing of the autocorrelation, the dimension from where the
intrinsic-dimension estimate stops tracking the embedding dimension (never below 3),
and, for signals with no such plateau, Gautama's entropy-ratio criterion. This is the
procedure the paper's supplement describes for its real datasets. You can still set
either value yourself; explicit values give the same output as earlier releases:

.. code-block:: python

    from uniqed.embedding import choose_embedding

    choice = choose_embedding(data_df['value'].values)
    print(choice)   # dimension, delay, method, delay_rule, dimension_profile, window, ...

    res_df = detect_outlier(data_df[['value']], cutoff_n=80,
                            embedding_dimension=3, embedding_delay=1)

The chooser needs about 500 samples beyond the embedding window and a series that holds
more than one cycle of its slowest rhythm. On shorter series, on series with too few
cycles, and on series whose values repeat exactly (an exactly periodic sampled signal),
``choose_embedding`` raises and tells you to pass the embedding explicitly.


References
----------

.. [1] Benkő, Z., Bábel, T., & Somogyvári, Z. (2020). How to find a unicorn: a novel model-free, unsupervised anomaly detection method for time series. http://arxiv.org/abs/2004.11468
