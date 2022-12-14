# -*- coding: utf-8 -*-
#eBible - Download projects.ipynb

#Automatically generated by Colaboratory.

#Original file is located at
#    https://colab.research.google.com/drive/1RiwdOiqB3TP5VofMbjFLbo5_hJP03Uds

# Define base folder
base = 'F:/GitHub/davidbaines/eBible'

# Import modules and directory paths

import os
from pathlib import Path
from datetime import date, datetime
from random import randint
import requests
from time import sleep
import shutil
from glob import iglob
from bs4 import BeautifulSoup
from csv import DictReader, DictWriter
import ntpath
import regex

eBible_url = r"https://ebible.org/Scriptures/"
eBible_csv_url = r"https://ebible.org/Scriptures/translations.csv"

corpus = Path(base)
zipped = corpus / "downloads"
unzipped = corpus / "projects"
ebible_projects = corpus / "projects"
metadata = corpus / "metadata"
metadata_csv = metadata / "translations.csv"
copyright_file = metadata / "copyrights.csv"
logs = corpus / "logs"

file_suffix = "_usfm.zip"
csv_headers = [
    "ID",
    "File",
    "Language",
    "Dialect",
    "Licence Type",
    "Licence Version",
    "CC Licence Link",
    "Copyright Holder",
    "Copyright Years",
    "Translation by",
]

print(eBible_url)
print(eBible_csv_url)
print(zipped)
print(unzipped)
print(ebible_projects)
print(metadata_csv)
print(copyright_file)
print(logs)

# Define methods for downloading and unzipping eBibles

def log_and_print(s, type='ínfo'):
    log_file.write(f"{type.upper()}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {s}\n")
    print(s)

def make_directories():
    os.makedirs(zipped, exist_ok=True)
    os.makedirs(unzipped, exist_ok=True)
    os.makedirs(metadata, exist_ok=True)
    os.makedirs(logs, exist_ok=True)


def download_csv_file(url, headers, save_as):

    r = requests.get(url, headers=headers)
    # If the status is OK continue
    if r.status_code == requests.codes.ok:

        with open(save_as, "wb") as out_file:
            # Write out the content of the page.
            out_file.write(r.content)

        return save_as
    return None


def download_zip_file(url, headers, save_as):

    r = requests.get(url, headers=headers)
    # If the status is OK continue
    if r.status_code == requests.codes.ok:

        with open(save_as, "wb") as out_file:
            # Write out the content of the page.
            out_file.write(r.content)

        return save_as
    return None
    
def get_folder(file):
    # Get the path of the folder to which the zip file should be extracted."
    return unzipped / file.name[0: (len(file.name) - len(file_suffix))]


def get_tree_size(path):
    """Return total size of files in given path and subdirs."""
    total = 0
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            total += get_tree_size(entry.path)
        else:
            total += entry.stat(follow_symlinks=False).st_size
    return total
    
    
def unzip_ebibles(source_folder, file_suffix, dest_folder):
    log_and_print(f"Starting unzipping eBible zip files...")
    pattern = "*" + file_suffix
    zip_files = sorted([zip_file for zip_file in source_folder.glob(pattern)])
    log_and_print(f"Found {len(zip_files)} files in {source_folder} matching pattern: {pattern}")

    # Strip off the pattern so that the subfolder name is the project ID.
    extract_folders = [ (zip_file, get_folder(zip_file)) for zip_file in zip_files ]
    extracts = [ (zip_file, folder) for zip_file, folder in extract_folders if not folder.exists() or zip_file.stat().st_size >= get_tree_size(folder) ]
    
    log_and_print(f"Found {len(extracts)} that were not yet extracted or are smaller than the zip file.")
    
    for zip_file, extract in extracts:
        extract.mkdir(parents=True, exist_ok=True)
        log_and_print(f"Extracting to: {extract}")
        shutil.unpack_archive(zip_file, extract)

    log_and_print(f"Finished unzipping eBible files")


def get_filenames(metadata_csv):
    file_infos = []
    countall = count_redist = 0

    with open(metadata_csv, encoding="utf-8-sig", newline="") as csvfile:
        reader = DictReader(csvfile, delimiter=",", quotechar='"')
        for row in reader:
            countall += 1
            if row["Redistributable"] == "True":
                row["Redistributable"] = True

                file_infos.append(row)
                count_redist += 1

            if row["Redistributable"] == "False":
                row["Redistributable"] = False

                file_infos.append(row)

        filenames = [row["translationId"] + file_suffix for row in file_infos]
        log_and_print(f"The translations csv file lists {countall} translations and {count_redist} are redistributable.")

        return filenames

# Download and unzip eBible projects

# Create directories if they don't already exist
make_directories()

log_file = open(logs / f"run_{date.today()}.log", "a")

# Set the user-agent to Chrome for Requests.
headers = {"user-agent": "Chrome/51.0.2704.106"}

# Download the list of translations.
log_and_print(f"Starting downloading eBible files...")
log_and_print(f"Downloading list of translations from {eBible_csv_url} to: {str(metadata_csv)}")
done = download_csv_file(eBible_csv_url, headers, metadata_csv)

if not done:
    log_and_print(f"Couldn't download {eBible_csv_url}")
    exit

# Get filenames
filenames = sorted(get_filenames(metadata_csv))

# Find which files have already been downloaded:
already_downloaded = sorted([file.name for file in zipped.glob("*" + file_suffix)])
log_and_print(f"There are {len(already_downloaded)} files with the suffix {file_suffix} already in {zipped}")

# Those that require downloading are the filenames - already_downloaded.
to_download = sorted(set(filenames) - set(already_downloaded))
log_and_print(f"\nThere are {len(to_download)} files still to download.")

# Download the zipped USFM file if it doesn't already exist.

for i, filename in enumerate(to_download):

    # Construct the download url and the local file path.
    url = eBible_url + filename
    save_as = zipped / filename

    # Skip any missing filenames.
    if filename == "":
        continue

    # Skip existing files that contain data.
    elif save_as.exists() and save_as.stat().st_size > 100:
        log_and_print(f"{i+1}: {save_as} already exists and contains {save_as.stat().st_size} bytes.")
        continue

    else:
        log_and_print(f"{i+1}: Downloading from {url} to {save_as}.")
        done = download_zip_file(url, headers, save_as)

        if done:
            log_and_print(f"Saved {url} as {save_as}\n")
            # Pause for a random number of miliseconds
            pause = randint(1, 5000) / 1000
            sleep(pause)

        else:
            log_and_print(f"Could not download {url}\n")
            
log_and_print(f"Finished downloading eBible files")

unzip_ebibles(zipped, file_suffix, unzipped)

log_file.close()

# Define methods for creating the copyrights file

def log_and_print(s, type='ínfo'):
    log_file.write(f"{type.upper()}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {s}\n")
    print(s)


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def read_list_from_file(f_in):
    lines = list()
    with open(f_in, "r", encoding="utf-8") as infile:
        for line in infile.read().splitlines():
            lines.append(line)
    return lines


def get_copyright_from_url(url):
    r = requests.get(url)
    # If the status is OK continue
    if r.status_code == requests.codes.ok:
        soup = BeautifulSoup(r.content, "lxml")
        cr_item = soup.find("td", colspan="3")
        return cr_item.string
    else:
        return None

# Get copyright info from eBible projects """

log_file = open(logs / f"run_{date.today()}.log", "a")

data = list()
#copr_regex = r".*[/\\](?P<id>.*?)[/\\]copr.htm"

log_and_print("Collecting eBible copyright information...")
for copyright_info_file in sorted(ebible_projects.glob("**/copr.htm")):
    id = str(copyright_info_file.parents[0].relative_to(unzipped))
    #print(id)
    
    #id_match = regex.match(copr_regex, str(copyright_info_file))
    #id = id_match["id"]

    entry = dict()
    entry["ID"] = str(id)
    entry["File"] = copyright_info_file

    with open(copyright_info_file, "r", encoding="utf-8") as copr:
        html = copr.read()
        soup = BeautifulSoup(html, "lxml")

    cclink = soup.find(href=regex.compile("creativecommons"))
    if cclink:
        ref = cclink.get("href")
        if ref:
            entry["CC Licence Link"] = ref
            cc_match = regex.match(
                r".*?/licenses/(?P<type>.*?)/(?P<version>.*)/", ref
            )
            if cc_match:
                entry["Licence Type"] = cc_match["type"]
                entry["Licence Version"] = cc_match["version"]
            else:
                cc_by_match = regex.match(r".*?/licenses/by(?P<version>.*)/", ref)
                if cc_by_match:
                    # print(f'Licence version = {cc_by_match["version"]}')
                    entry["Licence Type"] = "by"
                    entry["Licence Version"] = cc_by_match["version"]

    cclink = None

    titlelink = soup.find(href=regex.compile(f"https://ebible.org/{id}"))
    if titlelink:
        entry["Vernacular Title"] = titlelink.string
    titlelink = None

    copy_strings = [s for s in soup.body.p.stripped_strings]
      
    for i, copy_string in enumerate(copy_strings):
        if i == 0 and "copyright ©" in copy_string:
            entry["Copyright Years"] = copy_string
            entry["Copyright Holder"] = copy_strings[i + 1]
        if i > 0 and "Language:" in copy_string:
            entry["Language"] = copy_strings[i + 1]
        if "Dialect" in copy_string:
            entry["Dialect"] = copy_string
        if "Translation by" in copy_string:
            entry["Translation by"] = copy_string
        if "Public Domain" in copy_string:
            entry["Copyright Year"] = ""
            entry["Copyright Holder"] = "Public Domain"
    
    data.append(entry)

    with open(copyright_file, "w", encoding="utf-8") as csv_out:
        writer = DictWriter(
            csv_out, csv_headers, restval="", extrasaction="ignore", dialect="excel"
        )
        writer.writeheader()
        writer.writerows(data)
    

log_and_print(f"Wrote copyright info to {copyright_file}")
log_file.close()