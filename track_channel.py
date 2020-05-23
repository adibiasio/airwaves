"""Tracks channels over time
"""

import sys

import matplotlib as mpl
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import matplotlib.widgets as mplw
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
        self.real_channels = real_channels

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

    def _build_labels(self):
        label_list = gph.build_channel_labels(self.real_channels)
        self.labels = label_list

    def _graph(self):
        # Setting up figure & preparing Grid Layout
        self.fig = plt.figure(constrained_layout=True)
        main_grid = gridspec.GridSpec(13,7, figure=self.fig)
        self.widget_grid = gridspec.GridSpecFromSubplotSpec(4, 2, main_grid[8:13, 6])
        
        self.ax = plt.subplot(main_grid[:, :6])
        self.ax.xaxis.set_major_formatter(mpl.dates.DateFormatter("%m-%d\n%I:%M %p"))
        self.ax.grid()
        self.ax.set_xlabel("Time (mm/dd hh)")
        self.ax.set_prop_cycle(cycler('color', self.colors))

        # Graph lines
        for channel in self.real_channels:
            signal_measurement_col = self.signal_measurement + f"{channel}"
            line, = self.ax.plot(self.mdf["start_time"], self.mdf[signal_measurement_col])

        self.ax.set_title(f"{self.signal_measurement} of Antenna Instance {self.antenna} Over Time")
        self.ax.set_ylabel(self.signal_measurement)

        # Adding interactive legend
        handles = gph.make_patch(self.ax.lines, self.labels)
        leg_ncol = 3
        leg_fontsize = 12
        self.leg = self.fig.legend(
            handles=handles, 
            loc='upper right', 
            bbox_to_anchor=(0.98, 0.98), 
            shadow=True, 
            ncol=leg_ncol, 
            prop={'size': 7},
            fontsize=leg_fontsize
        )
        gph.enable_picking(self.ax.lines, self.leg, self.fig)

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
                    self.ax.set_prop_cycle(cycler('color', self.colors))
                    self.leg.remove()
                    self.ax.lines = []
                    lines_visible = True  
                    for signal_measurement in self.signal_measurements:
                        signal_measurement_col = signal_measurement + f"{channel}"
                        line, = self.ax.plot(self.mdf["start_time"], self.mdf[signal_measurement_col])
                    
                    # Recreate Legend & enable picking
                    handles = gph.make_patch(self.ax.lines, self.signal_measurements)
                    self.leg = self.fig.legend(
                        handles=handles, 
                        loc='upper right', 
                        bbox_to_anchor=(0.99, 0.98), 
                        shadow=True, 
                        ncol=len(self.signal_measurements)
                    )
                    gph.enable_picking(self.ax.lines, self.leg, self.fig)

                    title = f"Signal Measurements of Channel {channel} For Antenna Instance {self.antenna} Over Time"
                    y_label = "Signal Measurements"
                else:
                    return
            else:
                if len(self.leg.legendHandles) == len(self.real_channels):
                    # Executes when switching between signal measurement graphs
                    selected_channels = [_get_line_channel(line) for line in selected_lines]

                self.ax.set_prop_cycle(cycler('color', self.colors))
                self.ax.lines = []

                for channel in self.real_channels:
                    signal_measurement_col = self.signal_measurement + f"{channel}"
                    line, = self.ax.plot(self.mdf["start_time"], self.mdf[signal_measurement_col])

                if len(self.leg.legendHandles) != len(self.real_channels):
                    handles = gph.make_patch(self.ax.lines, self.labels)
                    self.leg.remove()
                    self.leg = self.fig.legend(
                        handles=handles, 
                        loc='upper right', 
                        bbox_to_anchor=(0.98, 0.98), 
                        shadow=True, 
                        ncol=3, 
                        prop={'size': 7}
                    )
                    selected_channels = [int(self.ax.title.get_text().split()[-1])]

                lines_visible = True if len(selected_channels) == 0 or len(selected_channels) == len(self.real_channels) else False  
                # Recreate picker map
                gph.enable_picking(self.ax.lines, self.leg, self.fig)
                
                title = f"{self.signal_measurement} of Antenna Instance {self.antenna} Over Time"
                y_label = self.signal_measurement
                
            # Set visibility of non selected lines
            if lines_visible:
                self.toggle_btn.label.set_text("Hide All")
                gph.set_all_vis(self.ax.lines, self.leg.legendHandles, self.fig, visible=lines_visible)
            else:
                lines = [line for line in self.ax.lines if _get_line_channel(line) not in selected_channels]
                patches = [patch for patch in self.leg.legendHandles
                            if int(plt.getp(patch, "label").split()[0]) in self.real_channels 
                            and int(plt.getp(patch, "label").split()[0]) not in selected_channels]
                gph.set_all_vis(lines, patches, self.fig, visible=lines_visible)

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
                gph.set_all_vis(self.ax.lines, self.leg.legendHandles, self.fig, visible=True)
            else:
                self.toggle_btn.label.set_text("Show All")
                gph.set_all_vis(self.ax.lines, self.leg.legendHandles, self.fig, visible=False)

        # Add widgets
        radio_ax = plt.subplot(self.widget_grid[2:3, 0])
        radio_btn_labels = self.signal_measurements[:] + ["All"]
        self.radio_btn = gph.MyRadioButtons(radio_ax, radio_btn_labels)
        self.radio_btn.on_clicked(_radio_btn_wrapper)

        toggle_btn_ax = plt.subplot(self.widget_grid[2:3,1])
        self.toggle_btn = mplw.Button(toggle_btn_ax, "Hide All")
        toggle_btn_ax._button = self.toggle_btn # Store button in axes
        self.toggle_btn.on_clicked(_toggle_btn_wrapper)

        text = "Click legend keys to toggle lines. Use the radio buttons " \
            "to switch between signal measurements. The \"All\" option displays " \
            "all signal measurements for 1 channel if it is the only 1 selected"
        self.fig.text(0.86, 0.01, text, wrap=True)
        plt.draw()


def main(args):
    """Handles cli arguments and runs the track channel program

    @param[in] args -   List of arguments passed into the cli
                        First three arguments are expected to be 
                        str signal_measurement, int antenna_instance, int real_channel
    """
    help_message = """Usage: track_channel signal_measurement real_channel [options]\nOptions:
    --help      Prints this help message and exits
    --range     Plots signal within date range
    --all       Plots all real channels
    """

    if "--help" in args:
        print(help_message)
        return

    if "--all" in args:
        df = load("mapping", cols=["channel"])
        real_channels = [channel for channel in df["channel"].unique().tolist()]
        track_channels = TrackChannels("snq", real_channels)
    else:
        try:
            if len(args) >= 2:
                real_channels = [int(arg) for arg in args[1:]]
            else:
                print("Invalid Arguments: Wrong number of arguments")
                return
        except ValueError:
            print("Invalid Arguments: Real Channels are of type \"int\"")
            return

        track_channels = TrackChannels(args[0], real_channels)

    track_channels.run()
    

if __name__ == "__main__":
    # main(sys.argv[1:])
    main(["snq", "27", "32", "--all"])
