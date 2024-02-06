#
# Author Jordan Doyle.
#
# usage: app_selector.py [-h] [-o OUTPUT] [-d] [-s] [-f] [-a AGE] [-i MIN] [-x MAX] [-c] [-p] [-v] [-g]
#
# options:
#   -h, --help                          show this help message and exit
#   -o OUTPUT, --output OUTPUT          output directory
#   -d, --download                      download APK files
#   -s, --source                        download source archive
#   -f, --format                        format index file
#   -a AGE, --age AGE                   maximum app age
#   -i MIN, --min MIN                   minimum app SDK version
#   -x MAX, --max MAX                   maximum app SDK version
#   -c, --category                      output categories
#   -p, --package                       output packages
#   -v, --verbose                       output all log messages
#   -g, --category-packages             output category packages
#

import argparse
import json
import logging
import os
import random
import shutil
import sys
from datetime import datetime
from urllib.error import HTTPError

import wget

argParser = argparse.ArgumentParser()
argParser.add_argument("-o", "--output", type=str, default='output', help="output directory")
argParser.add_argument("-d", "--download", default=False, action="store_true", help="download APK files")
argParser.add_argument("-s", "--source", default=False, action="store_true", help="download source archive")
argParser.add_argument("-f", "--format", default=False, action="store_true", help="format index file")
argParser.add_argument("-a", "--age", type=int, default=10, help="maximum app age")
argParser.add_argument("-i", "--min", type=int, default=16, help="minimum app SDK version")
argParser.add_argument("-x", "--max", type=int, default=29, help="maximum app SDK version")
argParser.add_argument("-c", "--category", default=False, action="store_true", help="output categories")
argParser.add_argument("-p", "--package", default=False, action="store_true", help="output packages")
argParser.add_argument("-v", "--verbose", default=False, action="store_true", help="output all log messages")
argParser.add_argument("-g", "--category-packages", default=False, action="store_true", help="output category packages")
args = argParser.parse_args()

log_level = logging.DEBUG if args.verbose else logging.INFO
log_format = '[%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s'
logging.basicConfig(level=log_level, format=log_format,
                    handlers=[logging.FileHandler(os.path.join(args.output, 'selection.log')),
                              logging.StreamHandler(sys.stdout)])

start = datetime.now()
logging.info("Start time: " + start.strftime("%d/%m/%Y-%H:%M:%S"))

if not os.path.isdir(args.output):
    logging.error("Provided output directory (" + args.output + ") does not exist.")
    exit(20)

APP_INDEX_FILE = 'index.json'
if not os.path.isfile(APP_INDEX_FILE):
    logging.info("Downloading " + APP_INDEX_FILE + ".")
    try:
        wget.download('https://f-droid.org/repo/index-v2.json', APP_INDEX_FILE)
        logging.info("Download successful.")
    except HTTPError as e:
        logging.error("Error downloading app index file." + str(e))
        exit(30)

# Providing seed values so that the same random selection can be made in each execution. However, if the index file is
# changed by F-Droid then the random selection will change regardless of the seed values given.
SEED_VALUES = [29, 147, 5, 86, 24, 61, 55, 44, 88, 32, 27, 1, 121, 14, 31, 17]

# Many gaming apps use frameworks such as unity which cannot be analysed by FlowDroid.
FILTERED_CATEGORIES = {"Games"}

# Some apps are filtered manually due to problems when working with them. The dictionary below maps filtered packages to
# the reason why they have been filtered.
FILTERED_APPS = {"com.androidfromfrankfurt.workingtimealert": "App will not install on the Android emulator.",
                 "click.dummer.yidkey": "Keyboard app not suitable for interface tests, no isolation.",
                 "org.retroshare.android.qml_app": "App will not install on the Android emulator.",
                 "pl.net.szafraniec.NFCTagmaker": "App launch fails on the Android emulator.",
                 "com.diblui.fullcolemak": "App would not install on the Android emulator.",
                 "de.cketti.dashclock.k9": "Not a standard app, appears to be an extension of some sort.",
                 "se.manyver": "App would not install on the Android emulator.",
                 "de.devmil.muzei.bingimageofthedayartsource": "Extension app not suitable for interface tests.",
                 "info.tangential.cone": "App would not install on the Android emulator.",
                 "org.weilbach.splitbills": "App can't be instrumented. Code is obfuscated.",
                 "io.lbry.browser": "App would not install on the Android emulator.",
                 "org.bitbucket.watashi564.combapp": "App can't be instrumented. Code is obfuscated.",
                 "org.dash.electrum.electrum_dash": "App would not install on the Android emulator.",
                 "com.mmazzarolo.breathly": "App can't be instrumented. Code is obfuscated."}


def write_json_file(file_name, data):
    logging.info("Writing JSON data in '" + os.path.basename(file_name) + "'.")

    if not os.path.isfile(file_name):
        os.makedirs(os.path.dirname(file_name), exist_ok=True)

    with open(file_name, 'w') as json_file:
        json_file.write(json.dumps(data, indent=4))


def get_latest_version(last_updated, versions):
    latest_version = None
    for package_version in versions.values():
        if package_version["added"] == last_updated:
            latest_version = package_version
            break
        elif latest_version is None or latest_version["added"] < package_version["added"]:
            latest_version = package_version

    return latest_version


def get_package_dictionary(package, metadata, version):
    return {"name": metadata["name"]["en-US"], "targetSdkVersion": version["manifest"]["usesSdk"]["targetSdkVersion"],
            "minSdkVersion": version["manifest"]["usesSdk"]["minSdkVersion"], "package": package,
            "source": package_data["repo"]["address"] + version["src"]["name"], "categories": metadata["categories"],
            "url": package_data["repo"]["address"] + version["file"]["name"], "lastUpdated": metadata["lastUpdated"],
            "versionCode": version["manifest"]["versionCode"]}


def filtered(package, metadata, version):
    global manual, category, age, sdk, source

    if package in FILTERED_APPS.keys():
        manual += 1
        logging.debug("Filtering '" + package + "': " + FILTERED_APPS.get(package))
        return True

    if not set(metadata["categories"]).isdisjoint(FILTERED_CATEGORIES):
        category += 1
        logging.debug("Filtering '" + package + "': App category does not meet requirements.")
        return True

    last_updated = datetime.fromtimestamp(metadata["lastUpdated"] / 1000.0)
    number_of_years = (datetime.now() - last_updated).days / 365
    if number_of_years > args.max:
        age += 1
        logging.debug("Filtering '" + package + "': App is not maintained, too old.")
        return True

    if "src" not in version:
        source += 1
        logging.debug("Filtering '" + package + "': App does not provide source code.")
        return True

    if "usesSdk" in version["manifest"]:
        if not args.min <= version["manifest"]["usesSdk"]["minSdkVersion"] <= args.max or not args.min <= \
                                                                                              version["manifest"][
                                                                                                  "usesSdk"][
                                                                                                  "targetSdkVersion"] <= args.max:
            sdk += 1
            logging.debug("Filtering '" + package + "': App SDK is less than the minimum " + str(
                args.min) + " or greater than the maximum " + str(args.max) + ".")
            return True
    else:
        sdk += 1
        logging.debug("Filtering '" + package + "': App does not declare SDK version.")
        return True

    return False


def list_filtered_packages():
    packages = {}

    for package_name, package_details in package_data["packages"].items():
        package_metadata = package_details["metadata"]
        package_version = get_latest_version(package_metadata["lastUpdated"], package_details["versions"])

        if not filtered(package_name, package_details["metadata"], package_version):
            packages[package_name] = get_package_dictionary(package_name, package_metadata, package_version)

    return packages


def list_category_packages(category):
    packages = {}

    for package_name, package_details in filtered_packages.items():
        if category in package_details["categories"]:
            packages[package_name] = package_details

    return packages


def download_apk_file(package_details):
    name = package_details["name"].lower().replace(' ', '_')
    version = str(package_details["versionCode"])
    file = os.path.join(args.output, 'apk', name + '_' + version + '.apk')

    if not os.path.isfile(file):
        os.makedirs(os.path.dirname(file), exist_ok=True)
        logging.info("Downloading " + package_details["name"].title() + " APK.")

        try:
            wget.download(package_details["url"], file)
            logging.info("Download successful.")
        except HTTPError as error:
            logging.error("Error downloading APK file from " + package_details["url"] + ". " + str(error))
    else:
        logging.info(package_details["name"].title() + " APK already downloaded.")


def download_source_archive(package_details):
    name = package_details["name"].lower().replace(' ', '_')
    version = str(package_details["versionCode"])
    file = os.path.join(args.output, 'archive', name + '_' + version + '.tar.gz')
    directory = os.path.join(args.output, 'source', name + '_' + version)

    if not os.path.isfile(file):
        os.makedirs(os.path.dirname(file), exist_ok=True)
        logging.info("Downloading " + package_details["name"].title() + " source.")

        try:
            wget.download(package_details["source"], file)
            logging.info("Download successful.")
        except HTTPError as error:
            logging.error("Error downloading source archive from " + package_details["source"] + ". " + str(error))
    else:
        logging.info(package_details["name"].title() + " source already downloaded.")

    if os.path.isfile(file):
        if not os.path.isdir(directory):
            logging.info("Extracting " + package_details["name"].title() + " source.")

            source_directory = os.path.join(args.output, 'source')
            shutil.unpack_archive(file, source_directory, "gztar")
            logging.info("Extracting successful.")

            archive_name = package_details["source"].split('/')[-1]
            logging.info("Renaming extracted directory '" + archive_name + "'.")
            archive_directory = os.path.join(source_directory, archive_name)
            if os.path.isdir(archive_directory):
                shutil.move(archive_directory, directory)
                logging.info("Rename successful.")
            else:
                logging.error("Rename failed, could not find directory " + archive_directory + ".")
        else:
            logging.info(package_details["name"].title() + " archive already extracted.")


def get_random_app_per_category():
    random_packages = {}
    selected_packages = []
    seed_index = 0

    for category, packages in category_packages.items():
        if len(packages) == 0:
            logging.error("No packages with category " + category)
            continue

        random_package = random_number = None
        while random_package is None or random_package in selected_packages:
            random.seed(SEED_VALUES[seed_index])
            random_number = random.randint(1, len(packages))
            random_package = list(packages.keys())[random_number - 1]

        package_details = packages[random_package]
        random_packages[category] = package_details
        selected_packages.append(random_package)
        seed_index += 1

        logging.info(
            "Selected '{0}', app {1} from {2} available.".format(package_details["name"].title(), random_number,
                                                                 len(packages)))
        if args.download:
            download_apk_file(package_details)
        if args.source:
            download_source_archive(package_details)

    return random_packages


def get_manually_selected_apps():
    packages = []

    for package, details in filtered_packages.items():
        if package != "com.lako.moclock" and package != "com.punksta.apps.volumecontrol":
            continue

        packages.append(details)
        logging.info("Manually selected '{0}', used in previous publication.".format(details["name"].title()))
        if args.download:
            download_apk_file(details)
        if args.source:
            download_source_archive(details)

    return packages


logging.info("Loading app index from file '" + APP_INDEX_FILE + "'.")
app_index_file = open(APP_INDEX_FILE)
package_data = json.load(app_index_file)
if args.format:
    write_json_file(APP_INDEX_FILE, package_data)
logging.info("Index contains " + str(len(package_data["packages"])) + " packages.")

logging.info("Finding categories in app index.")
categories = list(package_data["repo"]["categories"].keys())
logging.info("Filtering categories that do not meet requirements.")
categories = [category for category in categories if category not in FILTERED_CATEGORIES]
if args.category:
    write_json_file(os.path.join(args.output, 'f_droid_categories.json'), categories)
logging.info("Index contains " + str(len(categories)) + " categories.")

manual = category = age = sdk = source = 0

logging.info("Filtering packages that do not meet requirements.")
filtered_packages = list_filtered_packages()
if args.package:
    write_json_file(os.path.join(args.output, 'f_droid_packages.json'), filtered_packages)
logging.info("Filtered " + str(manual) + " packages manually.")
logging.info("Filtered " + str(category) + " packages with category filter.")
logging.info("Filtered " + str(age) + " packages above max age.")
logging.info("Filtered " + str(source) + " packages with no source code.")
logging.info("Filtered " + str(sdk) + " packages with unsuitable SDK version.")
logging.info(str(len(filtered_packages)) + " packages remain after filtering.")

logging.info("Creating list of packages per category.")
category_packages = {}
for current_category in categories:
    category_packages[current_category] = list_category_packages(current_category)
if args.category_packages:
    write_json_file(os.path.join(args.output, 'f_droid_category_packages.json'), category_packages)

logging.info("Selecting random app per category.")
random_app_per_category = get_random_app_per_category()
write_json_file(os.path.join(args.output, 'f_droid_random_apps.json'), random_app_per_category)

logging.info("Gathering apps from previous publication.")
manually_selected_apps = get_manually_selected_apps()
write_json_file(os.path.join(args.output, 'f_droid_manual_apps.json'), manually_selected_apps)

end = datetime.now()
logging.info("End time: " + end.strftime("%d/%m/%Y-%H:%M:%S"))
duration = end - start
logging.info("Execution time: " + str(round(duration.total_seconds())) + " second(s)")
