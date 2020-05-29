"""Common functions relating to graphing with matplotlib
"""

from abc import ABC, abstractmethod
from itertools import cycle

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.widgets import AxesWidget, RadioButtons

from db import load

pickermap = dict()


class GraphProgram(ABC):
    """ABC for a Graphing Program
    """
    def __init__(self):
        self.real_channels = None
        self.labels = None
        self.fig = None
        self.leg = None
        self.legend_map = None
        self.visible_object_count = 0

        self.colors = ["olive", "cyan", "lime", "red", "mediumpurple", 
                        "fuchsia", "darkorange", "dimgray", "darkblue", 
                        "darkgreen", "darkred", "purple", "saddlebrown", 
                        "pink", "peru", "teal", "gold", "tomato", "brown",
                        "slategray", "royalblue", "lightblue", "violet",
                        "rosybrown", "silver", "dodgerblue", "darkolivegreen",
                        "mistyrose", "darkkhaki", "bisque", "springgreen",
                        "crimson", "tan", "forestgreen", "thistle"]
        self.color_cycle = cycle(self.colors) # Generator for color cycle

    @abstractmethod
    def _validate_args(self):
        """Validates arg existence in db

        @param[out] Boolean (validation results)
        """
        pass

    @abstractmethod
    def _build_df(self):
        """Retrieves relevant data and builds a df
        """
        pass

    def _build_labels(self):
        """Builds graph labels with real and virtual channel numbers
        """
        labels = [str(channel) + "\n---" for channel in self.real_channels]
        self.mapping = load("SELECT channel, virtual FROM mapping")

        # Converting virtual channel & station name str to sorted virtual channel float
        self.mapping["virtual"] = pd.Series([float(virtual[0]) for virtual in self.mapping["virtual"].str.split().to_list()])
        self.mapping = self.mapping.sort_values(by="virtual")

        for real, virtual in zip(self.mapping["channel"].values, self.mapping["virtual"].values):
            if real in self.real_channels:
                i = self.real_channels.index(real)
                labels[i] += "\n" + str(virtual)

        self.labels = labels

    @abstractmethod
    def _graph(self):
        """Graphs the data onto an axes and figure
        """
        pass

    def run(self):
        """Runs the program
        """
        if not self._validate_args():
            return
        self._build_df()
        self._build_labels()
        self._graph()
        plt.show()

    # Adding graph functionality
    def set_all_vis(self, objs, patches, visible=True):
        """Toggles visibility of all objects

        @parameter[in] objs - List of matplotlib line/bar objects
        @parameter[in] patches - List of matplotlib patch objects
        @parameter[in] visible - Bool specifying visibility state
        """
        for patch, obj in zip(patches, objs):
            obj.toggle_vis(patch, visible=visible)

    def _on_legend_pick(self, event):
        """on pick toggle line visibility

        @parameter[in] event - matplotlib pick_event
        """
        try:
            # If object is clicked, it must be set to hidden
            # (Users can't click a hidden objects)
            event.artist.toggle_vis(self.legend_map[event.artist], visible=False)
        except AttributeError:
            # Users can toggle visibility of an object from the legend
            # unconditionally
            self.legend_map[event.artist].toggle_vis(event.artist)

    def enable_picking(self, objs, leg):
        """Enables legend picking (toggles obj on legend entry click)

        @parameter[in] objs - List of matplotlib line/bar objects
        @parameter[in] leg - matplotlib Legend objects
        """
        self.legend_map = dict()

        def _on_legend_pick_wrapper(event):
            """Wrapper function for _on_legend_pick fn

            @parameter[in] event - matplotlib pick_event
            """
            self._on_legend_pick(event)

        for patch, obj in zip(leg.legendHandles, objs):
            patch.set_picker(5)

            try:
                obj.set_picker(5)
            except AttributeError:
                pass
            
            self.legend_map[patch] = obj
            self.legend_map[obj] = patch
            pickermap.update({patch:_on_legend_pick_wrapper, obj:_on_legend_pick_wrapper})

        self.fig.canvas.mpl_connect("pick_event", onpick)


class MyLine2D(mpl.lines.Line2D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def toggle_vis(self, patch, visible=None):
        """Toggles visibility of a line object and its corresponding patch

        @parameter[in] patch - corresponding matplotlib patch object
        @parameter[in] visible - Bool specifying visibility state
        """
        vis = visible if type(visible) is bool else not self.get_visible()
        self.set_visible(vis)
    
        # Change the alpha on legend to see toggled lines
        if vis:
            patch.set_alpha(1.0)
        else:
            patch.set_alpha(0.2)

class MyRadioButtons(RadioButtons):
    """Class adapted from https://stackoverflow.com/questionss/55095111/displaying-radio-buttons-horizontally-in-matplotlib 
    """
    def __init__(self, ax, labels, active=0, activecolor='blue', size=49,
                 orientation="vertical", **kwargs):
        """
        Add radio buttons to an `~.axes.Axes`.
        Parameters
        ----------
        ax : `~matplotlib.axes.Axes`
            The axes to add the buttons to.
        labels : list of str
            The button labels.
        active : int
            The index of the initially selected button.
        activecolor : color
            The color of the selected button.
        size : float
            Size of the radio buttons
        orientation : str
            The orientation of the buttons: 'vertical' (default), or 'horizontal'.
        Further parameters are passed on to `Legend`.
        """
        AxesWidget.__init__(self, ax)
        self.activecolor = activecolor
        axcolor = ax.get_facecolor()
        self.value_selected = None
        self.stashed_buttons = []

        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_navigate(False)

        circles = []
        for i, label in enumerate(labels):
            if i == active:
                self.value_selected = label
                facecolor = activecolor
            else:
                facecolor = axcolor
            p = ax.scatter([],[], s=size, marker="o", edgecolor='black',
                           facecolor=facecolor)
            circles.append(p)
        if orientation == "horizontal":
            kwargs.update(ncol=len(labels), mode="expand")
        kwargs.setdefault("frameon", False)
        self.box = ax.legend(circles, labels, loc="center", **kwargs)
        self.labels = self.box.texts
        self.label_strings = [text.get_text() for text in self.labels]
        self.circles = self.box.legendHandles
        self.cnt = 0
        self.observers = {}
        self.ax = ax
        self._kwargs = kwargs

        for circle in self.circles:
            circle.set_picker(5)
            pickermap.update({circle:self._on_radio_button_click})
        self.connect_event('pick_event', onpick)

    def stash_button(self, label_str):
        """Stashes a Radio Button (Button and Label)

        @param[in] label_str - String with button label
        """
        if label_str in self.label_strings:
            button_num = self.label_strings.index(label_str)
            stash_label = self.label_strings[button_num]
            stash_text = self.labels[button_num]
            stash_circle = self.circles[button_num]

            for circle in self.circles:
                del pickermap[circle]

            self.labels.remove(stash_text)
            self.label_strings.remove(stash_label)
            self.circles.remove(stash_circle)
            self.stashed_buttons.append((stash_text, stash_circle, button_num))

            # Recreate Radio Button box
            self.box.remove()
            self.box = self.ax.legend(self.circles, self.label_strings, loc="center", **self._kwargs)
            self.circles = self.box.legendHandles
            for circle in self.circles:
                circle.set_picker(5)
                pickermap.update({circle:self._on_radio_button_click})
            plt.draw()

    def unstash_button(self, label):
        """Unstashes a Radio Button (Button and Label)

        @param[in] label - String with button label (matplotlib Text object)
        """
        # "button" is tuple of format (matplotlib.text.Text label, Circle circle, int index)
        stashed_labels = [button[0].get_text() for button in self.stashed_buttons]
        if label in stashed_labels:
            for circle in self.circles:
                del pickermap[circle]

            stashed_button_num = stashed_labels.index(label)
            button = self.stashed_buttons[stashed_button_num]
            self.labels.insert(button[2], button[0])
            self.label_strings.insert(button[2], button[0].get_text())
            self.circles.insert(button[2], button[1])
            self.stashed_buttons.remove(button)

            # Recreate Radio Button box & functions
            self.box.remove()
            self.box = self.ax.legend(self.circles, self.label_strings, loc="center", **self._kwargs)
            self.circles = self.box.legendHandles
            for circle in self.circles:
                circle.set_picker(5)
                pickermap.update({circle:self._on_radio_button_click})

            pickermap.update({button[1]:self._on_radio_button_click})
            plt.draw()

    def _on_radio_button_click(self, event):
        """On click function for radio button

        @param[in] event - matplotlib picker event
        """
        if (self.ignore(event) or event.mouseevent.button != 1 or
            event.mouseevent.inaxes != self.ax):
            return
        if event.artist in self.circles:
            self.set_active(self.circles.index(event.artist))


class MyTextBox(mpl.widgets.TextBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _click(self, event):
        if self.ignore(event):
            return
        if event.inaxes != self.ax:
            self.stop_typing()
            return
        if not self.eventson:
            return
        if not plt.getp(self.label, "visible"):
            return
        if event.canvas.mouse_grabber != self.ax:
            event.canvas.grab_mouse(self.ax)
        if not self.capturekeystrokes:
            self.begin_typing(event.x)
        self.position_cursor(event.x)

    def set_visible(self, visible):
        """Toggles visibility of the TextBox

        @parameter[in] visible - Bool specifying visibility state
        """
        plt.setp(self.label, visible=visible)
        plt.setp(self.text_disp, visible=visible)
        plt.setp(self.cursor, visible=visible)


def make_patches(objects, labels):
    """Creates a matplotlib patch of the same color for each matplotlib object (line/bar)

    @parameter[in] objects - List of matplotlib line/bar objects
    @return patches - List of matplotlib Patch objects
    """
    patches = []
    for obj, label in zip(objects, labels):
        color = plt.getp(obj, "color")
        patch = mpl.patches.Patch(color=color, label=label)
        patches.append(patch)

    return patches


def onpick(event):
    """General picker function, redirects pick event to correct
    function with pickermap

    @parameter[in] event - matplotlib picker event
    """
    if event.artist in pickermap:
        pickermap[event.artist](event)
    plt.draw()


if __name__ == "__main__":
    pass
