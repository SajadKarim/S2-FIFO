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