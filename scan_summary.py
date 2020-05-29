"""Graphs ss, snq, and seq for a scan
"""

import sys

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from db import exists_in_db, load
from graphing import GraphProgram

matplotlib.use("TkAgg")

class ScanSummary(GraphProgram):
    """Graphs ss, snq, and seq for a single scan
    """
    def __init__(self, scan):
        """@param[in] scan - int scan_instance
        """
        self.scan = scan
        self.labels = None
        self.mdf = None

    def _validate_args(self):
        return exists_in_db("scan_instance", "scan", value=self.scan)

    def _build_df(self):
        # Retrieve relevant section of database
        self.df = load(f"SELECT * FROM signal WHERE scan_instance={self.scan} AND snq>0")
        self.real_channels = self.df["channel"].values.tolist()

    def _graph(self):
        width=0.25
        self.fig, ax = plt.subplots(constrained_layout=True)

        # Getting data
        snq = self.df["snq"].values
        ss = self.df["ss"].values
        seq = self.df["seq"].values

        xloc = np.arange(len(self.labels))  # the label locations
        bars = []

        for x, y, label in zip([xloc-width, xloc, xloc+width], [snq, ss, seq], ["snq", "ss", "seq"]):
            bars.append(ax.bar(x, y, width, label=label))

        # Labeling and styling graph
        ax.set_ylabel("Signal Measurement")
        ax.set_xlabel("Channels")
        ax.set_title(f"Summary of Scan {self.scan}")
        ax.set_xticks(xloc)
        ax.set_xticklabels(self.labels)
        leg = ax.legend()
        self.enable_picking(bars, leg)
        ax.plot()

    def _on_legend_pick(self, event):
        """on pick toggle the visibility of all bars of a group

        @parameter[in] event - matplotlib pick_event
        """
        patch = event.artist

        for bar in self.legend_map[patch]:
            vis = not plt.getp(bar, "visible")
            plt.setp(bar, visible=vis)

        # Change the alpha on legend to see toggled lines
        if vis:
            patch.set_alpha(1.0)
        else:
            patch.set_alpha(0.2)


def main(args): 
    """Handles cli arguments and runs the scan diff program

    @param[in] args -   List of arguments passed into the cli
                        First expected to be int scan_instance
    """

    # Handling cli arguments (type casting and arg parsing)
    help_message = """Usage: scan_summary scan_instance
    """

    if "--help" in args:
        print(help_message)
        return

    try:
        if len(args) == 1:
            scan = int(args[0])
        else:
            print("Invalid Arguments: One scan instance is supported")
            return

    except ValueError:
        print("Invalid Arguments: Scan instances are of type \"int\"") 
        return

    scan_summary = ScanSummary(scan)
    scan_summary.run()


if __name__ == "__main__":
    main(sys.argv[1:])
    # main(["83"])
