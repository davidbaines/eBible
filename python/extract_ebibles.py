import download_ebibles
import os
import shutil

def get_folder(file):
    """Return the path of the folder to which the zip file should be extracted."""
    return download_ebibles.unzipped_folder / file.name[0: (len(file.name) - len(download_ebibles.file_suffix))]

def get_tree_size(path):
    """Return total size of files in given path and subdirs."""
    total = 0
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            total += get_tree_size(entry.path)
        else:
            total += entry.stat(follow_symlinks=False).st_size
    return total
    
    
def main():
    pattern = "*" + download_ebibles.file_suffix
    zip_files = [zip_file for zip_file in download_ebibles.zips_folder.glob(pattern)]
    
    # Strip off the pattern so that the subfolder name is the project ID.
    extract_folders = [ (zip_file, get_folder(zip_file)) for zip_file in zip_files ]
    extracts = [ (zip_file, folder) for zip_file, folder in extract_folders if zip_file.stat().st_size >= get_tree_size(folder) ]

    print(
        f"Found {len(zip_files)} files in {download_ebibles.zips_folder} matching pattern: {pattern}"
    )
    print(f"Found {len(extracts)} that are smaller than the zip file.")
    
    for zip_file, extract in extracts:
        extract.mkdir(parents=True, exist_ok=True)
        print(f"Extracting to: {extract}")
        shutil.unpack_archive(zip_file, extract)


if __name__ == "__main__":
    main()