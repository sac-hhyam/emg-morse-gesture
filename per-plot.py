"""
plot_metrics_paper.py
Publication-style grouped bar chart (precision/recall/F1 per class),
the kind typically seen in EMG/ML classification papers.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

# ── academic styling ──
mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif", "Liberation Serif"],
    "axes.linewidth": 0.8,
    "axes.edgecolor": "#333333",
    "xtick.color": "#222222",
    "ytick.color": "#222222",
    "text.color": "#111111",
})

# ── data ──
class_names = ["thumb", "two_finger", "fist"]
precision   = [0.403, 0.646, 0.562]
recall      = [0.882, 0.288, 0.070]
f1          = [0.553, 0.398, 0.125]

x = np.arange(len(class_names))
width = 0.25

# academic-paper-friendly muted palette
color_precision = "#4C72B0"
color_recall    = "#DD8452"
color_f1        = "#55A868"

fig, ax = plt.subplots(figsize=(7.5, 4.8))

b1 = ax.bar(x - width, precision, width, label="Precision",
            color=color_precision, edgecolor="black", linewidth=0.6)
b2 = ax.bar(x,         recall,    width, label="Recall",
            color=color_recall,    edgecolor="black", linewidth=0.6)
b3 = ax.bar(x + width, f1,        width, label="F1-score",
            color=color_f1,        edgecolor="black", linewidth=0.6)

# ── value labels on top of bars ──
def annotate_bars(bars):
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{height:.2f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8.5)

annotate_bars(b1)
annotate_bars(b2)
annotate_bars(b3)

# ── chance-level reference ──
ax.axhline(1/3, color="gray", linestyle="--", linewidth=0.9, alpha=0.7, zorder=0)
ax.text(len(class_names) - 0.5, 1/3 + 0.02, "chance level",
        fontsize=8.5, color="gray", style="italic", ha="right")

# ── formatting ──
ax.set_xticks(x)
ax.set_xticklabels(class_names, fontsize=11.5)
ax.set_ylabel("Score", fontsize=12, fontweight="bold")
ax.set_ylim(0, 1.05)
ax.set_title("Per-Class Classification Metrics\nGeneralization Test on Unseen Sessions",
              fontsize=12.5, fontweight="bold", pad=14)

ax.legend(frameon=True, fancybox=False, edgecolor="#333333",
          fontsize=10, loc="upper right")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, linestyle=":", linewidth=0.6, alpha=0.5)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig("per_class_metrics_paper.png", dpi=300, facecolor="white", bbox_inches="tight")
plt.savefig("per_class_metrics_paper.pdf", facecolor="white", bbox_inches="tight")
plt.show()
print("Saved per_class_metrics_paper.png and .pdf")