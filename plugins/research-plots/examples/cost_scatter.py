# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.6", "seaborn>=0.12", "numpy>=1.23"]
# ///
"""Synthetic style example. Run with uv run; uses the adjacent _config.py."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

import _config as plot_config

OUTPUT_PATH = Path(__file__).with_suffix(".pdf")


def main():
    # Seeded synthetic observations; groups have fixed color and marker mappings.
    rng = np.random.default_rng(20261109)
    methods = ["Method A", "Method B", "Method C"]
    styles = ["o", "s", "^"]
    cost, error, labels = [], [], []
    for index, center in enumerate([1.1, 2.0, 3.1]):
        x = np.clip(rng.normal(center, 0.24, 45), 0.3, None)
        y = 0.42 - 0.075 * x + rng.normal(0, 0.025, len(x))
        cost.extend(x)
        error.extend(y)
        labels.extend([methods[index]] * len(x))
    with plt.rc_context():
        plot_config.configure_style()
        # ICML/AISTATS single column, one 2-inch row.
        fig, ax = plt.subplots(figsize=(3.25, 2.0))
        try:
            sns.scatterplot(x=cost, y=error, hue=labels, style=labels,
                            hue_order=methods, style_order=methods,
                            palette=dict(zip(methods, plot_config.PALETTE)),
                            markers=dict(zip(methods, styles)),
                            s=12, alpha=0.65, linewidth=0, legend=False, ax=ax)
            # Opaque handles use the shared legend marker scale.
            handles = [plt.Line2D([], [], color=plot_config.PALETTE[i], marker=styles[i],
                                  linestyle="none", markersize=3, label=name)
                       for i, name in enumerate(methods)]
            legend = ax.legend(handles=handles, loc="upper right")
            legend.get_frame().set_linewidth(0.5)
            legend.get_frame().set_boxstyle("round", pad=0, rounding_size=plot_config.LEGEND_ROUNDING_SIZE)
            ax.set(xlabel="Compute cost (relative)", ylabel="Prediction error",
                   xlim=(0.3, 4.0), ylim=(0.08, 0.45))
            fig.tight_layout(pad=0.6)
            fig.draw_without_rendering()
            fig.savefig(OUTPUT_PATH, format="pdf")
            print(f"Saved {OUTPUT_PATH} ({fig.get_figwidth():.3f} x {fig.get_figheight():.3f} inches)")
        finally:
            plt.close(fig)


if __name__ == "__main__":
    main()
