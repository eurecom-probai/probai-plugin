"""Project plotting defaults. Apply explicitly before creating a figure."""

import shutil
import sys

import matplotlib as mpl
from matplotlib import font_manager
import seaborn as sns

PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#4D4D4D"]
LEGEND_ROUNDING_SIZE = 0.4


def configure_style(body=10):
    """Apply the project's fonts, colors, and compact plotting defaults."""
    sns.set_theme(context="paper", style="white", palette=PALETTE)
    legend_size = max(6.0, 6.0 * body / 10)
    small, label = max(7.0, 7.0 * body / 10), max(7.0, 8.0 * body / 10)
    mpl.rcParams.update({
        "xtick.major.pad": 1,
        "ytick.major.pad": 1,
        "xtick.major.width": 0.5,
        "ytick.major.width": 0.5,
        "legend.labelspacing": 0.2,
        "legend.handletextpad": 0.4,
        "legend.borderaxespad": 0.2,
        "axes.xmargin": 0.02,
        "axes.ymargin": 0.05,
        "figure.dpi": 500,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white", "axes.facecolor": "white",
        "savefig.facecolor": "white", "savefig.transparent": False,
        "text.color": "#262626", "axes.labelcolor": "#262626",
        "axes.edgecolor": "#262626", "xtick.color": "#262626", "ytick.color": "#262626",
        "axes.grid": False, "axes.linewidth": 0.6,
        "axes.spines.left": True, "axes.spines.bottom": True,
        "xtick.direction": "out", "ytick.direction": "out",
        "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "xtick.minor.visible": False, "ytick.minor.visible": False,
        "xtick.top": False, "ytick.right": False,
        "xtick.bottom": True, "ytick.left": True,
        "lines.linewidth": 1.2, "lines.markersize": 3,
        "font.size": small, "font.weight": "normal",
        "axes.labelsize": label, "axes.titlesize": label,
        "axes.labelweight": "normal", "axes.titleweight": "normal",
        "xtick.labelsize": small, "ytick.labelsize": small,
        "legend.fontsize": legend_size, "legend.title_fontsize": legend_size,
        "legend.markerscale": 0.75, "legend.handlelength": 1.5,
        "legend.handleheight": 0.5, "legend.borderpad": 0.3,
        "legend.columnspacing": 1.2,
        "legend.frameon": True, "legend.facecolor": "white",
        "legend.framealpha": 1.0, "legend.edgecolor": "#B0B0B0",
        "legend.fancybox": True, "image.cmap": "viridis",
        "savefig.dpi": "figure", "savefig.bbox": None, "pdf.fonttype": 42,
        "figure.autolayout": False, "figure.constrained_layout.use": False,
    })
    use_tex = shutil.which("latex") is not None
    family = "Computer Modern Sans Serif"
    if not use_tex:
        available = {font.name for font in font_manager.fontManager.ttflist}
        family = next((name for name in (
            "Computer Modern Sans Serif", "Computer Modern Sans", "CMU Sans Serif",
            "Latin Modern Sans", "Latin Modern Sans 10", "DejaVu Sans",
        ) if name in available), "DejaVu Sans")
        print(f"LaTeX unavailable; using {family} and Computer Modern mathtext.", file=sys.stderr)
    mpl.rcParams.update({
        "text.usetex": use_tex, "font.family": "sans-serif",
        "font.sans-serif": [family], "font.serif": ["Computer Modern Roman"],
        "mathtext.fontset": "cm", "text.latex.preamble": "",
    })
