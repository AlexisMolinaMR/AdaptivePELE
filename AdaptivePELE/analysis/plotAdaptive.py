from __future__ import absolute_import, division, print_function, unicode_literals
import os
import glob
import argparse
import matplotlib.pyplot as plt
from AdaptivePELE.utilities import utilities
plt.style.use("ggplot")
avail_backend = utilities.get_available_backend()
if avail_backend is not None:
    plt.switch_backend(avail_backend)


def parseArguments():
    """
        Parse command line arguments

        :returns: int, int, int, str, bool, bool, int, str, bool, str, str, str, str -- Number of steps per epoch,
            column to plot in the X axis, column to plot in the Y axis, name of
            the files containing the simulation data, whether to plot the data
            as points, wether to plot the data as lines, column to use as color, range of trajectories to select, whether to color each trajectory differently, path where to store the plot, label of the x-axis, label of the y-axis, label for the colorbar
    """
    desc = "Plot relevant information from a simulation's report files.\n"\
           "It MUST be run from the root epoch folder (i.e., where it can find the folders 0/, 1/, 2/, ... lastEpoch/"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("steps", type=int, default=4, help="Pele steps per run")
    parser.add_argument("xcol", type=int, default=2, help="xcol")
    parser.add_argument("ycol", type=int, default=4, help="ycol")
    parser.add_argument("filename", type=str, default="report_", help="Report filename")
    parser.add_argument("-points", action="store_true", help="Plot using points")
    parser.add_argument("-lines", action="store_true", help="Plot using lines")
    parser.add_argument("-zcol", type=int, default=None, help="Column to define color according to metric")
    parser.add_argument("-traj_col", action="store_true", help="Color differently each trajectory")
    parser.add_argument("-t", "--traj_range", type=str, default=None, help="Range of trajs to select, e.g to select trajs from 1 to 10, 1:10")
    parser.add_argument("--output_path", type=str, default=None, help="Where to save the file, including the name of the image file (for exmple path/plot.png)")
    parser.add_argument("--xlabel", type=str, default=None, help="Label for the x axis")
    parser.add_argument("--ylabel", type=str, default=None, help="Label for the y axis")
    parser.add_argument("--cblabel", type=str, default=None, help="Label for the colorbar")

    args = parser.parse_args()
    return args.steps, args.xcol, args.ycol, args.filename, args.points, args.lines, args.zcol, args.traj_range, args.traj_col, args.output_path, args.xlabel, args.ylabel, args.cblabel


def addLine(data_plot, traj_num, epoch, steps, opt_dict, artists):
    """
        Add a line to the plot corresponding to a report file

        :param data_plot: Data from the report file
        :type data_plot: np.ndarray
        :param traj_num: Number of the report
        :type traj_num: int
        :param epoch: Epoch of the report
        :type epoch: int
        :param steps: Number of steps of the simulation
        :type steps: int
        :param opt_dict: Dictionary with plotting options
        :type opt_dict: dict
    """
    if opt_dict['withLines']:
        x = data_plot[:, opt_dict['col1']]+epoch*steps
        modifier = '-'
    else:
        x = data_plot[:, opt_dict['col1']]
        modifier = 'o'
    y = data_plot[:, opt_dict['col2']]
    if opt_dict['color'] is None:
        artists.extend(plt.plot(x, y, modifier, c=opt_dict['cmap'].to_rgba(epoch), markersize=2.5))
    elif opt_dict['color'] == -1:
        artists.extend(plt.plot(x, y, modifier, c=opt_dict['cmap'].to_rgba(traj_num), markersize=2.5))
    else:
        colors = data_plot[:, opt_dict['color']]
        if opt_dict['withLines']:
            plt.plot(x, y, '-k', linewidth=0.2, alpha=0.2)
        artists.append(plt.scatter(x, y, c=colors, cmap=opt_dict['cmap'].cmap, s=15, zorder=2))


def createPlot(reportName, column1, column2, stepsPerRun, printWithLines, paletteModifier, trajs_range=None, path_out=None, label_x=None, label_y=None, label_colorbar=None):
    """
        Generate a string to be passed to gnuplot

        :param reportName: Name of the files containing the simulation data
        :type reportName: str
        :param column1: Column to plot in the X axis
        :type column1: int
        :param column2: Column to plot in the Y axis
        :type column2: int
        :param stepsPerRun: Number of steps per epoch,
        :type stepsPerRun: int
        :param paletteModifier: Wheter to use the epoch as color or a column
        :type paletteModifier: int
        :param trajs_range: Range of trajectories to plot
        :type trajs_range: str
        :param path_out: Path where to store the plot
        :type path_out: str
        :param label_x: Label of the x-axis
        :type label_x: str
        :param label_y: Label of the y-axis
        :type label_y: str
        :param label_colorbar: Label of the colorbar
        :type label_colorbar: str
    """
    epochs = utilities.get_epoch_folders('.')
    numberOfEpochs = int(len(epochs))
    cmap_name = "viridis"

    dictionary = {'reportName': reportName, 'col2': column2, 'numberOfEpochs': numberOfEpochs,
                  'col1': column1, 'withLines': printWithLines, 'color': paletteModifier}
    annotations = []
    artists = []
    trajectory_range = set()
    if trajs_range is not None:
        start, end = map(int, traj_range.split(":"))
        trajectory_range = set(range(start, end+1))
    cmin = 1e10
    cmax = -1e10
    data_dict = {}
    max_report = 0
    min_report = 1e10
    for epoch in epochs:
        ep = int(epoch)
        reports = glob.glob(os.path.join(epoch, reportName+"*"))
        if not len(reports):
            raise ValueError("Could not find any reports with the given name!!")
        for report in glob.glob(os.path.join(epoch, reportName+"*")):
            report_num = utilities.getReportNum(report)
            max_report = max(max_report, report_num)
            min_report = min(min_report, report_num)
            if trajs_range is not None and report_num not in trajectory_range:
                continue
            data = utilities.loadtxtfile(report)
            if paletteModifier is not None and paletteModifier != -1:
                cmin = min(cmin, data[:, paletteModifier].min())
                cmax = max(cmax, data[:, paletteModifier].max())
            data_dict[(ep, report_num)] = data
    fig, ax = plt.subplots()
    ticks = None
    if paletteModifier == -1:
        cmin = min_report
        cmax = max_report
    if paletteModifier is None:
        cmin = int(epochs[0])
        cmax = int(epochs[-1])
        ticks = range(cmin, cmax+1)
    sm = plt.cm.ScalarMappable(cmap=plt.get_cmap(cmap_name), norm=plt.Normalize(vmin=cmin, vmax=cmax))
    sm.set_array([])
    dictionary['cmap'] = sm
    if paletteModifier != -1:
        cbar = plt.colorbar(sm, ticks=ticks)
        cbar.ax.zorder = -1
    for el in data_dict:
        addLine(data_dict[el], el[1], el[0], stepsPerRun, dictionary, artists)
        annotations.append(["Epoch: %d\nTrajectory: %d\nModel: %d" % (el[0], el[1], i+1) for i in range(len(data_dict[el]))])
    if label_x is not None:
        plt.xlabel(label_x)
    if label_y is not None:
        plt.ylabel(label_y)
        if paletteModifier is None:
            cbar.set_label("Epoch")
        if label_colorbar is not None:
            cbar.set_label(label_colorbar)

    annot = ax.annotate("", xy=(0, 0), xytext=(20, 20),
                        textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="w"),
                        arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)

    def modify_color(color):
        color_offset = 0.5
        color = list(color)
        for i in range(3):
            color[i] = min(color[i]+color_offset, 1)
        return tuple(color)

    def update_annot(ind, color, pos, index):
        """Update the information box of the selected point"""
        annot.xy = pos
        annot.set_text(annotations[index][int(ind["ind"][0])])
        annot.get_bbox_patch().set_facecolor(modify_color(color))
        annot.get_bbox_patch().set_alpha(0.8)
        annot.zorder = 10

    def locate_event(event):
        for j, el in enumerate(artists):
            found, info = el.contains(event)
            if found:
                return j, found, info, el
        return 0, False, None, None

    def extract_data(obj_plot, ind):
        try:
            x, y = obj_plot.get_data()
            x = x[ind["ind"][0]]
            y = y[ind["ind"][0]]
            return (x, y)
        except AttributeError:
            return obj_plot.get_offsets()[ind["ind"][0]]

    def extract_color(obj_plot, ind):
        try:
            return obj_plot.get_markerfacecolor()
        except AttributeError:
            return obj_plot.get_facecolor()[ind["ind"][0]]

    def hover(event):
        """Action to perform when hovering the mouse on a point"""
        vis = annot.get_visible()
        if event.inaxes == ax:
            index, cont, ind, obj = locate_event(event)
            if cont:
                update_annot(ind, extract_color(obj, ind), extract_data(obj, ind), index)
                annot.set_visible(True)
                fig.canvas.draw_idle()
            else:
                if vis:
                    annot.set_visible(False)
                    fig.canvas.draw_idle()
    # Respond to mouse motion
    fig.canvas.mpl_connect("motion_notify_event", hover)


def generatePlot(stepsPerRun, xcol, ycol, reportName, kindOfPrint, paletteModifier, trajs_range, path_to_save, xlabel, ylabel, cblabel):
    """
        Generate a template string to use with gnuplot

        :param stepsPerRun: Number of steps per epoch,
        :type stepsPerRun: int
        :param xcol: Column to plot in the X axis
        :type xcol: int
        :param ycol: Column to plot in the Y axis
        :type ycol: int
        :param reportName: Name of the files containing the simulation data
        :type reportName: str
        :param kindOfPrint:  Kind of lines to plot (solid or points)
        :type kindOfPrint: bool
        :param paletteModifier: Third column to specify color
        :type paletteModifier: int
        :param trajs_range: Range of trajectories to plot
        :type trajs_range: str
        :param path_to_save: Path the save the plot
        :type path_to_save: str
        :param xlabel: Label of the x axis
        :type xlabel: str
        :param ylabel: Label of the y axis
        :type ylabel: str
        :param cblabel: Label of the colorbar
        :type cblabel: str

        :returns: str -- String to plot using gnuplot
    """
    if kindOfPrint == "PRINT_RMSD_STEPS":
        printWithLines = True
    elif kindOfPrint == "PRINT_BE_RMSD":
        printWithLines = False
    createPlot(reportName, xcol, ycol, stepsPerRun, printWithLines, paletteModifier, trajs_range=trajs_range, path_out=path_to_save, label_x=xlabel, label_y=ylabel, label_colorbar=cblabel)
    if path_to_save is not None:
        folder, _ = os.path.split(path_to_save)
        if folder:
            utilities.makeFolder(folder)
        plt.savefig(path_to_save)
    plt.show()

if __name__ == "__main__":
    steps_Run, Xcol, Ycol, filename, be, rmsd, colModifier, traj_range, color_traj, output_path, xlab, ylab, cblab = parseArguments()
    Xcol -= 1
    Ycol -= 1
    if colModifier is not None:
        colModifier -= 1
    # VARIABLES TO SET WHEN PRINTING
    if be:
        kind_Print = "PRINT_BE_RMSD"
    elif rmsd:
        kind_Print = "PRINT_RMSD_STEPS"
    if color_traj:
        colModifier = -1

    generatePlot(steps_Run, Xcol, Ycol, filename, kind_Print, colModifier, traj_range, output_path, xlab, ylab, cblab)
