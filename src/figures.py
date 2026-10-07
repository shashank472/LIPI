"""Paper figures (static PDF). Palette: validated reference categorical slots 1-3 (light mode)
and the blue sequential ramp; thin marks, recessive grid, legend for >=2 series."""
import os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P
from analyze import MULTI, load_ranks
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
CAT = ["#2a78d6", "#eb6834", "#1baf7a"]
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.linewidth": 0.6, "figure.facecolor": "white"})
LAB = {"en": "EN", "cm_rom": "CM-R", "cm_nat": "CM-N", "mono_nat": "MO-N", "mono_rom": "MO-R"}
SUF = ["en", "cm_rom", "cm_nat", "mono_nat", "mono_rom"]

def fig_forms(d):
    fw = d[(d.qform == "q_en") & d.model.isin(MULTI)]
    views = [v for v in ["raw", "translit", "gloss"] if v in set(fw.view)]
    names = {"raw": "Raw", "translit": "Translit", "gloss": "Gloss (LLM, write time)"}
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7), sharey=True)
    for ax, L, title in zip(axes, ["hi", "kn"], ["Hindi pool", "Kannada pool"]):
        x = np.arange(len(SUF)); w = 0.26
        for j, v in enumerate(views):
            vals = [100 * fw[(fw.view == v) & (fw.lang == L) & (fw.form == ("en" if s == "en" else f"{L}_{s}"))].r5.mean() for s in SUF]
            bars = ax.bar(x + (j - (len(views) - 1) / 2) * w, vals, w * 0.92, color=CAT[j], label=names[v], edgecolor=SURF, linewidth=0.8, zorder=3)
            if v in ("raw", "gloss"):
                for b, val in zip(bars, vals):
                    ax.text(b.get_x() + b.get_width() / 2, val + 1.2, f"{val:.0f}", ha="center", va="bottom", fontsize=6, color=INK2)
        ax.set_xticks(x, [LAB[s] for s in SUF], fontsize=7); ax.set_title(title, fontsize=8.5, color=INK, loc="left", pad=4)
        ax.grid(axis="y", color=GRID, linewidth=0.5, zorder=0); ax.set_ylim(0, 85)
        for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    axes[0].set_ylabel(f"Recall@5 (%)\nmean of {fw.model.nunique()} encoders")
    fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, ncol=3, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, 1.06))
    fig.tight_layout(); fig.savefig(P("paper/figures/fig_forms.pdf"), bbox_inches="tight"); plt.close(fig)

def fig_reverse(d):
    sub = d[d.model.isin(MULTI)]
    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    views = [("raw", "Raw"), ("gloss+qt", "Gloss + QT")]
    fig, axes = plt.subplots(1, 4, figsize=(7.4, 2.4), gridspec_kw={"wspace": 0.12})
    k = 0; im = None
    for L, lname in [("hi", "Hindi"), ("kn", "Kannada")]:
        qforms = ["q_en", f"q_{L}_cm_rom", f"q_{L}_mono_nat"]
        for v, vname in views:
            ax = axes[k]; k += 1
            M = np.array([[100 * sub[(sub.view == v) & (sub.lang == L) & (sub.form == ("en" if s == "en" else f"{L}_{s}")) & (sub.qform == q)].r5.mean()
                           for q in qforms] for s in SUF])
            im = ax.imshow(M, cmap=cmap, vmin=0, vmax=80, aspect="auto")
            for i in range(M.shape[0]):
                for j in range(M.shape[1]):
                    ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=6.5, color="white" if M[i, j] > 45 else INK)
            ax.set_xticks(range(3), ["EN", "CM-R", "MO-N"], fontsize=6.5); ax.set_yticks(range(5), [LAB[s] for s in SUF] if k == 1 else [""] * 5, fontsize=6.5); ax.tick_params(length=0)
            ax.set_title(f"{lname}: {vname}", fontsize=7.5, loc="left", color=INK)
            ax.set_xlabel("question form", fontsize=6.5)
            if k == 1: ax.set_ylabel("memory form", fontsize=6.5)
            for sp in ax.spines.values(): sp.set_visible(False)
    cb = fig.colorbar(im, ax=axes, fraction=0.02, pad=0.02); cb.set_label("Recall@5 (%)", fontsize=6.5); cb.ax.tick_params(labelsize=6)
    fig.savefig(P("paper/figures/fig_reverse.pdf"), bbox_inches="tight"); plt.close(fig)

if __name__ == "__main__":
    d = load_ranks(); fig_forms(d); fig_reverse(d); print("figures written")
