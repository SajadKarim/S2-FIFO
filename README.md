# S2-FIFO\<M>
Artifacts for S2-FIFO\<M>

## Plots

The folder `Plots/` contains the scripts that draw the figures of the paper and the results they read:

| File | Content |
|---|---|
| `RQ1and2Plots.py` | Plotting script for the miss-ratio figures of RQ1 and RQ2 |
| `sim_results_cmd.csv` | libCacheSim results for the S3-FIFO trace collections |
| `sim_results_others.csv` | libCacheSim results for the SNIA, SPC, Tectonic, and Meta Storage traces and the synthetic Zipf traces |
| `RQ3Plot.py` | Plotting script for the throughput figure of RQ3 |
| `cachelib_results.csv` | CacheLib benchmark results for the synthetic Zipf traces |

### Requirements

Python 3 with `numpy` and `matplotlib`:

```bash
pip install numpy matplotlib
```

## Simulation code and benchmark (libCacheSim)

The miss-ratio results in `Plots/sim_results_*.csv` were produced with libCacheSim, extended with the
S2-FIFO+ variants. The code is in the branch `btw27` of
[github.com/SajadKarim/libCacheSim](https://github.com/SajadKarim/libCacheSim):

- `libCacheSim/cache/eviction/S2FIFOPlus*.c`: the S2-FIFO+ variants as libCacheSim eviction policies
- `benchmark/`: the scripts that obtain the traces and run the simulations

The traces are not part of either repository. `benchmark/README.md` in that branch describes how to build
`cachesim`, the requirements, how to obtain the traces and run the simulations, and how to copy the results into
`Plots/` to draw the RQ1 and RQ2 figures.

## Throughput code and benchmark (CacheLib)

The throughput results in `Plots/cachelib_results.csv` were produced with CacheLib, extended with the
S2-FIFO+ variants. The code is in the branch `btw27` of
[github.com/SajadKarim/CacheLib](https://github.com/SajadKarim/CacheLib):

- `cachelib/allocator/`: the S2-FIFO+ variants as CacheLib eviction policies
- `benchmark/`: the multi-threaded benchmark and the scripts that build it and run the sweep

The Zipf traces are not part of either repository; the benchmark generates them. `benchmark/README.md` in that
branch describes the requirements, the dependencies and how to get them, how to build CacheLib and the
benchmark, how to run the sweep, and how to copy the results into `Plots/` to draw the RQ3 figure.

## Availability

The libCacheSim and CacheLib code, including the S2-FIFO+ variants and benchmark scripts, has not been released yet, as the work is currently under review. The code will be made available once the paper is accepted for publication.
