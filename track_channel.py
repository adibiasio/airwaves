"""Tracks channels over time
"""

import sys
from itertools import cycle

import matplotlib as mpl
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cycler import cycler

import graphing as gph
from db import exists_in_db, load


class TrackChannels(gph.GraphProgram):
    """Graphs differences in signal measurements of channels over time (scan_instances)
    """
    def __init__(self, signal_measurement, real_channels):
        """@param[in] signal_measurement - str signal measurement
        @param[in] real_channels - List of int real_channels
        """
        super().__init__()
        self.signal_measurement = signal_measurement
        self.signal_measurements = ["snq", "ss", "seq"]
        self.real_channels = sorted(real_channels, reverse=True)

        self.visible_line_count = len(self.real_channels)
        self.antenna = None
        self.labels = None
        self.mdf = None

    def _validate_args(self):
        results = [exists_in_db("channel", "mapping", value=channel) for channel in self.real_channels]
        results.extend([exists_in_db(measurement, "signal") for measurement in self.signal_measurements])
        return False if False in results else True

    def _build_df(self):
        signals = pd.DataFrame()
        self.antenna = load("monitor", cols=["configured_antenna_instance"])["configured_antenna_instance"].to_list()[0]

        for channel in self.real_channels:
            df = load("signal", direct_query=f"""SELECT signal.scan_instance, snq, ss, seq
                                                FROM signal INNER JOIN scan ON signal.scan_instance = scan.scan_instance 
                                                WHERE channel={channel} AND antenna_instance={self.antenna}""")

            df.columns = ["scan_instance"] + [f"{measurement}{channel}" for measurement in self.signal_measurements]
            signals = pd.merge(signals, df, how="inner", on="scan_instance") if not signals.empty else df

        scans = load("scan", cols=["scan_instance", "start_time"], datetimes=["start_time"])
        self.mdf = pd.merge(signals, scans, how="inner", on=["scan_instance"]) # merged data frame

    def _graph(self):
        # Setting up figure & preparing Grid Layout
        self.fig = plt.figure(constrained_layout=True)
        main_grid = gridspec.GridSpec(13,7, figure=self.fig)
        self.widget_grid = gridspec.GridSpecFromSubplotSpec(4, 2, main_grid[8:13, 6])
        
        self.ax = plt.subplot(main_grid[:, :6])
        self.ax.xaxis.set_major_formatter(mpl.dates.DateFormatter("%m-%d-%y")) # Formats dates in x-axis
        self.ax.fmt_xdata = mpl.dates.DateFormatter("%m-%d-%y %I:%M %p") # Formats mouse's x-coordinate date in toolbar
        self.ax.xaxis_date()
        self.ax.grid()
        self.ax.set_xlabel("Time (mm-dd-yy)")

        # Graph lines
        for channel in self.real_channels:
            signal_measurement_col = self.signal_measurement + f"{channel}"
            line = gph.MyLine2D(self.mdf["start_time"], self.mdf[signal_measurement_col], color=next(self.color_cycle))
            self.ax.add_line(line)

        self.ax.set_xlim(min(self.mdf["start_time"]), max(self.mdf["start_time"]))
        self.ax.set_ylim(-1, 101)
        self.ax.set_title(f"{self.signal_measurement} of Antenna Instance {self.antenna} Over Time")
        self.ax.set_ylabel(self.signal_measurement)

        # Adding interactive legend
        handles = gph.make_patches(self.ax.lines, self.labels)
        leg_ncol = 3
        leg_fontsize = 12
        self.leg = self.fig.legend(
            handles=handles, 
            title="Channels",
            loc='upper right', 
            bbox_to_anchor=(0.98, 0.98), 
            shadow=True, 
            ncol=leg_ncol, 
            prop={'size': 7},
            fontsize=leg_fontsize
        )
        self.enable_picking(self.ax.lines, self.leg)

        def _graph_subplot(option):
            """Graphs lines and handles regraphing on radio btn clicks

            @param[in] option - str with radio btn option clicked
            """
            def _get_line_channel(line):
                """Gets a line's corresponding real channel number

                @param[in] line - matplotlib Line2D object
                """
                # line.axes.get_lines() returns a silent list
                ind = line.axes.get_lines().index(line)
                return int(self.leg.texts[ind].get_text().split()[0])

            selected_lines = [line for line in self.ax.lines if line.get_visible()]

            if option == "All":
                if len(selected_lines) == 1:
                    channel = _get_line_channel(selected_lines[0])
                    self.leg.remove()
                    self.ax.lines = []
                    self.color_cycle = cycle(self.colors) # reset color cycle
                    lines_visible = True  

                    for signal_measurement in self.signal_measurements:
                        signal_measurement_col = signal_measurement + f"{channel}"
                        line = gph.MyLine2D(self.mdf["start_time"], self.mdf[signal_measurement_col], color=next(self.color_cycle))
                        self.ax.add_line(line)
                    
                    # Recreate Legend & enable picking
                    handles = gph.make_patches(self.ax.lines, self.signal_measurements)
                    self.leg = self.fig.legend(
                        title=f"Real Channel {channel}",
                        handles=handles, 
                        loc='upper right', 
                        bbox_to_anchor=(0.99, 0.98), 
                        shadow=True, 
                        ncol=len(self.signal_measurements)
                    )
                    self.enable_picking(self.ax.lines, self.leg)

                    title = f"Signal Measurements of Channel {channel} For Antenna Instance {self.antenna} Over Time"
                    y_label = "Signal Measurements"
                else:
                    return
            else:
                try:
                    int(plt.getp(self.leg.legendHandles[0], "label").split()[0]) # var = 
                    # Executes when switching between signal measurement graphs
                    selected_channels = [_get_line_channel(line) for line in selected_lines]
                except ValueError:
                    selected_channels = [int(plt.getp(self.leg, "title").get_text().split()[-1])]

                self.color_cycle = cycle(self.colors) # reset color cycle
                self.ax.lines = []

                for channel in self.real_channels:
                    signal_measurement_col = self.signal_measurement + f"{channel}"
                    line = gph.MyLine2D(self.mdf["start_time"], self.mdf[signal_measurement_col], color=next(self.color_cycle))
                    self.ax.add_line(line)

                if len(self.leg.legendHandles) != len(self.real_channels): # if var
                    handles = gph.make_patches(self.ax.lines, self.labels)
                    self.leg.remove()
                    self.leg = self.fig.legend(
                        handles=handles, 
                        title="Channels",
                        loc='upper right', 
                        bbox_to_anchor=(0.98, 0.98), 
                        shadow=True, 
                        ncol=3, 
                        prop={'size': 7}
                    )

                lines_visible = True if len(selected_channels) == 0 or len(selected_channels) == len(self.real_channels) else False  
                # Recreate picker map
                self.enable_picking(self.ax.lines, self.leg)
                
                title = f"{self.signal_measurement} of Antenna Instance {self.antenna} Over Time"
                y_label = self.signal_measurement
                
            # Set visibility of non selected lines
            if lines_visible:
                self.toggle_btn.label.set_text("Hide All")
                self.set_all_vis(self.ax.lines, self.leg.legendHandles, visible=lines_visible)
            else:
                lines = [line for line in self.ax.lines if _get_line_channel(line) not in selected_channels]
                patches = [patch for patch in self.leg.legendHandles
                            if int(plt.getp(patch, "label").split()[0]) in self.real_channels 
                            and int(plt.getp(patch, "label").split()[0]) not in selected_channels]
                self.set_all_vis(lines, patches, visible=lines_visible)

            # Styling
            self.ax.set_title(title)
            self.ax.set_ylabel(y_label)
            plt.draw()

        # Widget wrapper functions
        def _radio_btn_wrapper(event):
            """Wrapper fn for changing signal_measurement

            @param[in] event - str with the selected radio btn option 
            """
            self.signal_measurement = event if event in self.signal_measurements else self.signal_measurement
            _graph_subplot(event)

        def _toggle_btn_wrapper(event):
            """Wrapper fn for toggling line visibility

            @param[in] event - matplotlib MouseEvent object
            """
            if self.toggle_btn.label.get_text() == "Show All":
                self.toggle_btn.label.set_text("Hide All")
                self.set_all_vis(self.ax.lines, self.leg.legendHandles, visible=True)
            else:
                self.toggle_btn.label.set_text("Show All")
                self.set_all_vis(self.ax.lines, self.leg.legendHandles, visible=False)
            
            if "All" in self.radio_btn.label_strings and self.radio_btn.value_selected != "All":
                self.radio_btn.stash_button("All")

        # Add widgets
        radio_ax = plt.subplot(self.widget_grid[2:3,0])
        radio_btn_labels = self.signal_measurements[:] + ["All"]
        self.radio_btn = gph.MyRadioButtons(radio_ax, radio_btn_labels)
        self.radio_btn.on_clicked(_radio_btn_wrapper)
        self.radio_btn.stash_button("All")

        toggle_btn_ax = plt.subplot(self.widget_grid[2:3,1])
        self.toggle_btn = mpl.widgets.Button(toggle_btn_ax, "Hide All")
        toggle_btn_ax._button = self.toggle_btn # Store button in axes
        self.toggle_btn.on_clicked(_toggle_btn_wrapper)

        text = "Click legend keys to toggle lines. Use radio buttons " \
            "to switch between signal measurements. The \"All\" option  " \
            "appears when one channel is selected, use it to view all measurements"
        self.fig.text(0.86, 0.01, text, wrap=True, fontsize=9)
        plt.draw()

    def _on_legend_pick(self, event):
        super()._on_legend_pick(event)
        if self.radio_btn.value_selected != "All":
            self.visible_line_count = [line.get_visible() for patch, line in self.legend_map.items()].count(True)
            if self.visible_line_count == 1:
                self.radio_btn.unstash_button("All")
            elif "All" in self.radio_btn.label_strings:
                self.radio_btn.stash_button("All")


if __name__ == "__main__":
    channel_df = load("mapping", cols=["channel"])
    real_channels = [channel for channel in channel_df["channel"].unique().tolist()]
    track_channels = TrackChannels("snq", real_channels)
    track_channels.run()
