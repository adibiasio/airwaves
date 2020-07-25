"""Graphs differences in signal measurements of channels over time (scan instances)
"""

import json
from itertools import cycle

import pandas as pd
import plotly
import plotly.graph_objects as go

from db import load


class TrackChannels():
    def __init__(self):
        super().__init__()
        self.default_signal_measurement = "snq"
        self.signal_measurements = ["snq", "ss", "seq"]

        self.colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",  "#8c564b", 
                "#e377c2", "#7f7f7f", "#bcbd22", "#17becf", "goldenrod", "darkseagreen", 
                "palevioletred", "slateblue", "teal", "chocolate", "deepskyblue", "lightcoral", 
                "greenyellow", "dodgerblue",  "darksalmon", "khaki", "plum", "lightgreen", 
                "mediumslateblue", "olive", "darkgray", "fuschia", "ivory"]

        self.color_cycle = cycle(self.colors)

        self.default_antenna = load("SELECT configured_antenna_instance FROM monitor")["configured_antenna_instance"].to_list()[0]
        self.current_antenna = self.default_antenna
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

        self.fig = None
        self.real_channels = None
        self.labels = None
        self.mdf = None

    def _build_df(self):
        signals = pd.DataFrame()        
        for channel in self.real_channels:
            df = load("""SELECT signal.scan_instance, snq, ss, seq 
                        FROM signal LEFT JOIN scan ON signal.scan_instance = scan.scan_instance 
                        WHERE channel=? AND antenna_instance=?""", channel, self.current_antenna)

            df.columns = ["scan_instance"] + [f"{measurement}{channel}" for measurement in self.signal_measurements]
            signals = pd.merge(signals, df, how="inner", on="scan_instance") if not signals.empty else df

        annotationsdf = load("""SELECT status, temperature, wind_direction, wind_speed, 
                            humidity FROM weather LEFT JOIN scan ON scan.start_time = 
                            weather.start_time WHERE antenna_instance=?""", self.current_antenna)

        annotationsdf["annotations"] = [
                f"""Status: {status}<br>Temp: {str(temp)} F<br>Wind Direction: {str(winddirection)} Degrees<br>Wind Speed: {str(windspeed)} mph<br>Humidity: {str(humidity)}%"""
                for status, temp, winddirection, windspeed, humidity in
                zip(annotationsdf["status"], annotationsdf["temperature"], annotationsdf["wind_direction"], 
                annotationsdf["wind_speed"], annotationsdf["humidity"])
            ]

        annotationsdf = annotationsdf.drop(columns=["status", "temperature", "wind_direction", "wind_speed", "humidity"])

        scans = load("SELECT scan_instance, datetime(start_time,'unixepoch','-4 hours') as start_time FROM scan")
        # scans = scans.rename(columns={"datetime(start_time,'unixepoch','localtime')":"start_time"})
        scans = scans.astype({"start_time":"datetime64[ns]"})
        self.mdf = pd.merge(signals, scans, how="inner", on=["scan_instance"]) # merged data frame
        self.mdf = self.mdf.join(annotationsdf)

    def _build_labels(self):
        """Builds graph labels with real and virtual channel numbers
        """
        vertical_labels = [str(channel) + "<br>---" for channel in self.real_channels]
        horizontal_labels = [str(channel) + " |" for channel in self.real_channels]
        self.mapping = load("""SELECT channel, virtual FROM mapping 
                                WHERE channel IN (SELECT DISTINCT channel 
                                FROM signal INNER JOIN scan ON signal.scan_instance
                                 = scan.scan_instance WHERE antenna_instance=? 
                                AND snq>0)""", self.current_antenna)

        # Converting virtual channel & station name str to sorted virtual channel float
        self.mapping["floatVirtuals"] = pd.Series([float(virtual[0]) for virtual in self.mapping["virtual"].str.split().to_list()])
        self.mapping = self.mapping.sort_values(by="floatVirtuals")

        for real, virtual in zip(self.mapping["channel"].values, self.mapping["virtual"].values):
            if real in self.real_channels:
                i = self.real_channels.index(real)
                vertical_labels[i] += "<br>" + str(virtual)
                horizontal_labels[i] += "  " + str(virtual)

        self.labels = {channel: {"vertical": vertical + "<br>", "horizontal": horizontal} for (channel, vertical, horizontal) in zip(self.real_channels, vertical_labels, horizontal_labels)}

    def _graph(self):
        self.fig = go.Figure()
        xdata = self.mdf["start_time"]
        mode = "markers" if len(self.mdf["start_time"]) == 1 else "lines"

        update_xdata = True
        for signal_measurement in self.signal_measurements:
            visible = True if signal_measurement == self.default_signal_measurement else False
            self.color_cycle = cycle(self.colors) # reset color cycle
            for channel, color in zip(self.real_channels, self.color_cycle):
                col = f"{signal_measurement}{channel}"
                self.fig.add_trace(go.Scatter(x=xdata, y=self.mdf[col], mode=mode, name=channel, marker= {"color": color}))
                self.fig["data"][-1].visible = visible
                
                if update_xdata:
                    xdata = []
                    update_xdata = False
        
        # self.fig.layout = {
        #     "paper_bgcolor": 'rgba(0,0,0,0)',
        #     "plot_bgcolor": 'rgba(0,0,0,0)',
        #     "xaxis": {"gridcolor": "rgb(238,238,238)", "zerolinecolor": "rgb(68,68,68)"},
        #     "yaxis": {"gridcolor": "rgb(238,238,238)"}
        # }
        return self.fig

    def get_json(self, antenna=None):
        try:
            # Sets default and acts as an extra layer of sanitization
            int(antenna)
            self.current_antenna = antenna
        except TypeError:
            pass

        self.real_channels = load(f"""SELECT DISTINCT channel FROM (SELECT * FROM signal 
                                WHERE signal.scan_instance IN (SELECT scan_instance 
                                FROM scan WHERE antenna_instance={self.current_antenna})) WHERE snq>0;""")["channel"].to_list()
        self.real_channels = sorted(self.real_channels, reverse=True)

        self._build_labels()
        self._build_df()
        self._graph()

        return plotly.io.to_json(self.fig)


if __name__ == "__main__":
    pass
