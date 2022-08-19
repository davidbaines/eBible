#!/usr/bin/env python
import argparse
from bs4 import BeautifulSoup
from csv import DictWriter
import ntpath
from pathlib import Path
import regex


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
    print(f"Url is {url}")
    r = requests.get(url, headers=headers)
    # If the status is OK continue
    if r.status_code == requests.codes.ok:
        soup = BeautifulSoup(r.content, "lxml")
        cr_item = soup.find("td", colspan="3")
        return cr_item.string
    else:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize the licence information for each eBible."
    )
    parser.add_argument("folder", help="Directory containing eBible projects")
    parser.add_argument("output", help="Output csv filename and path")
    args = parser.parse_args()
    
    ebible_folder = Path(args.folder)
    licence_file = Path(args.output)
    
    ebible_detail_base_url = r'https://ebible.org/find/details.php?id='
    ebible_detail_url_suffix = r'&all=1'
    
    copyright_info_files = list(ebible_folder.glob("**/copr.htm"))
    # for htm in copyright_info_files:
    #    print(htm)

    data = list()
    copr_regex = r".*\\(?P<id>.*?)\\copr.htm"

    for copyright_info_file in copyright_info_files:
    
        
        id_match = regex.match(copr_regex, str(copyright_info_file))
        print(copyright_info_file, id_match)
        id = id_match["id"]

        entry = dict()
        entry["ID"] = str(id)
        entry["File"] = copyright_info_file

        # get the details webpage and check the 
        #url = ebible_detail_base_url + id
        #copyright_from_url = f"{get_copyright_from_url(url)}"
        #entry["Copyright from URL"] = copyright_from_url

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
                        print(f'Licence version = {cc_by_match["version"]}')
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

    for item in data:
        print(item)

    headers = [
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
        #"Copyright from URL",
    ]
    print(headers)

    with open(licence_file, "w", encoding="utf-8") as csv_out:
        writer = DictWriter(
            csv_out, headers, restval="", extrasaction="ignore", dialect="excel"
        )
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Wrote eBible_licences.csv to {ebible_folder}")

if __name__ == "__main__":
    main()
