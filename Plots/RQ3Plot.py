#!/usr/bin/env python3
"""Draws the throughput figure for RQ3 of the S2-FIFO+ paper.

Input: cachelib_results.csv, the CacheLib benchmark results in the same folder as this script.
Output: RQ3.png and RQ3.pdf, written next to this script.

The figure shows the throughput of each S2-FIFO variant relative to S3-FIFO over the number of threads,
with one column per Zipf skew and one row per cache size (300 MB and 3000 MB per thread).

Throughput is measured in requests per second. The benchmark harness reports MQPS as cache operations
per second, where every request is a get and every miss adds a set, so the request rate is
MQPS / (1 + miss ratio).

The vertical axis is logarithmic and labelled in percent. A speedup and a slowdown by the same factor,
for example +100% and -50%, therefore lie at the same distance from the S3-FIFO line at 0.

The results also contain runs with 24 threads and runs of the stock CacheLib policies. The figure shows
only 1 to 16 threads and only the S2-FIFO variants.
"""
import os, csv
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, NullLocator, FuncFormatter
from matplotlib.transforms import Bbox

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = "cachelib_results.csv"
BASE = "s3fifo"                               # baseline policy
THREADS = [1, 2, 4, 8, 16]                    # thread counts shown in the figure
PANELS = [("small", "300 MB/thread"), ("large", "3000 MB/thread")]   # cache size per thread and its label
W = 4.8                                       # width of the figure in inches, the text width of the paper

# Colours and fonts, the same as in RQ1and2Plots.py
C_INK, C_INK2, C_MUTED, C_GRID, C_AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({"font.size": 7.5, "axes.titlesize": 7.5, "axes.labelsize": 7.5, "xtick.labelsize": 6.5,
                     "ytick.labelsize": 6.5, "legend.fontsize": 6.5, "pdf.fonttype": 42, "ps.fonttype": 42,
                     "axes.edgecolor": C_AXIS, "axes.linewidth": .6, "xtick.color": C_INK2, "ytick.color": C_INK2,
                     "xtick.major.width": .6, "ytick.major.width": .6, "text.color": C_INK, "axes.labelcolor": C_INK})

# The S2-FIFO variants, grouped by policy family. Each family gets its own colour and its own column in
# the legend, and each variant within a family gets its own shade and marker.
# Each entry gives the policy name in the results file, the label, the family, the marker, the line style,
# and the colour.
REC, FREQ, DIS = "recency", "frequency", "disregard"
FAMILIES = [REC, FREQ, DIS]                   # preserve recency, order by frequency, disregard recency
VARIANTS = [
    ("s2fifo_plus_lru",            "LRU",              REC,  "o", "-",  "#0d366b"),
    ("s3fifo_clock1arr",           "CLOCK",            REC,  "s", "-",  "#1c5cab"),
    ("s2fifo_plus_gclockex",       "GCLOCK",           REC,  "^", "-",  "#2a78d6"),
    ("s3fifo_clocknarr",           "ClockBit",         REC,  "D", "-",  "#5598e7"),
    ("s2fifo_plus_clock_credit",   "ClockCredit",      REC,  "v", "-",  "#86b6ef"),
    ("s2fifo_plus_lfu",            "LFU",              FREQ, "s", ":",  "#eb6834"),
    ("s2fifo_plus_mru",            "MRU",              DIS,  "^", "--", "#0b6e4c"),
    ("s2fifo_plus_thresh_fifo",    "Threshold FIFO",   DIS,  "v", "--", "#1baf7a"),
    ("s2fifo_plus_random_uniform", "Random (uniform)", DIS,  "P", "--", "#72d1ad"),
]
ALPHAS = ["0.6", "0.8", "0.9", "1.0"]         # Zipf skews shown in the figure

# Read the results. TP maps (alpha, cache size, policy, threads) to million requests per second.
TP = {}
for r in csv.DictReader(open(os.path.join(HERE, SOURCE))):
    assert r["exit"] == "0" and "NA" not in r.values(), f"failed run: {r}"
    TP[(r["alpha"], r["panel"], r["policy"], int(r["threads"]))] = float(r["MQPS"]) / (1 + float(r["miss_ratio"]))
NEED = [BASE] + [p for p, *_ in VARIANTS]
missing = [(a, pa, p, t) for a in ALPHAS for pa, _ in PANELS for p in NEED for t in THREADS if (a, pa, p, t) not in TP]
assert not missing, f"missing results: {missing[:5]}"

def rel(a, pa, p, t):
    """Throughput of policy p divided by the throughput of S3-FIFO in the same configuration."""
    return TP[(a, pa, p, t)] / TP[(a, pa, BASE, t)]

# Draw the figure.
RT = [.1, .2, .5, .75, 1, 1.5, 2, 3]          # possible tick positions on the vertical axis, as ratios

def pct(v, _=None):
    """Tick label of a ratio as a percent difference, for example 0.5 becomes -50%."""
    d = round((v - 1) * 100)
    return "0" if d == 0 else f"{d:+d}%".replace("-", "−")

def style(p):
    """Line and marker style of a variant."""
    _, _, _, m, ls, c = next(v for v in VARIANTS if v[0] == p)
    return dict(color=c, lw=.9, ls=ls, marker=m, ms=2.6, mfc=c, mec="white", mew=.3, zorder=3)

def clean(ax):
    """Removes the top and right frame lines and adds a light grid."""
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.grid(axis="both", which="major", color=C_GRID, lw=.5); ax.set_axisbelow(True)

def thread_axis(ax):
    """Logarithmic thread axis with a label at each thread count."""
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(FixedLocator(THREADS)); ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: ""))
    ax.set_xlim(0.85, 19)
    for t in THREADS:
        ax.annotate(str(t), xy=(t, 0), xycoords=ax.get_xaxis_transform(), xytext=(0, -3.5),
                    textcoords="offset points", ha="center", va="top", fontsize=6, color=C_INK2,
                    annotation_clip=False)
    ax.xaxis.labelpad = 9

def legends(fig, axes):
    """Lists the S2-FIFO variants under one heading, with one column per family, and S3-FIFO on the left."""
    cols = [[v for v in VARIANTS if v[2] == f] for f in FAMILIES]
    n = max(len(c) for c in cols)
    hs = []
    for c in cols:
        for p, l, *_ in c:
            s = style(p); s.pop("zorder"); s["ms"] += 1
            hs.append(Line2D([], [], label=l, **s))
        hs += [Line2D([], [], ls="", marker="", label="")] * (n - len(c))   # empty entries fill short columns
    top = max(a.get_position().y1 for a in axes.flat)
    y = top + .2 / fig.get_size_inches()[1]
    kw = dict(frameon=False, handlelength=2.0, columnspacing=.9, handletextpad=.4, labelspacing=.2)
    lv = fig.legend(handles=hs, loc="lower left", bbox_to_anchor=(.30, y), ncol=len(cols),
                    title=r"S2-FIFO$\langle M\rangle$ with $M$ =", title_fontsize=6.5, **kw)
    lv._legend_box.align = "left"
    # Place S3-FIFO level with the first row of variants. An empty title gives it the same height above
    # its entry as the heading of the variants.
    ytop = lv.get_window_extent(fig.canvas.get_renderer()).transformed(fig.transFigure.inverted()).y1
    fig.legend(handles=[Line2D([], [], color=C_INK, lw=1.2, label="S3-FIFO (= 0)")], loc="upper right",
               bbox_to_anchor=(.28, ytop), title=" ", title_fontsize=6.5, **kw)

def save(fig, name):
    """Saves the figure as PNG and PDF, cropped to the plots and the legends."""
    # Matplotlib's automatic cropping can cut off legends placed outside the plots, so the crop box is
    # computed from the plots and the legends explicitly.
    r = fig.canvas.get_renderer()
    bbs = [fig.get_tightbbox(r, bbox_extra_artists=[t for ax in fig.axes for t in ax.texts] + list(fig.axes))]
    bbs += [lg.get_window_extent(r).transformed(fig.dpi_scale_trans.inverted()) for lg in fig.legends]
    bb = Bbox.union(bbs)
    bb = Bbox.from_extents(bb.x0 - .1, bb.y0 - .02, bb.x1 + .1, bb.y1 + .02)   # small margin, since text is slightly wider at 300 dpi
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(HERE, f"{name}.{ext}"), dpi=300 if ext == "png" else None, bbox_inches=bb)
    plt.close(fig)

def rq3():
    fig, axes = plt.subplots(len(PANELS), len(ALPHAS), figsize=(W, 1.6 * len(PANELS) + .55), sharey=True,
                             squeeze=False, gridspec_kw={"wspace": .1, "hspace": .38})
    vals = [rel(a, pa, p, t) for a in ALPHAS for pa, _ in PANELS for p, *_ in VARIANTS for t in THREADS]
    lo, hi = min(vals) / 1.12, max(vals) * 1.12
    for i, (pa, lab) in enumerate(PANELS):
        for j, a in enumerate(ALPHAS):
            ax = axes[i][j]
            ax.axhline(1, color=C_INK, lw=1.2, zorder=4)                  # the S3-FIFO line
            for p, *_ in VARIANTS[::-1]:
                ax.plot(THREADS, [rel(a, pa, p, t) for t in THREADS], **style(p))
            thread_axis(ax); clean(ax)
            ax.set_yscale("log")
            ax.yaxis.set_major_locator(FixedLocator([v for v in RT if lo <= v <= hi]))
            ax.yaxis.set_minor_locator(NullLocator())
            ax.yaxis.set_major_formatter(FuncFormatter(pct))
            ax.set_ylim(lo, hi)
            ax.set_title(f"α = {a}", loc="left", pad=2)
        axes[i][0].set_ylabel(f"{lab}\nThroughput vs. S3-FIFO")
    ax = axes[0][0]
    ax.text(.04, .97, "faster than S3-FIFO", transform=ax.transAxes, fontsize=5.6, color=C_MUTED, va="top")
    ax.text(.04, .03, "slower", transform=ax.transAxes, fontsize=5.6, color=C_MUTED, va="bottom")
    for ax in axes[-1]: ax.set_xlabel("Threads")
    legends(fig, axes)
    save(fig, "RQ3")

rq3()
print("wrote RQ3.png and RQ3.pdf to", HERE)
