#!/usr/bin/env python3
"""Draws the miss-ratio figures for RQ1 and RQ2 of the S2-FIFO+ paper.

Input: sim_results_cmd.csv and sim_results_others.csv (libCacheSim results, in the same folder as this script).
Output: the following figures, each as .png and .pdf, written next to this script.
  RQ1   Mean miss-ratio difference of each S2-FIFO variant from S3-FIFO at three cache sizes,
        (a) averaged over all traces and (b) averaged over trace collections.
  RQ2a  Heatmap of the mean miss-ratio difference per trace collection and variant,
        with the three cache sizes stacked vertically.
  RQ2b  The same heatmap for the synthetic Zipf traces, one row per skew value.

The difference is the miss ratio of a variant minus the miss ratio of S3-FIFO, so a negative value means
the variant misses less often. Miss ratios count objects, not bytes, and use the full traces.
The synthetic traces are excluded from all averages, which leaves 13,234 production traces in 17 collections.
The Zipf traces are shown only in RQ2b.
"""
import os, csv, collections
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, SymLogNorm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = ["sim_results_cmd.csv", "sim_results_others.csv"]   # S3-FIFO trace collections; other and synthetic traces
EXCLUDE = {"adv", "zipf"}                     # synthetic collections, left out of all averages
BASE = "s3fifo"                               # baseline policy
# The S2-FIFO variants: policy name in the results file and its label in the figures
VARIANTS = [("S2FIFOPlusLRU", "LRU"), ("S2FIFOPlusClock1ex", "CLOCK"), ("S2FIFOPlusGClockex", "GCLOCK"),
            ("S2FIFOPlusClockBitex", "ClockBit"), ("S2FIFOPlusClockCredit", "ClockCredit"),
            ("S2FIFOPlusLFU", "LFU"),
            ("S2FIFOPlusMRU", "MRU"), ("S2FIFOPlusThreshFIFO", "Threshold FIFO"),
            ("S2FIFOPlusRandomBucket", "Random (bucket)"), ("S2FIFOPlusRandomUniform", "Random (uniform)")]
# Groups of variants, with the number of variants in each group (in the order of VARIANTS)
GROUPS = [("Policies that preserve recency", 5), ("Policies that order by frequency", 1),
          ("Policies that disregard recency", 4)]
SIZES = [("0.1", "10%"), ("0.01", "1%"), ("0.001", "0.1%")]   # cache size as a fraction of the footprint, and its label
# Workload family of each trace collection
FAMILY = {"tencentBlock": "block", "alibabaBlock": "block", "cloudphysics": "block", "msr": "block",
          "fiu": "block", "systor": "block", "k5cloud": "block", "spc": "block", "metaStorage": "block",
          "twitter": "key-value", "metaKV": "key-value", "dogi": "key-value",
          "metaCDN": "CDN / web", "tencentPhoto": "CDN / web", "wiki": "CDN / web",
          "ibm_objectstore": "object / blob", "tectonic": "object / blob"}
FAMILIES = ["block", "key-value", "CDN / web", "object / blob"]
SHORT = {"tencentBlock": "Tencent", "k5cloud": "K5", "alibabaBlock": "Alibaba", "cloudphysics": "CloudPhysics",
         "msr": "MSR", "fiu": "FIU", "systor": "Systor", "metaStorage": "Meta", "spc": "SPC", "twitter": "Twitter",
         "metaKV": "Meta", "dogi": "Dogi", "wiki": "Wiki", "metaCDN": "Meta", "tencentPhoto": "Tencent",
         "ibm_objectstore": "IBM", "tectonic": "Tectonic"}   # short row labels; the family label tells the "Meta" rows apart
W = 4.8                                       # width of the RQ1 figure in inches (text width of the paper)
VARIANT_HDR = "S2-FIFO⟨M⟩"                     # heading above or below the variant labels

# Colours: shades of blue for the cache sizes; blue (better), gray, and red (worse) for the heatmaps
C_SIZE = {"0.1": "#86b6ef", "0.01": "#2a78d6", "0.001": "#104281"}
M_SIZE = {"0.1": "o", "0.01": "s", "0.001": "^"}
C_INK, C_INK2, C_MUTED, C_GRID, C_AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
DIVERGING = LinearSegmentedColormap.from_list("bgr", ["#184f95", "#6da7ec", "#f0efec", "#ec8a86", "#b3302f"])
plt.rcParams.update({"font.size": 7.5, "axes.titlesize": 7.5, "axes.labelsize": 7.5, "xtick.labelsize": 7,
                     "ytick.labelsize": 7, "legend.fontsize": 7, "pdf.fonttype": 42, "ps.fonttype": 42,
                     "axes.edgecolor": C_AXIS, "axes.linewidth": .6, "xtick.color": C_INK2, "ytick.color": C_INK2,
                     "xtick.major.width": .6, "ytick.major.width": .6, "text.color": C_INK, "axes.labelcolor": C_INK})

# Load the results
mr = collections.defaultdict(dict)            # miss ratios of the production traces, by trace file and cache size
COLL = {}                                     # trace collection of each trace file
ZMR = collections.defaultdict(dict)           # miss ratios of the synthetic Zipf traces, by trace and cache size
for src in SOURCES:
    for r in csv.DictReader(open(os.path.join(HERE, src))):
        if r["collection"] == "zipf": ZMR[(r["trace"], r["frac"])][r["policy"]] = float(r["miss_ratio"])
        if r["collection"] in EXCLUDE: continue
        mr[(r["file"], r["frac"])][r["policy"]] = float(r["miss_ratio"]); COLL[r["file"]] = r["collection"]
# Check that every trace has a result for every policy and cache size
NEED = [BASE] + [v for v, _ in VARIANTS]
FILES = sorted({f for f, _ in mr})
missing = [(f, fr) for f in FILES for fr, _ in SIZES if not all(p in mr.get((f, fr), {}) for p in NEED)]
assert not missing, f"{len(missing)} incomplete cells, e.g. {missing[:3]}"
# Order of the collections in the heatmap: by family, then by number of traces (largest first), then by name.
# Sorting by name last keeps the order fixed when two collections have the same number of traces.
COLLS = sorted({COLL[f] for f in FILES}, key=lambda c: (FAMILIES.index(FAMILY[c]), -sum(COLL[f] == c for f in FILES), c))
coll_arr = np.array([COLL[f] for f in FILES])
# Per-trace difference from S3-FIFO for every variant and cache size
S3 = {fr: np.array([mr[(f, fr)][BASE] for f in FILES]) for fr, _ in SIZES}
D = {(p, fr): np.array([mr[(f, fr)][p] for f in FILES]) - S3[fr] for p, _ in VARIANTS for fr, _ in SIZES}
# The same for the Zipf traces, ordered by skew
ZIPF = sorted({t for t, _ in ZMR}, key=lambda t: float(t.split("_a")[1]))
ZS3 = {fr: np.array([ZMR[(t, fr)][BASE] for t in ZIPF]) for fr, _ in SIZES}
ZD = {(p, fr): np.array([ZMR[(t, fr)][p] for t in ZIPF]) - ZS3[fr] for p, _ in VARIANTS for fr, _ in SIZES}
print(f"{len(FILES)} traces, {len(COLLS)} collections, {len(ZIPF)} Zipf traces")

def tmean(p, fr): return D[(p, fr)].mean()                                         # average over all traces
def cmean(p, fr): return np.mean([D[(p, fr)][coll_arr == c].mean() for c in COLLS])  # average of the collection averages

def save(fig, name):
    """Write the figure as .png and .pdf next to this script."""
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, f"{name}.{ext}"), dpi=300 if ext == "png" else None, bbox_inches="tight",
                    pad_inches=0.02)
    plt.close(fig)

def clean(ax):
    """Remove the top and right borders and add vertical grid lines."""
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.grid(axis="x", color=C_GRID, lw=.5); ax.set_axisbelow(True)

# The horizontal axis of RQ1 is linear between -0.001 and +0.001 and logarithmic outside this range
LT = 1e-3
DTICKS = [-0.001, 0, 0.001, 0.01, 0.1]
def dlabel(v):
    """Axis label with an explicit sign, for example +0.01."""
    if v == 0: return "0"
    return ("−" if v < 0 else "+") + (f"{abs(v):g}")
def symlog_x(ax, lo=-0.005, hi=0.45):
    # matplotlib 3.3 renamed the parameters of the symlog scale; older versions ignore the new names without an error
    if tuple(int(x) for x in matplotlib.__version__.split(".")[:2]) >= (3, 3):
        ax.set_xscale("symlog", linthresh=LT, linscale=0.6)
    else:
        ax.set_xscale("symlog", linthreshx=LT, linscalex=0.6)
    ax.set_xlim(lo, hi); ax.set_xticks(DTICKS); ax.set_xticklabels([dlabel(v) for v in DTICKS])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())

def variant_rows(gap=0.8):
    """Vertical position of each variant and of each group heading, with extra space between groups."""
    ys, glab, y = [], [], 0.0
    for g, n in GROUPS:
        glab.append((g, y - 0.62))
        for _ in range(n): ys.append(y); y += 1
        y += gap
    return np.array(ys), glab

# RQ1: mean difference per variant as a dot plot, with the variant labels on both sides
def rq1():
    ys, glab = variant_rows()
    fig, axes = plt.subplots(1, 2, figsize=(W, 2.75), sharey=True, gridspec_kw={"wspace": 0.08})
    off = {"0.1": -0.22, "0.01": 0.0, "0.001": 0.22}
    for ax, agg, lab in zip(axes, (tmean, cmean), ("(a) mean over 13,234 traces", "(b) mean over 17 trace collections")):
        ax.axvspan(-LT, LT, color="#f4f3f0", zorder=0, lw=0)   # shade the linear part of the axis
        ax.axvline(0, color=C_INK2, lw=.6, zorder=1)
        for fr, _ in SIZES:
            xs = [agg(v, fr) for v, _ in VARIANTS]
            ax.scatter(xs, ys + off[fr], s=16, marker=M_SIZE[fr], color=C_SIZE[fr], edgecolor="white", lw=.4, zorder=3)
        symlog_x(ax); clean(ax)
        ax.set_xlabel("Δ miss ratio vs. S3-FIFO   (← better)")
        ax.text(0.0, 1.0, lab, transform=ax.transAxes, ha="left", va="bottom", fontsize=7.5, color=C_INK)
        for g, gy in glab[1:]:
            ax.axhline(gy - 0.4, color=C_GRID, lw=.5, zorder=0)
    axes[0].set_yticks(ys); axes[0].set_yticklabels([n for _, n in VARIANTS]); axes[0].tick_params(axis="y", length=0)
    for g, gy in glab: axes[0].text(-0.0048, gy + 0.05, g, fontsize=6.3, color=C_MUTED, style="italic", va="center")
    axes[0].set_ylim(ys[-1] + 0.6, -1.0)
    HDR = dict(fontsize=plt.rcParams["ytick.labelsize"], color=C_INK2, va="bottom")   # same style as the variant labels
    axes[0].text(-0.03, 1.0, VARIANT_HDR, transform=axes[0].transAxes, ha="right", **HDR)
    axes[1].text(1.03, 1.0, VARIANT_HDR, transform=axes[1].transAxes, ha="left", **HDR)
    axes[1].tick_params(axis="y", which="both", left=False, right=False, labelleft=False, labelright=True, length=0)
    axes[0].spines["right"].set_visible(True)                                              # borders between the panels
    axes[1].spines["left"].set_visible(True); axes[1].spines["right"].set_visible(True)    # and next to the right labels
    hs = [Line2D([], [], ls="", marker=M_SIZE[fr], ms=5, color=C_SIZE[fr], mec="white", mew=.4,
                 label=f"Cache = {lab} of footprint") for fr, lab in SIZES]
    hs.append(Patch(color="#f4f3f0", label="Linear scale (|Δ| < 0.001)"))
    axes[0].legend(handles=hs, ncol=2, loc="lower center", bbox_to_anchor=(1.04, 1.07), frameon=False,
                   handletextpad=0.3, columnspacing=1.2)
    save(fig, "RQ1")

# RQ2: heatmaps of the mean difference (colour scale is linear near 0 and logarithmic beyond)
VMAX = 0.35
NORM = SymLogNorm(linthresh=LT, linscale=1.0, vmin=-VMAX, vmax=VMAX)
def cell_txt(v):
    """Cell text: the difference in units of 0.001, with a sign."""
    k = v * 1000
    if abs(k) < 0.05: return "0"
    return f"{k:+.1f}".replace("-", "−") if abs(k) < 9.95 else f"{k:+.0f}".replace("-", "−")
def heat_matrix(fr, zipf=False):
    """Row labels and values of one heatmap panel."""
    if zipf:   # the uniform Zipf trace (skew 0) is left out, since all variants have almost the same miss ratio on it
        keep = [i for i, t in enumerate(ZIPF) if float(t.split("_a")[1]) > 0]
        return ([f"Zipf α = {ZIPF[i].split('_a')[1]}" for i in keep],
                np.array([[ZD[(v, fr)][i] for v, _ in VARIANTS] for i in keep]))
    return ([SHORT[c] for c in COLLS],
            np.array([[D[(v, fr)][coll_arr == c].mean() for v, _ in VARIANTS] for c in COLLS]))
def heat(ax, fr, fs=5.0, lfs=6.0, zipf=False):
    """Draw one heatmap panel with its values, separators, and family labels."""
    labels, M = heat_matrix(fr, zipf)
    im = ax.imshow(M, cmap=DIVERGING, norm=NORM, aspect="auto", interpolation="none")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            # white text on dark cells, black text on light cells
            rgb = DIVERGING(NORM(M[i, j]))[:3]; lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
            ax.text(j, i, cell_txt(M[i, j]), ha="center", va="center", fontsize=fs,
                    color="white" if lum < 0.5 else C_INK)
    ax.set_xticks(range(len(VARIANTS))); ax.set_xticklabels([n for _, n in VARIANTS], rotation=45, ha="right")
    ax.tick_params(length=0)
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=lfs)
    # white lines between the variant groups (vertical) and between the workload families (horizontal)
    x = -0.5
    for _, n in GROUPS[:-1]: x += n; ax.axvline(x, color="white", lw=2)
    fam_rows = [] if zipf else [sum(FAMILY[c] == f for c in COLLS) for f in FAMILIES]; y = -0.5
    for f, n in zip(FAMILIES, fam_rows):
        ax.text(len(VARIANTS) - 0.35, y + n / 2, f, ha="left", va="center", fontsize=6.3, color=C_MUTED,
                style="italic", clip_on=False)
        if f != FAMILIES[-1]: ax.axhline(y + n, color="white", lw=2)
        y += n
    for sp in ax.spines.values(): sp.set_visible(False)
    return im
def colorbar(fig, im, cax):
    """Vertical colour scale with tick labels in units of 0.001."""
    cb = fig.colorbar(im, cax=cax, orientation="vertical")
    t = [-0.1, -0.01, -0.001, 0, 0.001, 0.01, 0.1]
    cb.set_ticks(t); cb.set_ticklabels([cell_txt(v).replace(".0", "") if v else "0" for v in t])
    cb.minorticks_off(); cb.outline.set_visible(False); cb.ax.tick_params(length=2, labelsize=6)
    cb.set_label("mean Δ miss ratio vs. S3-FIFO (×10⁻³);  blue = better, red = worse", fontsize=6.5)
    return cb

GEOM = {}                                     # cell size and spacing of RQ2a in inches, reused by RQ2b
def rq2a(hspace=0.13, title_pad=2, height=8.6):
    """Heatmap of the production trace collections, three cache sizes stacked, colour scale on the right."""
    fig, axes = plt.subplots(3, 1, figsize=(3.9, height), gridspec_kw={"hspace": hspace})
    for k, (ax, (fr, lab)) in enumerate(zip(axes, SIZES)):
        im = heat(ax, fr)
        ax.set_title(f"Cache = {lab} of footprint", fontsize=7, loc="left", pad=title_pad)
        if k < 2: ax.tick_params(labelbottom=False)
    axes[-1].set_xlabel(VARIANT_HDR, fontsize=plt.rcParams["xtick.labelsize"], color=C_INK2, labelpad=2)
    # place the colour scale to the right of the family labels, over the full height of the three panels
    fig.canvas.draw(); r = fig.canvas.get_renderer(); inv = fig.transFigure.inverted()
    xmax = max(t.get_window_extent(r).transformed(inv).x1 for ax in axes for t in ax.texts)
    top, bot = axes[0].get_position().y1, axes[-1].get_position().y0
    colorbar(fig, im, fig.add_axes([xmax + 0.04, bot, 0.022, top - bot]))
    # remember the cell size and spacing so that RQ2b looks the same
    fw, fh = fig.get_size_inches(); p0, p1, p2 = (a.get_position() for a in axes)
    GEOM.update(left=p0.x0 * fw, width=p0.width * fw, row_h=p0.height * fh / len(COLLS),
                gap=(p0.y0 - p1.y1) * fh, top=(1 - p0.y1) * fh, bottom=p2.y0 * fh,
                cb_gap=0.04 * fw, cb_w=0.022 * fw)
    save(fig, "RQ2a")

def rq2b(title_pad=2):
    """Heatmap of the Zipf traces with the same cell size and spacing as RQ2a, so rq2a must run first."""
    g = GEOM; panel = len(heat_matrix("0.1", zipf=True)[0]) * g["row_h"]
    H = g["top"] + 3 * panel + 2 * g["gap"] + g["bottom"]
    W6 = g["left"] + g["width"] + g["cb_gap"] + g["cb_w"] + 0.6          # 0.6 inches for the colour-scale labels
    fig = plt.figure(figsize=(W6, H)); axes = []
    top = H - g["top"]
    for k, (fr, lab) in enumerate(SIZES):
        y0 = top - panel
        ax = fig.add_axes([g["left"] / W6, y0 / H, g["width"] / W6, panel / H]); axes.append(ax)
        im = heat(ax, fr, zipf=True)
        ax.set_title(f"Cache = {lab} of footprint", fontsize=7, loc="left", pad=title_pad)
        if k < 2: ax.tick_params(labelbottom=False)
        top = y0 - g["gap"]
    axes[-1].set_xlabel(VARIANT_HDR, fontsize=plt.rcParams["xtick.labelsize"], color=C_INK2, labelpad=2)
    t, b = axes[0].get_position().y1, axes[-1].get_position().y0
    cb = colorbar(fig, im, fig.add_axes([(g["left"] + g["width"] + g["cb_gap"]) / W6, b, g["cb_w"] / W6, t - b]))
    # the colour scale is shorter than in RQ2a, so its label is split over two lines
    cb.set_label("mean Δ miss ratio vs. S3-FIFO (×10⁻³)\nblue = better, red = worse", fontsize=6.5)
    save(fig, "RQ2b")

rq1(); rq2a(); rq2b()
print("wrote RQ1, RQ2a and RQ2b (.png and .pdf) next to this script")
