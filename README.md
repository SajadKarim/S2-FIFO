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

To run the benchmark, install the OS packages once, then build the dependencies, CacheLib, and the
benchmark with `setup.sh`, and start the sweep (Ubuntu 20.04 shown):

```bash
git clone -b btw27 https://github.com/SajadKarim/CacheLib.git && cd CacheLib

sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test    # g++ 11 on Ubuntu 20.04; not needed on 22.04
sudo apt-get install -y g++-11 git curl numactl time python3 python3-numpy
./contrib/prerequisites-ubuntu18.sh                       # OS packages of the CacheLib dependencies (uses sudo)

cd benchmark
./setup.sh                                                # dependencies at fixed revisions, CacheLib, and the benchmark; about an hour
nohup setsid ./run_all.sh > results.nohup.out 2>&1 &      # full sweep, 400 runs, about 18 hours
```

`setup.sh` fetches the CacheLib dependencies (folly, fbthrift, and others) at the revisions the results
were produced with and builds everything with g++ 11; `contrib/build.sh` alone does not work on this
branch. `run_all.sh` generates the Zipf traces (2.4 GB each) before the sweep if they are missing, with
the trace generator of libCacheSim, which it downloads; the traces are not part of either repository.
Both scripts can be run again after an interruption and continue where they stopped.

When the sweep has finished, `benchmark/results/cachelib_results.csv` contains all runs (Zipf skews 0.6,
0.8, 0.9, and 1.0, 1 to 16 threads, two cache sizes). Copy it into `Plots/` of this repository and run
`python3 RQ3Plot.py` to draw the RQ3 figure.

`benchmark/README.md` describes the requirements (a machine with at least two NUMA nodes and about
100 GB of free memory on one of them), the dependency revisions, the build steps that `setup.sh` runs,
smaller sweeps, the policies, and the result files.

## Availability

The libCacheSim and CacheLib code, including the S2-FIFO+ variants and benchmark scripts, has not been released yet, as the work is currently under review. The code will be made available once the paper is accepted for publication.
