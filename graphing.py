"""Common functions relating to graphing with matplotlib
"""

from abc import ABC, abstractmethod

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
        self.linestyles = ['solid', 'dashed', 'dashdot', 'dotted']
        self.colors = ["olive", "cyan", "lime", "red", "mediumpurple", 
                        "fuchsia", "darkorange", "dimgray", "darkblue", 
                        "darkgreen", "darkred", "purple", "saddlebrown", 
                        "pink", "peru", "teal", "gold", "tomato", "brown",
                        "slategray", "royalblue", "lightblue", "violet",
                        "rosybrown", "silver", "dodgerblue", "darkolivegreen",
                        "mistyrose", "darkkhaki", "bisque", "springgreen",
                        "crimson", "tan", "forestgreen", "thistle"]

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

    @abstractmethod
    def _build_labels(self):
        """Builds graph labels with real and virtual channel numbers
        """
        pass

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
        self.circles = self.box.legendHandles
        for c in self.circles:
            c.set_picker(5)
        self.cnt = 0
        self.observers = {}

        for circle in self.circles:
            add_to_picker_map(circle, self._on_radio_button_click)
        self.connect_event('pick_event', onpick)

    def _on_radio_button_click(self, event):
        """On click function for radio button

        @param[in] event - matplotlib picker event
        """
        if (self.ignore(event) or event.mouseevent.button != 1 or
            event.mouseevent.inaxes != self.ax):
            return
        if event.artist in self.circles:
            self.set_active(self.circles.index(event.artist))


def build_channel_labels(real_channels):
    """Creates labels with corresponding virtual channels

    @parameter[in] real_channels - List of real channels to map & create labels from
    @parameter[out] labels - List of real channel, virtual channel strings
    """
    labels = [str(channel) + "\n---" for channel in real_channels]
    mapping = load("mapping", cols=["channel", "virtual"])

    # Converting virtual channel & station name str to sorted virtual channel float
    mapping["virtual"] = pd.Series([float(virtual[0]) for virtual in mapping["virtual"].str.split().to_list()])
    mapping = mapping.sort_values(by="virtual")

    for real, virtual in zip(mapping["channel"].values, mapping["virtual"].values):
        if real in real_channels:
            i = real_channels.index(real)
            labels[i] += "\n" + str(virtual)

    return labels


def make_patch(lines, labels):
    """Creates a matplotlib patch of the same color for each line

    @param[out] patches - List of matplotlib Patch objects
    """
    patches = []
    for line, label in zip(lines, labels):
        color = plt.getp(line, "color")
        patch = mpl.patches.Patch(color=color, label=label)
        patches.append(patch)

    return patches


def toggle_vis(patch, original_obj, visible=None):
    """Toggles visibility of a patch and object

    @parameter[in] patch - matplotlib patch object
    @parameter[in] original_obj - matplotlib line/bar object
    @parameter[in] vis - Bool specifying visibility state
    """
    if isinstance(original_obj, mpl.container.BarContainer):
        # For bar graph
        for patch in original_obj.patches:
            vis = visible if type(visible) is bool else not plt.getp(patch, "visible")
            plt.setp(patch, visible=vis)
    else:
        # For line graph
        vis = visible if type(visible) is bool else not original_obj.get_visible()
        original_obj.set_visible(vis)
 
    # Change the alpha on legend to see toggled lines
    if vis:
        patch.set_alpha(1.0)
    else:
        patch.set_alpha(0.2)


def set_all_vis(objs, patches, fig, visible=True):
    """Toggles visibility of all objects

    @parameter[in] objs - List of matplotlib line/bar objects
    @parameter[in] patches - List of matplotlib patch objects
    @parameter[in] fig - matplotlib figure object
    @parameter[in] visible - Bool specifying visibility state
    """
    for patch, obj in zip(patches, objs):
        toggle_vis(patch, obj, visible=visible)
    fig.canvas.draw()


def add_to_picker_map(artist, func, pickermap=pickermap):
    """Adds artist and picker fn pair to pickermap dict

    @parameter[in] artist - matplotlib artist object
    @parameter[in] func - function to be called on artist click
    @parameter[in] pickermap - dict with artist: picker_fn pairs
    """
    if func != None:
        pickermap.update({artist:func})


def onpick(event, pickermap=pickermap):
    """General picker function, redirects pick event to correct
    function with pickermap

    @parameter[in] event - matplotlib picker event
    @parameter[in] pickermap - dict with artist: picker_fn pairs
    """
    if event.artist in pickermap:
        pickermap[event.artist](event)


def enable_picking(objs, leg, fig):
    """Enables legend picking (toggles obj on legend entry click)

    @parameter[in] objs - List of matplotlib line/bar objects
    @parameter[in] leg - matplotlib legend object
    @parameter[in] fig - matplotlib figure object
    """
    obj_d = dict()

    def _on_legend_pick(event):
        """on pick toggle line visibility

         @parameter[in] event - matplotlib pick_event
        """
        patch = event.artist
        original_obj = obj_d[patch]
        toggle_vis(patch, original_obj)
        fig.canvas.draw()

    for patch, obj in zip(leg.legendHandles, objs):
        patch.set_picker(5)
        obj_d[patch] = obj
        add_to_picker_map(patch, _on_legend_pick)

    fig.canvas.mpl_connect("pick_event", onpick)


if __name__ == "__main__":
    pass
