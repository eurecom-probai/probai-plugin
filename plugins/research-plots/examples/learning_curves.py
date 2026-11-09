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

import _config as plot_config

OUTPUT_PATH = Path(__file__).with_suffix(".pdf")


def main():
    # Analytic curves and illustrative bands, with no empirical estimates.
    observations = np.geomspace(100, 10000, 65)
    methods = ["Method A", "Method B", "Method C"]
    markers = ["o", "s", "^"]
    with plt.rc_context():
        plot_config.configure_style()
        # ICML/AISTATS full width, one 2-inch row plus a shared legend.
        fig, axes = plt.subplots(1, 2, figsize=(6.75, 2.0), squeeze=False)
        try:
            for panel, ax in enumerate(axes.flat):
                for index, method in enumerate(methods):
                    rate = [0.58, 0.43, 0.32][index]
                    floor = [0.045, 0.06, 0.08][index]
                    curve = floor + (0.62 - 0.16 * panel) * (observations / 100) ** (-rate)
                    band = 0.025 * (observations / 100) ** (-0.25) * (1 - 0.25 * panel)
                    ax.fill_between(observations, curve - band, curve + band,
                                    color=plot_config.PALETTE[index], alpha=0.12, linewidth=0)
                    ax.plot(observations, curve, color=plot_config.PALETTE[index], label=method,
                            marker=markers[index], markevery=10)
                ax.set_xscale("log")
                ax.set_xlabel("Training observations")
                ax.set_ylabel("Error" if panel == 0 else "Calibration error")
                ax.set_title("Prediction" if panel == 0 else "Calibration")
                ax.set_ylim(bottom=0)
            handles, labels = axes[0, 0].get_legend_handles_labels()
            legend = fig.legend(handles, labels, loc="upper center", ncol=3, borderaxespad=0)
            legend.get_frame().set_linewidth(0.5)
            legend.get_frame().set_boxstyle("round", pad=0, rounding_size=plot_config.LEGEND_ROUNDING_SIZE)
            legend.set_in_layout(False)
            fig.draw_without_rendering()
            legend_height = legend.get_window_extent().height / fig.dpi
            height = 2.0 + legend_height + 0.10
            fig.set_size_inches(6.75, height)
            legend.set_bbox_to_anchor((0.5, 1 - 0.04 / height), transform=fig.transFigure)
            fig.tight_layout(pad=0.6, rect=(0, 0, 1, 2.0 / height))
            fig.draw_without_rendering()
            fig.savefig(OUTPUT_PATH, format="pdf")
            print(f"Saved {OUTPUT_PATH} ({fig.get_figwidth():.3f} x {fig.get_figheight():.3f} inches)")
        finally:
            plt.close(fig)


if __name__ == "__main__":
    main()
