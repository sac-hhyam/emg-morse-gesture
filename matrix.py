
"""
plot_confusion_matrix_paper.py
Publication-style confusion matrix, similar to figures seen in
EMG/ML papers (seaborn heatmap, serif typography, clean academic styling).
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns

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

cm = np.array([
    [402,  49,   5],
    [246, 106,  16],
    [349,   9,  27],
])

cm_pct = cm.astype(float) / cm.sum(axis=1, keepdims=True) * 100

# ── figure ──
fig, ax = plt.subplots(figsize=(6, 5.2))

sns.heatmap(
    cm_pct,
    annot=False,
    cmap="Blues",          # standard academic sequential colormap
    cbar_kws={"label": "Recall (%)", "shrink": 0.85},
    square=True,
    linewidths=0.6,
    linecolor="white",
    vmin=0, vmax=100,
    ax=ax,
)

# ── annotate cells: count on top, percentage below ──
for i in range(len(class_names)):
    for j in range(len(class_names)):
        val_pct = cm_pct[i, j]
        count = cm[i, j]
        text_color = "white" if val_pct > 55 else "#1a1a1a"
        ax.text(j + 0.5, i + 0.40, f"{count}",
                ha="center", va="center", fontsize=13,
                fontweight="bold", color=text_color)
        ax.text(j + 0.5, i + 0.65, f"{val_pct:.1f}%",
                ha="center", va="center", fontsize=9.5,
                color=text_color, alpha=0.9)

# ── labels ──
ax.set_xticklabels(class_names, fontsize=11)
ax.set_yticklabels(class_names, fontsize=11, rotation=0)
ax.set_xlabel("Predicted label", fontsize=12, fontweight="bold", labelpad=10)
ax.set_ylabel("True label", fontsize=12, fontweight="bold", labelpad=10)
ax.set_title("Confusion Matrix\nGeneralization Test on Unseen Sessions (n = 1209)",
              fontsize=12.5, fontweight="bold", pad=14)

# subtle frame
for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(0.8)
    spine.set_color("#333333")

plt.tight_layout()
plt.savefig("confusion_matrix_paper.png", dpi=300, facecolor="white", bbox_inches="tight")
plt.savefig("confusion_matrix_paper.pdf", facecolor="white", bbox_inches="tight")  # vector for papers
plt.show()
print("Saved confusion_matrix_paper.png and .pdf")
