import csv
import logging
import os
from pathlib import Path
from random import randint
import requests
from time import sleep


# Tell the script where to find a list of URLS to download.
# urls_filename = "BibleZips.txt"

# Or
base_url = r"https://ebible.org/Scriptures/"

file_suffix = "_usfm.zip"

root_folder = Path(
    r"D:\GitHub\BibleNLP\bible-parallel-corpus-internal\corpus\eBible"
)
root_folder = Path(r"C:\eBible")
zips_folder = root_folder / "sources"
unzipped_folder = root_folder / "extracted_sources"

metadata_folder = root_folder / "metadata"
metadata_csv = metadata_folder / "translations.csv"

online_csv_url = r"https://ebible.org/Scriptures/translations.csv"



def download_csv_file(url, headers, save_as):

    r = requests.get(url, headers=headers)
    # If the status is OK continue
    if r.status_code == requests.codes.ok:

        with open(save_as, "wb") as out_file:
            # Write out the content of the page.
            out_file.write(r.content)

        return save_as
    return None


def save_csv_file(csv_url, save_as):
    print(f"Saving file from {csv_url} to {zips_folder}")

    r = requests.get(csv_url)
    # If the status is OK continue
    if r.status_code == requests.codes.ok:

        with open(save_as, "wb") as csv_file:
            csv_file.write(r.content)
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


def main():
    # Set logging level
    logging.basicConfig(level=logging.INFO)

    # Set the user-agent to Chrome for Requests.
    headers = {"user-agent": "Chrome/51.0.2704.106"}

    if not metadata_csv.exists() or not metadata_csv.is_file():
        if zips_folder.exists() and zips_folder.is_dir():

            print(f"The folder for zipfiles exists at: {zips_folder}")

            # Download the list of translations.
            print(
                f"Downloading list of translations from {online_csv_url} to: {str(metadata_csv)}"
            )
            done = download_csv_file(online_csv_url, headers, metadata_csv)
            if done:
                print(f"Saved the list of tranlations as: {str(metadata_csv)}")

            else:
                print(f"Couldn't download {online_csv_url}")
        else:
            print(f"The target folder {zips_folder} doesn't exist.")
    else:
        print(f"The translations csv file exists at :{str(metadata_csv)}")

    file_infos = []
    countall = count_redist = 0

    with open(metadata_csv, encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
        #        print(reader.fieldnames)
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
        #        print(filenames[0])
        print(
            f"The translations csv file lists {countall} translations and {count_redist} are redistributable."
        )

    # Find which files have already been downloaded:
    already_downloaded = [file.name for file in zips_folder.glob("*" + file_suffix)]
    
    print(
        f"There are {len(already_downloaded)} files with the suffix {file_suffix} already in {zips_folder}"
    )

    print(already_downloaded[0:2])
    print(filenames[0:2])

    # Those that require downloading are the filenames - already_downloaded.
    to_download = set(filenames) - set(already_downloaded)
    print(f"\nThere are {len(to_download)} files still to download.")

    # Download the zipped USFM file if it doesn't already exist.

    for i, filename in enumerate(to_download):

        # Construct the download url and the local file path.
        url = base_url + filename
        save_as = zips_folder / filename

        # Skip any missing filenames.
        if filename == "":
            continue

        # Skip existing files that contain data.
        elif save_as.exists() and save_as.stat().st_size > 100:
            print(
                f"{i+1}: {save_as} already exists and contains {save_as.stat().st_size} bytes."
            )

            continue

        else:
            print(f"{i+1}: Downloading from {url} to {save_as}.")
            done = download_zip_file(url, headers, save_as)

            if done:
                print(f"Saved {url} as {save_as}\n")
                # Pause for a random number of miliseconds
                pause = randint(1, 5000) / 1000
                sleep(pause)

            else:
                print(f"Could not download {url}\n")



if __name__ == "__main__":
    main()