# S2-FIFO<M>
Artifacts for S2-FIFO<M>

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

- `benchmark/`: the scripts that run the simulations on the trace collections

To run the benchmark, build `cachesim` and start the sweep for each trace set (`traces_s3fifo` for the
S3-FIFO trace collections, `traces_new` for the other and synthetic traces):

```bash
cd libCacheSim
mkdir -p _build && cd _build && cmake -DCMAKE_BUILD_TYPE=Release .. && make -j cachesim && cd ..

cd benchmark/traces_s3fifo
gcc -O2 -o tracestat tracestat.c
bash list_traces.sh <traces root>     # list the traces under <traces root>/s3fifo
bash prepass.sh                       # count requests and unique objects of each trace
bash launch.sh <traces root>          # run all simulations in the background; results go to results.csv
bash status.sh                        # show the progress
```

The traces themselves are not part of the repository. The README files in `benchmark/traces_s3fifo/`,
`benchmark/traces_new/`, and `benchmark/trace_gen/` describe which traces are needed, their format and
folder layout, where they can be obtained, the settings of the scripts, and the result files.

## Throughput code and benchmark (CacheLib)

The throughput results in `Plots/cachelib_results.csv` were produced with CacheLib, extended with the
S2-FIFO+ variants. The code is in the branch `btw27` of
[github.com/SajadKarim/CacheLib](https://github.com/SajadKarim/CacheLib):

- `cachelib/allocator/`: the S2-FIFO+ variants as CacheLib eviction policies
- `benchmark/`: the multi-threaded benchmark and the script that runs the sweep

To run the benchmark, build CacheLib and the benchmark, and start the sweep:

```bash
cd CacheLib
./contrib/build.sh -j                  # dependencies into opt/cachelib, CacheLib into build-cachelib
cd build-cachelib && cmake -DCMAKE_BUILD_TYPE=Release . && make -j && cd ..

cd benchmark
cmake -S . -B _build -DCMAKE_BUILD_TYPE=Release && cmake --build _build -j
mkdir -p results
nohup setsid ./run_all.sh > results/nohup.out 2>&1 &     # full sweep, about 50 hours
```

When the sweep has finished, `benchmark/results/cachelib_results.csv` contains all runs. Copy it into
`Plots/` of this repository and run `python3 RQ3Plot.py` to draw the RQ3 figure.

`benchmark/README.md` describes the requirements (a machine with at least two NUMA nodes and the
trace generator of libCacheSim), the settings in `run_all.sh` to adjust for a new machine, smaller
sweeps, the policies, and the result files.

## Availability

The libCacheSim and CacheLib code, including the S2-FIFO+ variants and benchmark scripts, has not been released yet, as the work is currently under review. The code will be made available once the paper is accepted for publication.