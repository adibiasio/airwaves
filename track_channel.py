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
from db import load

mpl.use("TkAgg")


class TrackChannels(gph.GraphProgram):
    """Graphs differences in signal measurements of channels over time (scan_instances)
    """
    def __init__(self):
        """@param[in] signal_measurement - str signal measurement
        @param[in] real_channels - List of int real_channels
        """
        super().__init__()
        self.signal_measurement = "snq"
        self.signal_measurements = ["snq", "ss", "seq"]

        self.visible_line_count = None
        self.antenna = None
        self.labels = None
        self.mdf = None

        self.cached_antennas = {}

    def _validate_args(self):
        return True

    def _build_df(self):
        signals = pd.DataFrame()
        if self.antenna == None:
            self.antenna = load("SELECT configured_antenna_instance FROM monitor")["configured_antenna_instance"].to_list()[0]
            self.real_channels = load("SELECT DISTINCT channel FROM signal WHERE snq>0")["channel"].to_list()
            self.real_channels = sorted(self.real_channels, reverse=True)
            self.visible_line_count = len(self.real_channels)

        elif self.antenna in self.cached_antennas.keys():
            self.mdf = self.cached_antennas[self.antenna][0]
            self.real_channels = self.cached_antennas[self.antenna][1]
            return

        for channel in self.real_channels:
            df = load(f"""SELECT signal.scan_instance, snq, ss, seq
                        FROM signal INNER JOIN scan ON signal.scan_instance = scan.scan_instance 
                        WHERE channel={channel} AND antenna_instance={self.antenna}""")

            df.columns = ["scan_instance"] + [f"{measurement}{channel}" for measurement in self.signal_measurements]
            signals = pd.merge(signals, df, how="inner", on="scan_instance") if not signals.empty else df

        scans = load("select scan_instance, datetime(start_time,'unixepoch','localtime') from scan")
        scans = scans.rename(columns={"datetime(start_time,'unixepoch','localtime')":"start_time"})
        scans = scans.astype({"start_time":"datetime64[ns]"})
        self.mdf = pd.merge(signals, scans, how="inner", on=["scan_instance"]) # merged data frame
        self.cached_antennas.update({self.antenna:(self.mdf,self.real_channels)})

    def _graph(self):
        # Setting up figure & preparing Grid Layout
        self.fig = plt.figure(constrained_layout=True)
        main_grid = gridspec.GridSpec(13,7, figure=self.fig)
        widget_grid = gridspec.GridSpecFromSubplotSpec(4, 2, main_grid[8:13, 6])
        text_input_grid = gridspec.GridSpecFromSubplotSpec(2, 1, widget_grid[1,:2])
        
        # Axes configuration
        self.ax = plt.subplot(main_grid[:, :6])
        self.ax.xaxis.set_major_formatter(mpl.dates.DateFormatter("%m-%d-%y")) # Formats dates in x-axis
        self.ax.fmt_xdata = mpl.dates.DateFormatter("%m-%d-%y %I:%M %p") # Formats mouse's x-coordinate date in toolbar
        self.ax.xaxis_date()
        self.ax.grid()
        self.ax.set_xlabel("Time (mm-dd-yy)")        
        self.ax.set_xlim(min(self.mdf["start_time"]), max(self.mdf["start_time"]))
        self.ax.set_ylim(-1, 101)
        self.ax.set_title(f"{self.signal_measurement} of Antenna Instance {self.antenna} Over Time")
        self.ax.set_ylabel(self.signal_measurement)
        virtual_channels = []

        # Graph lines
        for channel in self.real_channels:
            signal_measurement_col = self.signal_measurement + f"{channel}"
            line = gph.MyLine2D(self.mdf["start_time"], self.mdf[signal_measurement_col], color=next(self.color_cycle))
            self.ax.add_line(line)
            virtual_channels.extend(self.mapping.loc[self.mapping["channel"]==channel, "virtual"])

        legend_title = f"""Channels\n({len(self.real_channels)} Real and {len(virtual_channels)} Virtual Channels)"""

        def _make_legend(labels, title):
            """Adding interactive legend

            @param[in] labels - list of strings to be legend labels
            @param[in] title - string, legend title
            """
            self.leg.remove() if self.leg else ""

            handles = gph.make_patches(self.ax.lines, labels)
            self.leg = self.fig.legend(
                handles=handles, 
                title=title,
                loc='upper right', 
                shadow=True, 
                ncol=4, 
                prop={'size': 7},
                fontsize=12
            )

            if "\n" in title:
                plt.setp(self.leg.get_title(), multialignment='center')

            self.enable_picking(self.ax.lines, self.leg)

        _make_legend(self.labels, legend_title)

        def _graph_subplot(option):
            """Graphs lines and handles regraphing on radio btn clicks

            @param[in] option - str with radio btn option clicked
            """
            def _get_line_channel(line):
                """Gets a line's corresponding real channel number

                @param[in] line - matplotlib Line2D object
                """
                ind = line.axes.get_lines().index(line)
                return int(self.leg.texts[ind].get_text().split()[0])

            selected_lines = [line for line in self.ax.lines if line.get_visible()]

            if option == "All":
                try:
                    channel = _get_line_channel(selected_lines[0])
                except ValueError:
                    # The All option is already selected
                    return

                self.antenna_input.set_visible(False)
                self.antenna_input.set_val("(Select a Signal Measurement)")
                self.ax.lines = []
                self.color_cycle = cycle(self.colors) # reset color cycle
                lines_visible = True  

                for signal_measurement in self.signal_measurements:
                    signal_measurement_col = signal_measurement + f"{channel}"
                    line = gph.MyLine2D(self.mdf["start_time"], self.mdf[signal_measurement_col], color=next(self.color_cycle))
                    self.ax.add_line(line)

                _make_legend(self.signal_measurements, f"Real Channel {channel}")
                title = f"Signal Measurements of Channel {channel} For Antenna Instance {self.antenna} Over Time"
                y_label = "Signal Measurements"
            else:
                try:
                    int(plt.getp(self.leg.legendHandles[0], "label").split()[0])
                    # Executes when switching between signal measurement graphs
                    selected_channels = [_get_line_channel(line) for line in selected_lines]
                    new_legend = False
                except ValueError:
                    # Executes when switching from the "All" Option to a signal measurement option
                    selected_channels = [int(plt.getp(self.leg, "title").get_text().split()[-1])]
                    new_legend = True
                    
                    # Update antenna input
                    self.antenna_input.set_visible(True)
                    self.antenna_input.set_val(self.antenna)

                self.color_cycle = cycle(self.colors) # reset color cycle
                self.ax.lines = []
                virtual_channels = []

                for channel in self.real_channels:
                    signal_measurement_col = self.signal_measurement + f"{channel}"
                    line = gph.MyLine2D(self.mdf["start_time"], self.mdf[signal_measurement_col], color=next(self.color_cycle))
                    self.ax.add_line(line)
                    virtual_channels.extend(self.mapping.loc[self.mapping["channel"]==channel, "virtual"])

                legend_title = f"""Channels\n({len(self.real_channels)} Real and {len(virtual_channels)} Virtual Channels)"""
                lines_visible = True if len(selected_channels) == 0 or len(selected_channels) == len(self.real_channels) else False
                title = f"{self.signal_measurement} of Antenna Instance {self.antenna} Over Time"
                y_label = self.signal_measurement

                if new_legend:
                    _make_legend(self.labels, legend_title)
                else:
                    self.enable_picking(self.ax.lines, self.leg)
                
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

        # Widget wrapper functions
        def _on_text_box(event):
            """Wrapper fn for changing antenna instance

            @param[in] event - str with the submitted antenna instance
            """
            try:
                int(event)
            except ValueError:
                return

            if int(event) in load("SELECT antenna_instance FROM antenna")["antenna_instance"].to_list():
                self.antenna = int(event) 
            else:
                return

            self._build_df()
            _graph_subplot(self.radio_btn.value_selected)
            
            # Reset Visibility of all lines
            self.toggle_btn.label.set_text("Hide All")
            self.set_all_vis(self.ax.lines, self.leg.legendHandles, visible=True)
            self._update_radio_button()

            if min(self.mdf["start_time"]) == max(self.mdf["start_time"]):
                self.ax.set_xlim(min(self.mdf["start_time"]) - pd.to_timedelta(2, unit="d"), min(self.mdf["start_time"]) + pd.to_timedelta(2, unit="d"))
            else:
                self.ax.set_xlim(min(self.mdf["start_time"]), max(self.mdf["start_time"]))
            plt.draw()

        def _on_radio_btn(event):
            """Wrapper fn for changing signal_measurement

            @param[in] event - str with the selected radio btn option 
            """
            self.signal_measurement = event if event in self.signal_measurements else self.signal_measurement
            _graph_subplot(event)
            self._update_radio_button()
            plt.draw()

        def _on_toggle_btn(event):
            """Wrapper fn for toggling line visibility

            @param[in] event - matplotlib MouseEvent object
            """
            if self.toggle_btn.label.get_text() == "Show All":
                self.toggle_btn.label.set_text("Hide All")
                self.set_all_vis(self.ax.lines, self.leg.legendHandles, visible=True)
            else:
                self.toggle_btn.label.set_text("Show All")
                self.set_all_vis(self.ax.lines, self.leg.legendHandles, visible=False)
            
            self._update_radio_button()
            plt.draw()

        # Add widgets
        antenna_inupt_ax = plt.subplot(text_input_grid[1,0])  
        self.antenna_input = gph.MyTextBox(antenna_inupt_ax,"Antenna \nInstance: ", initial=str(self.antenna))
        self.antenna_input.on_submit(_on_text_box)

        radio_ax = plt.subplot(widget_grid[2:3,0])
        radio_btn_labels = self.signal_measurements[:] + ["All"]
        self.radio_btn = gph.MyRadioButtons(radio_ax, radio_btn_labels)
        self.radio_btn.on_clicked(_on_radio_btn)
        self.radio_btn.stash_button("All")

        toggle_btn_ax = plt.subplot(widget_grid[2:3,1])
        self.toggle_btn = mpl.widgets.Button(toggle_btn_ax, "Hide All")
        self.toggle_btn.on_clicked(_on_toggle_btn)

        directions = "Click lines or corresponding legend keys to toggle visiibility. Use " \
            "radio buttons to switch signal measurements. Configure antenna instance " \
            "with the text field. The \"All\" option appears " \
            "when one channel is selected, use it to view all measurements."
        self.fig.text(0.86, 0.01, directions, wrap=True, fontsize=9)
        plt.draw()

    def _update_radio_button(self):
        """Update stashed radio buttons
        """
        self.visible_line_count = [line.get_visible() for line in self.ax.lines].count(True)

        # Editing Radio Button Options
        if self.radio_btn.value_selected != "All":
            if self.visible_line_count == 1:
                self.radio_btn.unstash_button("All")
            elif "All" in self.radio_btn.label_strings:
                self.radio_btn.stash_button("All")

    def _on_legend_pick(self, event):
        super()._on_legend_pick(event)
        self._update_radio_button()

        # Keep visibility button up to date
        if self.visible_line_count == 0 and self.toggle_btn.label.get_text() == "Hide All":
            self.toggle_btn.label.set_text("Show All")
        elif self.visible_line_count == len(self.real_channels) and self.toggle_btn.label.get_text() == "Show All":
            self.toggle_btn.label.set_text("Hide All")

            
if __name__ == "__main__":
    track_channels = TrackChannels()
    track_channels.run()
