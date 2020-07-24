"""Graphs signal measurement distribution for a channel
"""

import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
from plotly.figure_factory import create_distplot

from db import load


class ChannelDistribution():
    def __init__(self):
        # default channel is latest scan
        self.channel = None
        self.labels = None
        self.signal_measurements = ["snq", "ss", "seq"]

        self.default_antenna = load("SELECT configured_antenna_instance FROM monitor")["configured_antenna_instance"].to_list()[0]
        self.default_channel = load("""SELECT channel FROM mapping WHERE channel IN (SELECT DISTINCT channel FROM signal 
                                        INNER JOIN scan ON signal.scan_instance = scan.scan_instance WHERE antenna_instance=? 
                                        AND snq>0) ORDER BY channel ASC LIMIT 1""", self.default_antenna)["channel"].values.tolist()[0]

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

        self.weather_map = { 
            self.default_antenna: 
            load("""SELECT DISTINCT(status) FROM weather INNER JOIN 
                    scan ON weather.start_time = scan.start_time WHERE 
                    antenna_instance=?""", self.default_antenna)["status"].values.tolist()
        }

        self.filter_col_labels = ["hour_of_day", "weather.start_time", "temperature", "wind_direction", "wind_speed", "humidity", "status"]
        self.max_filter_conditions = 7

    def _build_df(self, channel, antenna, filter_conditions, inversetod):
        qstrings = []
        qvalues = []

        if filter_conditions != None:
            if inversetod:
                start_splice = 1
                qstrings.append(" AND (hour_of_day>=? OR hour_of_day<=?)")
                qvalues.extend(filter_conditions["hour_of_day"])
            else:
                start_splice = 0
            
            for col_label in self.filter_col_labels[start_splice:6]:
                new_q = f" AND {col_label}>=? AND {col_label}<=?" if filter_conditions[col_label] else ""
                qstrings.append(new_q)

                if filter_conditions[col_label]:
                    qvalues.extend(filter_conditions[col_label])

            if filter_conditions["status"] != None:
                qstrings.append(" AND status=?")
                qvalues.append(filter_conditions["status"])

        else:
            qstrings = ["" for i in range(self.max_filter_conditions)]

        self.df = load(
            """SELECT signal.scan_instance, signal.ss, signal.snq, signal.seq, 
            scan.antenna_instance, weather.start_time, weather.start_time - 
            strftime('%s', weather.start_time, "unixepoch", "start of day") 
            as hour_of_day, weather.reference_time, weather.status, 
            weather.temperature, weather.wind_direction, weather.status, 
            weather.temperature, weather.wind_direction, weather.sunset 
            FROM signal 
            LEFT JOIN scan ON signal.scan_instance = scan.scan_instance 
            LEFT JOIN weather ON scan.start_time = weather.start_time 
            WHERE channel=? AND antenna_instance=?""" + "".join(qstrings),
            channel, antenna, *qvalues
        )

        channeldf = load("""SELECT DISTINCT channel FROM signal INNER JOIN 
                            scan ON signal.scan_instance = scan.scan_instance 
                            WHERE antenna_instance=? AND snq>0;""", antenna)

        self.real_channels = sorted(channeldf["channel"].values.tolist(), reverse=True)

    def _build_labels(self, antenna):
        """Builds graph labels with real and virtual channel numbers
        """
        self.labels = {channel: str(channel) + ": " for channel in self.real_channels}
        self.mapping = load("""SELECT channel, virtual FROM mapping 
                                WHERE channel IN (SELECT DISTINCT channel 
                                FROM signal INNER JOIN scan ON signal.scan_instance
                                 = scan.scan_instance WHERE antenna_instance=? 
                                AND snq>0)""", antenna)

        for real, virtual in zip(self.mapping["channel"].values, self.mapping["virtual"].values):
            if real in self.real_channels:
                self.labels[real] += ", " + str(virtual)

        for channel in self.labels.keys():
            self.labels[channel] = self.labels[channel].replace(", ", "", 1)

    def _graph(self, curve, histnorm):
        # scan_range used to avoid a singular matrix error
        # resulting from the signal measurements forming a singular matrix
        scan_range = len(self.df["snq"])

        if scan_range > 1:
            for i in reversed(range(1, len(self.df["snq"]) + 1)):
                try:
                    lines = create_distplot([self.df["snq"].iloc[0:i], self.df["ss"].iloc[0:i], self.df["seq"].iloc[0:i]], self.signal_measurements,
                                                bin_size=1, curve_type=curve, show_rug=False, histnorm=histnorm)
                    scan_range = i
                    models = [lines.data[3], lines.data[4], lines.data[5]]
                    break
                except np.linalg.LinAlgError:
                    # Error Raised: 
                    # numpy.linalg.LinAlgError: singular matrix
                    pass
        else:
            models = [go.Scatter(x=[scan_range], y = self.df[signal], legendgroup=signal, showlegend=False) for signal in self.signal_measurements]

        self.fig = go.Figure(data=[
            go.Histogram(x=self.df["snq"].iloc[0:scan_range], name="snq", legendgroup="snq", 
                opacity=0.75, bingroup=1, xbins={"size": 1}, marker={"line": {"color": "black", "width": 1.5}}),
            go.Histogram(x=self.df["ss"].iloc[0:scan_range], name="ss", legendgroup="ss", 
                opacity=0.75, bingroup=1, xbins={"size": 1}, marker={"line": {"color": "black", "width": 1.5}}),
            go.Histogram(x=self.df["seq"].iloc[0:scan_range], name="seq", legendgroup="seq", 
                opacity=0.75, bingroup=1, xbins={"size": 1}, marker={"line": {"color": "black", "width": 1.5}}),
            models[0],
            models[1],
            models[2]
        ])
        self.fig.update_traces(visible=True)

    def get_json(self, channel=None, antenna=None, model="kde", histnorm="", filter_conditions=None, inversetod=False):
        self._build_df(channel, antenna, filter_conditions, inversetod)
        self._build_labels(antenna)
        self._graph(model, histnorm)
        self.channel_label = self.labels[channel] if channel in self.labels.keys() else self.labels[list(self.labels)[0]]
        self.channel_label = self.channel_label.replace(": ", "<br>---<br>")
        self.channel_label = self.channel_label.replace(", ", "<br>")

        return plotly.io.to_json(self.fig)

    def get_channel_map(self, antenna=None):
        existing_antennas = load("SELECT antenna_instance FROM antenna")["antenna_instance"].tolist()

        if antenna not in existing_antennas:
            antenna = self.default_antenna

        channeldf = load("""SELECT DISTINCT channel FROM signal INNER JOIN 
                            scan ON signal.scan_instance = scan.scan_instance 
                            WHERE antenna_instance=? AND snq>0;""", antenna)

        self.real_channels = sorted(channeldf["channel"].values.tolist(), reverse=True)

        self._build_labels(antenna)
        return self.labels

    def get_weather_map(self, antenna=None):
        existing_antennas = load("SELECT antenna_instance FROM antenna")["antenna_instance"].tolist()

        if antenna not in existing_antennas:
            antenna = self.default_antenna

        self.weather_map = { 
            antenna: 
            load("""SELECT DISTINCT(status) FROM weather INNER JOIN 
                    scan ON weather.start_time = scan.start_time WHERE 
                    antenna_instance=?""", antenna)["status"].values.tolist()
        }

        return self.weather_map

if __name__ == "__main__":
    pass
