"""ebible.py contains functions to:
Download zipped Bibles in USFM format from ebible.org to one folder.
Unzip the downloaded files to another folder.
Check the licence data contained in the copr.htm files in the unzipped folders. Write that as a csv file.
Extract files that have a licence that permits redistibution using SILNLP for the extraction.
"""

# Import modules and directory paths
import argparse
from bs4 import BeautifulSoup
from csv import DictReader, DictWriter
from datetime import date, datetime 
from glob import iglob
import ntpath
import os
from pathlib import Path
from random import randint
import regex
import requests
import shutil
from time import sleep, strftime

global headers
headers = {"Accept-Encoding":"gzip, deflate", "Connection":"keep-alive", "Upgrade-Insecure-Requests" : "1", "User-Agent":"Mozilla/5.0"}

# Define methods for downloading and unzipping eBibles

def log_and_print(file, s, type='Info'):

    with open(file, "a") as log:
        log.write(f"{type.upper()}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {s}\n")
    print(s)


def make_directories(dirs_to_create):
    for dir_to_create in dirs_to_create:
        dir_to_create.mkdir(parents=True, exist_ok=True)


def download_file(url, file, headers=headers):

    r = requests.get(url, headers=headers)
    # If the status is OK continue
    if r.status_code == requests.codes.ok:

        with open(file, "wb") as out_file:
            # Write out the content of the page.
            out_file.write(r.content)

        return file
    return None
    
def get_tree_size(path):
    """Return total size of files in given path and subdirs."""
    total = 0
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            total += get_tree_size(entry.path)
        else:
            total += entry.stat(follow_symlinks=False).st_size
    return total
    

def unzip_ebible(source_file, dest_folder):
    
    if dest_folder.is_dir():
        log_and_print(logfile, f"Extracting {source_file} to: {dest_folder}") 
        shutil.unpack_archive(source_file, dest_folder)
        #log_and_print(f"Extracted {source_file} to: {dest_folder}") 
    
    else: 
        log_and_print(logfile, f"Can't extract, {dest_folder} doesn't exist.") 

       
def unzip_ebibles(source_folder, file_suffix, unzip_folder, logfile):
    log_and_print(logfile, f"Starting unzipping eBible zip files...")
    pattern = "*" + file_suffix
    zip_files = sorted([zip_file for zip_file in source_folder.glob(pattern)])
    log_and_print(logfile, f"Found {len(zip_files)} files in {source_folder} matching pattern: {pattern}")

    # Strip off the pattern so that the subfolder name is the project ID.
    extract_folders = [ (zip_file, unzip_folder / f"{zip_file.name[0:3]}-{zip_file.name[0: (len(zip_file.name) - len(file_suffix))]}" ) for zip_file in zip_files ]
    extracts = [ (zip_file, folder) for zip_file, folder in extract_folders if not folder.exists() or zip_file.stat().st_size >= get_tree_size(folder) ]

    log_and_print(logfile, f"Found {len(extracts)} that were not yet extracted or are smaller than the zip file.")
    
    for zip_file, extract in extracts:
        extract.mkdir(parents=True, exist_ok=True)
        log_and_print(logfile, f"Extracting to: {extract}")
        shutil.unpack_archive(zip_file, extract)

    log_and_print(logfile, f"Finished unzipping eBible files")


def get_redistributable(translations_csv):
    
    redistributable_files = []
    all_files = []

    with open(translations_csv, encoding="utf-8-sig", newline="") as csvfile:
        reader = DictReader(csvfile, delimiter=",", quotechar='"')
        for row in reader:
            all_files.append(row["translationId"])

            if row["Redistributable"] == "True":
                redistributable_files.append(row["translationId"])

        return all_files, redistributable_files

# Define methods for creating the copyrights file

def norm_name(name):
    if len(name) < 3:
        return None
    elif len(name) == 3: 
        return f"{name[:3]}-{name}"
    elif len(name) >= 7  and name[3] == '-' and name[0:3] == name[4:7]:
        return name
    else :
        return f"{name[:3]}-{name}"

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

def main():
    parser = argparse.ArgumentParser(description="Download, unzip and extract text corpora from eBible.")
    parser.add_argument("--base-folder", default=Path.home() / "eBible", help="The base folder where others will be created.")
    args = parser.parse_args()

    # Define base folder
    base = Path(args.base_folder)
    corpus = base / "corpus"
    unzipped = base / "unzipped"
    zipped = base / "zipped"
    projects = unzipped
    metadata = base / "metadata"
    logs = base / "logs"

    year, month, day, hour, minute = map(int, strftime("%Y %m %d %H %M").split())
    log_filename = f"run_{year}_{month}_{day}-{hour}_{minute}.log"
    logfile = logs / log_filename

    licence_file = metadata / "licences.csv"

    all_folders = [corpus, unzipped, zipped, metadata, logs]
    missing_folders = [folder for folder in all_folders if not folder.is_dir()]
    
    print(f"\nThe base folder is : {base}\n")
    # base = r"F:/GitHub/davidbaines/eBible"
    
    print("The following folders are required:")
    for folder in all_folders:
        print(folder)
    print()

    if missing_folders:
        print("The following folders are required and will be created if you continue.")
        for folder in missing_folders:
            print(folder)

        choice = ''        
        while choice not in ['y','n']:
            choice = input("Would you like to continue? y /n ").lower()
        if choice == 'y':
            # Create the required directories
            make_directories(missing_folders)
        elif choice == 'n':
            exit(0)

    translations_csv = metadata / "translations.csv"
    
    eBible_url = r"https://ebible.org/Scriptures/"
    translations_csv_url = r"https://ebible.org/Scriptures/translations.csv"


    csv_headers = [
        "ID",
        "Language",
        "Dialect",
        "Licence Type",
        "Licence Version",
        "CC Licence Link",
        "Copyright Holder",
        "Copyright Years",
        "Translation by",
    ]

    # Download the list of translations.
    log_and_print(logfile, f"Downloading list of translations from {translations_csv_url} to: {str(translations_csv)}")
    done = download_file(translations_csv_url, translations_csv)
    
    if not done:
        log_and_print(logfile, f"Couldn't download {translations_csv_url}")
        exit(1)

    file_suffix = "_usfm.zip"

    # Get filenames
    all_files, redistributable_files = get_redistributable(translations_csv)
    restricted_files = set(all_files) - set(redistributable_files)

    all_filenames = sorted([file + file_suffix for file in all_files])
    redistributable_filenames = sorted([file + file_suffix for file in redistributable_files])
    resticted_filenames = sorted([file + file_suffix for file in restricted_files])

    log_and_print(logfile, f"The translations csv file lists {len(all_files)} translations and {len(redistributable_files)} are redistributable.")
    log_and_print(logfile, f"The translations csv file lists {len(restricted_files)} restrcited translations.")
    log_and_print(logfile, f"{len(restricted_files)} + {len(redistributable_files)} = {len(restricted_files) + len(redistributable_files)}")

    # Find which files have already been downloaded. 
    already_downloaded = sorted([file.name for file in zipped.glob("*" + file_suffix)])
    
    # These wont download usually.
    wont_download = ["due_usfm.zip", "engamp_usfm.zip", "engnasb_usfm.zip", "khm-h_usfm.zip", "khm_usfm.zip", "sancol_usfm.zip", "sankan_usfm.zip", "spaLBLA_usfm.zip", "spanblh_usfm.zip"]

    # For downloading we need to maintain the eBible names e.g. aai_usfm.zip
    print(all_filenames[:3])
    print(already_downloaded[:3])
    print(wont_download[:3])
    print(resticted_filenames[:3])
    exit()

    log_and_print(logfile, f"There are {len(already_downloaded)} files with the suffix {file_suffix} already in {zipped}")
    log_and_print(logfile, f"There are {len(wont_download)} files that usually fail to download.")

    dont_download = set(already_downloaded).union(set(wont_download))
    to_download = sorted(set(all_filenames) - set(dont_download))
    log_and_print(logfile, f"There are {len(to_download)} files still to download.")


    # Download the zipped USFM file if it doesn't already exist.

    for i, filename in enumerate(to_download):

        # Construct the download url and the local file path.
        url = eBible_url + filename
        file = zipped / filename

        # Skip any missing filenames.
        if filename == "":
            continue

        # Skip existing files that contain data.
        elif file.exists() and file.stat().st_size > 100:
            log_and_print(logfile, f"{i+1}: {file} already exists and contains {file.stat().st_size} bytes.")
            continue

        else:
            log_and_print(logfile, f"{i+1}: Downloading from {url} to {file}.")
            done = download_file(url, file)

            if done:
                log_and_print(logfile, f"Saved {url} as {file}\n")
                # Pause for a random number of miliseconds
                pause = randint(1, 5000) / 1000
                sleep(pause)

            else:
                log_and_print(logfile, f"Could not download {url}\n")
                
    log_and_print(logfile, f"Finished downloading eBible files\n")

    unzip_ebibles(zipped, file_suffix, unzipped, logfile)


    # Get copyright info from eBible projects """

    data = list()
    copr_regex = r".*[/\\](?P<id>.*?)[/\\]copr.htm"

    log_and_print(logfile, "Collecting eBible copyright information...")

    for i, copyright_info_file in enumerate(sorted(unzipped.glob("**/copr.htm"))):
        id = str(copyright_info_file.parents[0].relative_to(unzipped))
        
        id_match = regex.match(copr_regex, str(copyright_info_file))
        id = id_match["id"]

        if i % 100 == 0 :
            print(f"Read {i} files. Now reading: {copyright_info_file} with ID: {id}")

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
                descriptions = ["Dialect (if applicable): ", "Dialect: "]
                for description in descriptions:
                    if copy_string.startswith(description):
                        entry["Dialect"] = copy_string[len(description):]
                        break
                    else: 
                        entry["Dialect"] = copy_string

            if "Translation by" in copy_string:
                entry["Translation by"] = copy_string
            if "Public Domain" in copy_string:
                entry["Copyright Year"] = ""
                entry["Copyright Holder"] = "Public Domain"
        
        data.append(entry)

    with open(licence_file, "w", encoding="utf-8", newline='') as csv_out:
        writer = DictWriter(
            csv_out, csv_headers, restval="", extrasaction="ignore", dialect="excel",
        )
        writer.writeheader()
        writer.writerows(data)
        
    log_and_print(logfile, f"Wrote copyright info for {len(data)} translations to {licence_file}\n")

    extracted_files = [entry['ID'][4:] for entry in data]
    missing_files = [file + file_suffix for file in sorted(set(all_files) - set(extracted_files))]
    unexpectedly_missing = set(missing_files) - set(wont_download)

    print(f"There are {len(unexpectedly_missing)} missing extract folders.")

    if len(unexpectedly_missing) == 0:
        print(f"There are exactly {len(wont_download)} missing unzipped folders. They are the same {len(missing_files)} that we didn't try to download.")
    else :
        print(f"{len(unexpectedly_missing)} files were not extracted. Upto 50 are shown:")
        for file in sorted(unexpectedly_missing)[:50]:
            print(file)
    
    #print(sorted(all_files)[:3])
    #print(extracted_files[:3])
    #print(sorted(missing_files)[:3])

if __name__ == "__main__":
    main()
