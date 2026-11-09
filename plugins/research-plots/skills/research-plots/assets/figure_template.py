"""Single-column line figure. Adapt the input columns and labels to the data."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import _config as plot_config

INPUT_PATH = Path(__file__).with_name("data.csv")
OUTPUT_PATH = Path(__file__).with_suffix(".pdf")


def main():
    # This figure expects CSV columns x,y, in plotting order.
    data = np.genfromtxt(INPUT_PATH, delimiter=",", names=True)
    with plt.rc_context():
        plot_config.configure_style()
        # Apply this figure's rcParams overrides here, if needed.
        fig, ax = plt.subplots(figsize=(3.25, 2.0))
        ax.plot(data["x"], data["y"], color=plot_config.PALETTE[0])
        ax.set(xlabel="x", ylabel="y")
        fig.tight_layout(pad=0.6)
        fig.savefig(OUTPUT_PATH, format="pdf")
        plt.close(fig)


if __name__ == "__main__":
    main()
