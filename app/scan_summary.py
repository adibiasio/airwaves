"""Graphs channel signal measurements for a given scan
"""

import pandas as pd
import plotly
import plotly.graph_objects as go

from db import load


class ScanSummary():
    def __init__(self):
        # default scan is latest scan
        self.scan = None
        self.labels = None

        self.default_antenna = load("SELECT configured_antenna_instance FROM monitor")["configured_antenna_instance"].to_list()[0]
        antenna_df = load("SELECT * FROM antenna")
        self.antenna_map = {instance: {"name": str(instance) + "; " + "Name: " + name + ", Location: " + location + ", Direction: " + str(direction) + " degrees, Comments: "}
                            for instance, name, location, direction, comment in zip(antenna_df["antenna_instance"], antenna_df["name"], antenna_df["location"], 
                            antenna_df["direction"], antenna_df["comment"])}

        # Remove quotations
        for i, description in enumerate(self.antenna_map.values()):
            if "'" in self.antenna_map[i + 1]["name"]:
                self.antenna_map[i + 1]["name"] = self.antenna_map[i + 1]["name"].replace("'", "")
            
            if "\"" in self.antenna_map[i + 1]["name"]:
                self.antenna_map[i + 1]["name"] = self.antenna_map[i + 1]["name"].replace("\"", "")

    def _build_df(self):
        self.df = load(f"SELECT * FROM signal WHERE scan_instance={self.scan} AND snq>0")
        self.real_channels = self.df["channel"].values.tolist()

    def _build_labels(self, antenna):
        """Builds graph labels with real and virtual channel numbers
        """
        self.labels = [str(channel) + "<br>---" for channel in self.real_channels]
        self.mapping = load("""SELECT channel, virtual FROM mapping 
                                WHERE channel IN (SELECT DISTINCT channel 
                                FROM signal INNER JOIN scan ON signal.scan_instance
                                 = scan.scan_instance WHERE antenna_instance=? 
                                AND snq>0)""", antenna)

        # Converting virtual channel & station name str to sorted virtual channel float
        self.mapping["virtual"] = pd.Series([float(virtual[0]) for virtual in self.mapping["virtual"].str.split().to_list()])

        for real, virtual in zip(self.mapping["channel"].values, self.mapping["virtual"].values):
            if real in self.real_channels:
                i = self.real_channels.index(real)
                self.labels[i] += "<br>" + str(virtual)

    def _graph(self):
        self.fig = go.Figure(data=[
            go.Bar(name="snq", x=self.labels, y=self.df["snq"], marker={"line": {"color": "black", "width": 1.5}}),
            go.Bar(name="ss", x=self.labels, y=self.df["ss"], marker={"line": {"color": "black", "width": 1.5}}),
            go.Bar(name="seq", x=self.labels, y=self.df["seq"], marker={"line": {"color": "black", "width": 1.5}}),
        ])

    def get_json(self, scantime=None, antenna=None):
        existing_antennas = load("SELECT antenna_instance FROM antenna")["antenna_instance"].tolist()

        if antenna not in existing_antennas:
            # return figure rendered for last antenna
            return plotly.io.to_json(self.fig)

        try:
            # Sets default and acts as an extra layer of sanitization
            int(scantime)
        except TypeError:
            scantime = "SELECT strftime('%s', 'now')"

        df = load("""SELECT * FROM scan WHERE antenna_instance=?
                     ORDER BY ABS(start_time - (?)) LIMIT 1;""", 
                     antenna , scantime)[["scan_instance", "start_time"]]

        self.scan = df["scan_instance"].values.tolist()[0]
        self.start_time = df["start_time"].values.tolist()[0] * 1000 # convert from seconds to miliseconds

        self._build_df()
        self._build_labels(antenna)
        self._graph()
        return plotly.io.to_json(self.fig)

    def get_antenna_range(self, antenna=None):
        existing_antennas = load("SELECT antenna_instance FROM antenna")["antenna_instance"].tolist()

        if antenna not in existing_antennas:
            return

        return {
            # Factor of 1000 used to convert from seconds to miliseconds
            "start": load("SELECT * FROM scan WHERE antenna_instance=? ORDER BY scan_instance ASC LIMIT 1", antenna)["start_time"].values.tolist()[0] * 1000, 
            "end": load("SELECT * FROM scan WHERE antenna_instance=? ORDER BY scan_instance DESC LIMIT 1", antenna)["start_time"].values.tolist()[0] * 1000
        }

if __name__ == "__main__":
    pass
