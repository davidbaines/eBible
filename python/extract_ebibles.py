import download_ebibles
import shutil

def main():
    pattern = "*" + download_ebibles.file_suffix
    files_to_extract = [file for file in download_ebibles.zips_folder.glob(pattern)]
    print(
        f"Found {len(files_to_extract)} files to extract in {download_ebibles.zips_folder} matching pattern: {pattern}"
    )

    for file_to_extract in files_to_extract:
        # file_to_extract = files_to_extract[0]

        # Strip off the pattern so that the subfolder name is the project ID.
        extract_folder_name = file_to_extract.name[
            0 : (len(file_to_extract.name) - len(download_ebibles.file_suffix))
        ]

        extract_folder = download_ebibles.unzipped_folder / extract_folder_name
        extract_folder.mkdir(parents=True, exist_ok=True)
        print(f"Extracting to: {extract_folder}")
        shutil.unpack_archive(file_to_extract, extract_folder)


if __name__ == "__main__":
    main()