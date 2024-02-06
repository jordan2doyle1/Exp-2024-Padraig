#
# Author Jordan Doyle.
#
# usage: bar_plot.py [-h] [-v] [-o OUTPUT] -r RESULTS
#
# options:
#   -h, --help                          show this help message and exit
#   -o OUTPUT, --output OUTPUT          output directory
#   -r RESULTS, --results RESULTS       results base directory
#   -v, --verbose                       output all log messages
#

import argparse
import logging
import os
import re
import sys
import xml.etree.ElementTree as ElementTree
from datetime import datetime
from statistics import mean

import matplotlib.pyplot as mpl
import numpy as np
import pandas
import scipy
import tikzplotlib
from bs4 import BeautifulSoup

from VD_A import VD_A

argParser = argparse.ArgumentParser()
argParser.add_argument("-o", "--output", type=str, default='output', help="output directory")
argParser.add_argument("-r", "--results", type=str, required=True, help="results base directory")
argParser.add_argument("-v", "--verbose", default=False, action="store_true", help="output all log messages")
args = argParser.parse_args()

log_level = logging.DEBUG if args.verbose else logging.INFO
log_format = '[%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s'
logging.basicConfig(level=log_level, format=log_format,
                    handlers=[logging.FileHandler(os.path.join(args.output, 'plot.log')),
                              logging.StreamHandler(sys.stdout)])

start = datetime.now()
logging.info("Start time: " + start.strftime("%d/%m/%Y-%H:%M:%S"))

if not os.path.isdir(args.output):
    logging.error("Provided output directory (" + args.outputs + ") does not exist.")
    exit(20)

if not os.path.isdir(args.results):
    logging.error("Provided results directory (" + args.results + ") does not exist.")
    exit(30)


def tikzplotlib_fix_ncols(obj):
    """
    workaround for matplotlib 3.6 renamed legend's _ncol to _ncols, which breaks tikzplotlib
    """
    if hasattr(obj, "_ncols"):
        # noinspection PyProtectedMember
        obj._ncol = obj._ncols
    for child in obj.get_children():
        tikzplotlib_fix_ncols(child)


def get_html_coverage(file):
    logging.debug("Reading coverage from " + file)

    with open(file) as html:
        soup = BeautifulSoup(html, 'html.parser')

    footer_data = soup.find('tfoot').find('tr').findChildren('td')
    coverage_percentage = footer_data[2].find(string=True)
    coverage = float(coverage_percentage[:-1])

    logging.debug("Coverage from " + file + " is " + str(coverage))
    return coverage


def get_filtered_coverage(file):
    logging.debug("Reading coverage from " + file)
    covered = missed = 0
    tree = ElementTree.parse(file)

    root = tree.getroot()
    bundle_id = root.get("name").replace(".", "/").removesuffix("/debug").removesuffix("/osmdroid")
    bundle_list = [bundle_id]

    if bundle_id == "com/punksta/apps/volumecontrol":
        bundle_list = ['com/punksta/apps', 'com/example/punksta/volumecontrol']
    elif bundle_id == "com/asdoi/timetable":
        bundle_list = ['com/ulan/timetable']

    for package in tree.findall("package"):
        package_name = package.get("name")

        if all(not package_name.startswith(bundle) for bundle in bundle_list):
            continue

        for clazz in package.findall("class"):
            for counter in clazz.findall("counter"):
                if counter.get("type") == "INSTRUCTION":
                    covered = covered + int(counter.get("covered"))
                    missed = missed + int(counter.get("missed"))

    if covered == 0 and missed == 0:
        logging.error("Problem filtering coverage in XML file (" + file + ")")
        return 0

    coverage = (covered / (covered + missed)) * 100
    logging.debug("Coverage from " + file + " is " + str(coverage))
    return coverage


def get_execution_runtime(file):
    logging.debug("Reading execution runtime from " + file)
    runtime = 0

    with open(file) as log:
        for line in log:
            match = re.search(r"\[INFO] \(.+\) - Execution time: (\d+:\d+:\d+)\.", line)
            if match is None:
                continue

            formatted_runtime = match.group(1)
            time_values = formatted_runtime.split(":")
            runtime = (int(time_values[0]) * 60 * 60) + (int(time_values[1]) * 60) + int(time_values[2])

    logging.debug("Runtime from " + file + " is " + str(runtime))
    return runtime


def get_coverage_stats(base, filtered=False):
    values = []

    if "traversal" in base or "padraig" in base:
        logging.debug("Looking for results in " + base)

        if filtered:
            xml_file = os.path.join(base, "report_1", "acvtool-report.xml")
            if os.path.isfile(xml_file):
                coverage = get_filtered_coverage(xml_file)
                values.append(coverage)
        else:
            html_file = os.path.join(base, "report_1", "index.html")
            if os.path.isfile(html_file):
                coverage = get_html_coverage(html_file)
                values.append(coverage)
    else:
        logging.debug("Looking for results in sub-directories of " + base)
        for directory in sorted(os.listdir(base)):
            if not directory.startswith("test_"):
                continue

            test_directory = os.path.join(base, directory)
            logging.debug("Looking for results in " + test_directory)
            test_number = directory.replace("test_", "").strip()

            if filtered:
                xml_file = os.path.join(test_directory, "report_" + test_number, "acvtool-report.xml")
                if os.path.isfile(xml_file):
                    coverage = get_filtered_coverage(xml_file)
                    values.append(coverage)
            else:
                html_file = os.path.join(test_directory, "report_" + test_number, "index.html")
                if os.path.isfile(html_file):
                    coverage = get_html_coverage(html_file)
                    values.append(coverage)

    if len(values) == 0:
        logging.error("No coverage data found in " + base)
        return [0, 0, 0]

    if any(task in base for task in ["traversal", "padraig"]) and len(values) != 1:
        logging.warning("Number of coverage values is not 1 for " + base)

    if all(task not in base for task in ["traversal", "padraig"]) and len(values) < 10:
        logging.warning("Average does not include 10 coverage values for " + base)

    average = mean(values)
    logging.debug("Average test coverage is " + str(average) + " in " + base)
    minimum = min(values)
    logging.debug("Minimum test coverage is " + str(minimum) + " in " + base)
    maximum = max(values)
    logging.debug("Maximum test coverage is " + str(maximum) + " in " + base)

    return [average, minimum, maximum]


def get_runtime_stats(base):
    values = []

    if "traversal" in base or "model" in base or "padraig" in base:
        logging.debug("Looking for results in " + base)
        log_file = os.path.join(base, "cmd.log")
        if os.path.isfile(log_file):
            runtime = get_execution_runtime(log_file)
            values.append(runtime)
    else:
        logging.debug("Looking for results in sub-directories of " + base)
        for directory in sorted(os.listdir(base)):
            if not directory.startswith("test_"):
                continue

            test_directory = os.path.join(base, directory)
            logging.debug("Looking for results in " + test_directory)
            test_number = directory.replace("test_", "").strip()

            log_file = os.path.join(test_directory, "cmd_" + test_number + ".log")
            if os.path.isfile(log_file):
                runtime = get_execution_runtime(log_file)
                values.append(runtime)

    if len(values) == 0:
        logging.error("No runtime data found in " + base)
        return [0, 0, 0]

    if any(task in base for task in ["traversal", "model", "padraig"]) and len(values) != 1:
        logging.warning("Number of runtime values is not 1 for " + base)

    if all(task not in base for task in ["traversal", "model", "padraig"]) and len(values) < 10:
        logging.warning("Average does not include 10 runtime values for " + base)

    average = mean(values)
    logging.debug("Average test coverage is " + str(average) + " in " + base)
    minimum = min(values)
    logging.debug("Minimum test coverage is " + str(minimum) + " in " + base)
    maximum = max(values)
    logging.debug("Maximum test coverage is " + str(maximum) + " in " + base)

    return [average, minimum, maximum]


def plot_coverage_comparison(base_directory, filtered=False):
    x_keys = []
    table_lines = []

    approaches = ['padraig', 'monkey', 'monkey-click', 's-smog', 'stoat']
    hatches = ['/', None, '\\', '-', 'x', '.', '*', '+', '|', 'o', 'O']
    colors = ['orange', 'cyan', 'green', 'red', 'purple', 'brown', 'pink', 'blue']
    results = {}

    figure, axis = mpl.subplots(figsize=(20, 20))
    figure.subplots_adjust(bottom=0.25)

    logging.debug("Searching sub-directories of " + base_directory)
    for app in sorted(os.listdir(base_directory)):
        app_directory = os.path.join(base_directory, app)
        if not os.path.isdir(app_directory):
            continue

        table_line = app[:app.rfind('_')].replace('_', ' ').title()
        x_keys.append(table_line)
        logging.debug("Searching app directory " + app_directory)

        for approach in approaches:
            stats = [0, 0, 0]

            approach_directory = os.path.join(app_directory, approach)
            if os.path.isdir(approach_directory):
                logging.debug("Searching approach directory " + approach_directory)
                stats = get_coverage_stats(approach_directory, filtered=filtered)

            table_line = "{} & {}".format(table_line, round(stats[0], 2)) if approach == "padraig" else \
                ("{} & {} & {} & {}".format(table_line, round(stats[0], 2), round(stats[1], 2), round(stats[2], 2)))

            results.setdefault(approach + '_avg', []).append(stats[0])
            results.setdefault(approach + '_min', []).append(stats[1])
            results.setdefault(approach + '_max', []).append(stats[2])

        table_line = table_line + " \\\\"
        table_lines.append(table_line)

    if len(table_lines) == 0 and len(results) == 0:
        logging.warning("No data available to plot.")
        return

    base_file_name = "padraig_line_table.txt"
    file_name = "filtered_" + base_file_name if filtered else base_file_name
    output_file = os.path.join(args.output, file_name)
    with open(output_file, 'w') as table_file:
        for line in table_lines:
            line_values = line.replace(" \\\\", "").split(" & ")
            line_app = line_values.pop(0)
            line_values = [float(i) for i in line_values]
            max_value = max(line_values)

            formatted_line = line_app
            for value in line_values:
                if value == max_value:
                    formatted_line = formatted_line + " & \\textbf{" + str(value) + "}"
                else:
                    formatted_line = formatted_line + " & " + str(value)
            formatted_line = formatted_line + " \\\\"
            table_file.write("%s\n" % formatted_line)

    x_indexes = np.arange(len(x_keys))
    bar_width = 1 / len(approaches)

    max_values = []
    for index, approach in enumerate(approaches):
        # yerr = [np.subtract(results[approach + '_avg'], results[approach + '_min']),
        #         np.subtract(results[approach + '_max'], results[approach + '_avg'])]
        axis.bar(x_indexes + (bar_width * index), results[approach + '_avg'], width=bar_width, color=colors[index],
                 label=approach.title(), hatch=hatches[index])  # , yerr=yerr, capsize=3)
        max_values.append(max(results[approach + '_max']))

    axis.set_title("Automated Input Generation Tools Line Coverage")
    y_max_value = max(max_values) + 5
    mpl.yticks(np.arange(0, y_max_value, step=10), np.arange(0, y_max_value, step=10))
    axis.set_ylabel("Coverage (%)")
    axis.set_xticks(x_indexes + (bar_width * 2), x_keys, rotation=90)
    axis.set_xlabel("AUT")
    mpl.legend(loc='upper right')

    base_file_name = "padraig_line_bar_plot"
    file_name = "filtered_" + base_file_name if filtered else base_file_name
    output_file = os.path.join(args.output, file_name)
    mpl.savefig(output_file + '.png')
    tikzplotlib_fix_ncols(figure)
    tikzplotlib.save(output_file + '.tex')
    mpl.close('all')

    increase_values = []
    for index, app in enumerate(sorted(os.listdir(base_directory))):
        app_directory = os.path.join(base_directory, app)
        if not os.path.isdir(app_directory):
            continue

        padraig = results['padraig_avg'][index - 1]
        for approach in approaches:
            if approach == 'padraig':
                continue

            approach_value = results[approach + '_avg'][index - 1]
            increase_values.append(padraig - approach_value)

    logging.info("Average increase: " + str(mean(increase_values)))


def table_runtime_comparison(base_directory):
    table_lines = []
    approaches = ['padraig', 's-smog', 'stoat']  # 'monkey', 'monkey-click'
    axis_data = {}

    logging.debug("Searching sub-directories of " + base_directory)
    for app in sorted(os.listdir(base_directory)):
        app_directory = os.path.join(base_directory, app)
        if not os.path.isdir(app_directory):
            continue

        logging.debug("Searching directory " + app_directory)
        table_line = app[:app.rfind('_')].replace('_', ' ').title()

        for approach in approaches:
            runtime_stats = [0, 0, 0]

            approach_directory = os.path.join(app_directory, approach)
            if os.path.isdir(approach_directory):
                logging.debug("Searching approach directory " + approach_directory)
                runtime_stats = get_runtime_stats(approach_directory)

                if approach == "padraig":
                    traversal_directory = os.path.join(app_directory, "traversal")
                    if os.path.isdir(traversal_directory):
                        logging.debug("Searching traversal directory " + traversal_directory)
                        stats = get_runtime_stats(traversal_directory)
                        runtime_stats = [runtime_stats[i] + stats[i] for i in range(len(runtime_stats))]
                    model_directory = os.path.join(app_directory, "model")
                    if os.path.isdir(model_directory):
                        logging.debug("Searching model directory " + model_directory)
                        stats = get_runtime_stats(model_directory)
                        runtime_stats = [runtime_stats[i] + stats[i] for i in range(len(runtime_stats))]

            if approach == "padraig":
                table_line = table_line + " & " + str(round(runtime_stats[0], 2))
            else:
                table_line = (table_line + " & " + str(round(runtime_stats[0], 2)) + " & " + str(
                    round(runtime_stats[1], 2)) + " & " + str(round(runtime_stats[2], 2)))

            axis_data.setdefault(approach + '_y', []).append(runtime_stats[0])

        table_line = table_line + " \\\\"
        table_lines.append(table_line)

    if len(table_lines) == 0 and len(axis_data) == 0:
        logging.warning("No data available to plot.")
        return

    output_file = os.path.join(args.output, "padraig_runtime_table.txt")
    with open(output_file, 'w') as table_file:
        for table_line in table_lines:
            line_values = table_line.replace(" \\\\", "").split(" & ")
            line_app = line_values.pop(0)
            line_values = [float(i) for i in line_values]
            min_value = min(line_values)

            formatted_line = line_app
            for value in line_values:
                if value == min_value:
                    formatted_line = "{} & \\textbf{{{:,}}}".format(formatted_line, value)
                else:
                    formatted_line = "{} & {:,}".format(formatted_line, value)
            formatted_line = formatted_line + " \\\\"
            table_file.write("%s\n" % formatted_line)

    decrease_values = []
    for index, app in enumerate(sorted(os.listdir(base_directory))):
        app_directory = os.path.join(base_directory, app)
        if not os.path.isdir(app_directory):
            continue

        padraig = axis_data['padraig_y'][index - 1]
        for approach in approaches:
            if approach == 'padraig' or approach == 'monkey' or approach == 'monkey-click':
                continue

            approach_value = axis_data[approach + '_y'][index - 1]
            decrease_values.append(approach_value - padraig)

    logging.info("Average decrease: " + str(mean(decrease_values)))


def plot_runtime_comparison(base_directory):
    app_names = []

    approaches = ['padraig', 'monkey', 'monkey-click', 's-smog', 'stoat']
    colors = ['orange', 'cyan', 'green', 'red', 'purple', 'brown', 'pink', 'blue']
    axis_data = {}

    figure, axis = mpl.subplots(figsize=(20, 20))
    figure.subplots_adjust(bottom=0.25)

    logging.debug("Searching sub-directories of " + base_directory)
    for app in sorted(os.listdir(base_directory)):
        app_directory = os.path.join(base_directory, app)
        if not os.path.isdir(app_directory):
            continue

        logging.debug("Searching directory " + app_directory)

        app_name = app[:app.rfind('_')].replace('_', ' ').title()
        app_names.append(app_name)

        for approach in approaches:
            coverage_stats = [0, 0, 0]
            runtime_stats = [0, 0, 0]

            approach_directory = os.path.join(app_directory, approach)
            if os.path.isdir(approach_directory):
                logging.debug("Searching approach directory " + approach_directory)
                coverage_stats = get_coverage_stats(approach_directory, filtered=True)
                runtime_stats = get_runtime_stats(approach_directory)

                if approach == "padraig":
                    traversal_directory = os.path.join(app_directory, "traversal")
                    if os.path.isdir(traversal_directory):
                        logging.debug("Searching traversal directory " + traversal_directory)
                        stats = get_runtime_stats(traversal_directory)
                        runtime_stats = [runtime_stats[i] + stats[i] for i in range(len(runtime_stats))]
                    model_directory = os.path.join(app_directory, "model")
                    if os.path.isdir(model_directory):
                        logging.debug("Searching model directory " + model_directory)
                        stats = get_runtime_stats(model_directory)
                        runtime_stats = [runtime_stats[i] + stats[i] for i in range(len(runtime_stats))]

            axis_data.setdefault(approach + '_y', []).append(runtime_stats[0])
            axis_data.setdefault(approach + '_x', []).append(coverage_stats[0])

    if len(axis_data) == 0:
        logging.warning("No data available to plot.")
        return

    for index, approach in enumerate(approaches):
        axis.plot(axis_data[approach + '_x'], axis_data[approach + '_y'], 'o', color=colors[index],
                  label=approach.title())

    axis.set_title("Automated Input Generation Tool Runtime")
    mpl.yticks(np.arange(0, 13000, step=500), np.arange(0, 13000, step=500))
    axis.set_ylabel("Runtime (s)")
    mpl.xticks(np.arange(0, 45, step=10), np.arange(0, 45, step=10))
    axis.set_xlabel("Coverage (%)")
    mpl.legend(loc='upper right')

    output_file = os.path.join(args.output, "padraig_runtime_plot")
    mpl.savefig(output_file + '.png')
    tikzplotlib_fix_ncols(figure)
    tikzplotlib.save(output_file + '.tex')
    mpl.close('all')


def summerize_coverage(base_directory):
    csv_lines = ['App,Approach,Coverage']
    approaches = ['padraig', 'monkey', 'monkey-click', 's-smog', 'stoat']

    logging.debug("Searching sub-directories of " + base_directory)
    for app in sorted(os.listdir(base_directory)):
        app_directory = os.path.join(base_directory, app)
        if not os.path.isdir(app_directory):
            continue

        app_name = app[:app.rfind('_')].replace('_', ' ').title()

        logging.debug("Searching directory " + app_directory)
        for approach in approaches:
            approach_directory = os.path.join(app_directory, approach)
            if os.path.isdir(approach_directory):
                logging.debug("Searching approach directory " + approach_directory)

                if "padraig" in approach_directory:
                    xml_file = os.path.join(approach_directory, "report_1", "acvtool-report.xml")
                    if os.path.isfile(xml_file):
                        coverage = get_filtered_coverage(xml_file)
                        csv_lines.append(app_name + "," + approach + "," + str(coverage))
                else:
                    logging.debug("Looking for results in sub-directories of " + approach_directory)
                    coverage = 0
                    count = 0

                    for directory in sorted(os.listdir(approach_directory)):
                        if not directory.startswith("test_"):
                            continue

                        test_directory = os.path.join(approach_directory, directory)
                        logging.debug("Looking for results in " + test_directory)
                        test_number = int(directory.replace("test_", "").strip())

                        xml_file = os.path.join(test_directory, "report_" + str(test_number), "acvtool-report.xml")
                        if os.path.isfile(xml_file):
                            coverage = get_filtered_coverage(xml_file)
                            csv_lines.append(app_name + "," + approach + "," + str(coverage))
                            count = count + 1

                    if count != 10:
                        for i in range(count, 10):
                            csv_lines.append(app_name + "," + approach + "," + str(coverage))

    if len(csv_lines) == 0:
        logging.warning("No data available to plot.")
        return

    output_file = os.path.join(args.output, "coverage_summary.csv")
    with open(output_file, 'w') as fp:
        for item in csv_lines:
            fp.write("%s\n" % item)


def execute_mann_whitney_u_test():
    coverage_df = pandas.read_csv("output/coverage_summary.csv")
    comparison_df = pandas.DataFrame(columns=["App", "Approach", "Coverage"])

    for app in coverage_df.App.unique():
        app_df = coverage_df[coverage_df["App"] == app]
        padraig_results = app_df[app_df["Approach"] == "padraig"]["Coverage"]
        for approach in ["monkey", "monkey-click", "s-smog", "stoat"]:
            approach_results = app_df[app_df["Approach"] == approach]["Coverage"]
            mannwhitney_method = scipy.stats.mannwhitneyu(approach_results, padraig_results.to_list() * 10)
            if mannwhitney_method.pvalue > 0.05:
                comparison_method = "SAME MANNW"
            else:
                a12_method, _ = VD_A(padraig_results.to_list() * 10, approach_results.to_list())
                if 0.5 < a12_method < 0.556:
                    comparison_method = "BETTER NEGLIGIBLE"
                elif 0.556 <= a12_method < 0.638:
                    comparison_method = "BETTER SMALL"
                elif 0.638 <= a12_method < 0.714:
                    comparison_method = "BETTER MEDIUM"
                elif 0.714 <= a12_method:
                    comparison_method = "BETTER LARGE"
                elif 0.444 < a12_method < 0.5:
                    comparison_method = "WORSE NEGLIGIBLE"
                elif 0.362 < a12_method <= 0.444:
                    comparison_method = "WORSE SMALL"
                elif 0.286 < a12_method <= 0.362:
                    comparison_method = "WORSE MEDIUM"
                elif a12_method <= 0.286:
                    comparison_method = "WORSE LARGE"
                else:
                    comparison_method = "SAME A12"
            comparison_df.loc[len(comparison_df.index)] = [app, approach, comparison_method]
    comparison_df.to_csv(os.path.join(args.output, "comparison_results.csv"))


def create_statistical_analysis_tex_table():
    table_lines = []
    u_test_df = pandas.read_csv("output/comparison_results.csv", header=[0], index_col=[0])

    for app in u_test_df.App.unique():
        app_df = u_test_df[u_test_df["App"] == app]

        monkey = app_df.loc[app_df.Approach == 'monkey', 'Coverage'].values[0]
        monkey_click = app_df.loc[app_df.Approach == 'monkey-click', 'Coverage'].values[0]
        smog = app_df.loc[app_df.Approach == 's-smog', 'Coverage'].values[0]
        stoat = app_df.loc[app_df.Approach == 'stoat', 'Coverage'].values[0]

        line = app + " & " + monkey + " & " + monkey_click + " & " + smog + " & " + stoat + " \\\\"
        table_lines.append(line)

    if len(table_lines) == 0:
        logging.warning("No table data available.")
        return

    for i, line in enumerate(table_lines):
        line = line.replace("BETTER LARGE", "\\betterLarge")
        line = line.replace("SAME MANNW", "\\same")
        line = line.replace("WORSE LARGE", "\\worseLarge")
        table_lines[i] = line

    output_file = os.path.join(args.output, "u_test_table.txt")
    with open(output_file, 'w') as fp:
        for item in table_lines:
            fp.write("%s\n" % item)


logging.info("Plotting coverage data for app comparison.")
plot_coverage_comparison(args.results)
logging.info("Plotting filtered coverage data for app comparison.")
plot_coverage_comparison(args.results, filtered=True)
logging.info("Tabling runtime data for app comparison.")
table_runtime_comparison(args.results)
logging.info("Creating coverage summary CSV file.")
summerize_coverage(args.results)
logging.info("Running Mann-Whitney U Test")
execute_mann_whitney_u_test()
logging.info("Creating statistical analysis table.")
create_statistical_analysis_tex_table()

end = datetime.now()
logging.info("End time: " + end.strftime("%d/%m/%Y-%H:%M:%S"))
duration = end - start
logging.info("Execution time: " + str(round(duration.total_seconds())) + " second(s)")
