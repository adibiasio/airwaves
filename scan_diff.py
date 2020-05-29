"""Compares two scan instances
"""

import sys

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from db import exists_in_db, load
from graphing import GraphProgram

matplotlib.use("TkAgg")

class ScanDiff(GraphProgram):
    """Graphs differences in signal measurements between two scan instances
    """
    def __init__(self, signal_measurement, scans, compare):
        """@param[in] signal_measurement - str signal measurement
        @param[in] scans - List of int scan_instances
        @param[in] compare - Boolean: Determines graph mode "compare"
        """
        self.signal_measurement = signal_measurement
        self.scans = scans
        self.compare = compare
        self.labels = None
        self.mdf = None

    def _validate_args(self):
        results = [exists_in_db("scan_instance", "scan", value=scan) for scan in self.scans]
        results.append(exists_in_db(self.signal_measurement, "signal"))

        return False if False in results else True

    def _build_df(self):
        scan_dfs = []

        if self.signal_measurement == "snq":
            channels = load(f"""SELECT DISTINCT channel FROM signal 
                                WHERE (scan_instance = {self.scans[0]} 
                                OR scan_instance={self.scans[1]}) AND 
                                NOT snq = 0""")["channel"].to_list()
            temp_conditions = [("channel", channels)]
        else:
            temp_conditions = [("snq", 0, True)] # Channel is not watchable if snq = 0 

        # Retrieve relevant section of database
        cols=["scan_instance", "channel", self.signal_measurement]
        for scan in self.scans:
            filter_conditions = temp_conditions + [("scan_instance", scan)]
            scan_dfs.append(load(f"""SELECT scan_instance, channel, snq, ss, seq FROM
                                    signal WHERE scan_instance={scan} AND snq>0"""))

        # Sorting by scan 1's signal_measurement
        self.mdf = pd.merge(scan_dfs[0], scan_dfs[1], how="outer", on=["channel"], suffixes=("0", "1")) # merged data frame
        self.mdf = self.mdf.sort_values(by=self.signal_measurement + "1")
        self.real_channels = self.mdf["channel"].values.tolist()

        # Replacing NaN values
        for i in range(0, len(self.scans)):
            self.mdf[f"scan_instance{i}"].fillna(self.scans[i], inplace=True)
            self.mdf[f"{self.signal_measurement}{i}"].fillna(0, inplace=True)

    def _graph(self):
        width = 0.35  # the width of the bars
        self.fig, ax = plt.subplots(constrained_layout=True)
        x1 = self.mdf[self.signal_measurement + "0"]
        x2 = self.mdf[self.signal_measurement + "1"]

        if self.compare:
            x = np.arange(len(self.labels))  # the label locations
            bar1 = ax.bar(x - width/2, x1.values, width, label=f"Scan {self.scans[0]}")
            bar2 = ax.bar(x + width/2, x2.values, width, label=f"Scan {self.scans[1]}")
            leg = ax.legend()
            self.enable_picking([bar1, bar2], leg)
        else:
            # Create diff data set (scan1 - scan2)
            xdiff = x1 - x2
            xdiff = pd.Series.to_list(xdiff)
            colors = ["g" if diff > 0 else "r" for diff in xdiff] # when diff = 0, color is a placeholder

            x = np.arange(len(self.labels))  # label locations

            # Styling
            bars = ax.bar(x, xdiff, width, color=colors)
            line = ax.axhline(0, color="gray")
            text1 = ax.text(len(xdiff) - 5, max(xdiff) - 1, f"Scan {self.scans[0]} is better", bbox={'facecolor': 'green', 'alpha': 0.5, 'pad': 10})
            text2 = ax.text(len(xdiff) - 5, min(xdiff) + 0.5, f"Scan {self.scans[1]} is better", bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 10})

        # Labeling and styling graph
        ax.set_ylabel(self.signal_measurement)
        ax.set_xlabel("Channels")
        ax.set_title(f"{self.signal_measurement} of Scans {self.scans[0]} and {self.scans[1]}")
        ax.set_xticks(x)
        ax.set_xticklabels(self.labels)
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
                        First three are expected to be
                        str signal_measurement, int scan_instance, int scan_instance
    """

    # Handling cli arguments (type casting and arg parsing)
    help_message = """Usage: scan_diff signal_measurement scan_instance scan_instance [options]\nOptions:
    --help      Prints this help message and exits
    --compare   Creates grouped bar graph
    """

    if "--help" in args:
        print(help_message)
        return

    try:
        if len(args) >= 3:
            scans = [int(arg) for arg in args[1:3]]
        else:
            print("Invalid Arguments: Two scan instances are supported")
            return

    except ValueError:
        print("Invalid Arguments: Scan instances are of type \"int\"") 
        return

    compare = True if "--compare" in args else False

    scan_diff = ScanDiff(args[0], scans, compare)
    scan_diff.run()


if __name__ == "__main__":
    main(sys.argv[1:])
    # main(["ss", "80", "83", "--compare"])
