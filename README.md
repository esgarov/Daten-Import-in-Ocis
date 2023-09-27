# Daten-Import-in-Ocis

This tool provides functionality to manage OCIS storage, allowing for the creation of files and directories, and the retrieval of space information.

## Features:

Compute and handle various checksums like SHA1, MD5, and Adler32 for file uploads.
Recursively create directories and upload files to the OCIS storage.
List all available spaces within the OCIS storage.
Handle file name conflicts by appending a counter to the new file's name.
Update the tree size of parent directories after a file upload.
Allows specification of a space and directory within that space for file or directory creation.
Symlink creation for easy access and management.

## Requirements:

Python 3.x
msgpack library (you can install it using pip: pip install msgpack)

## Usage:

```bash
python ocis-import.py [OPTIONS] [ITEMS]
```
## Options:

items: Paths of the files or directories to be uploaded. Use -s arg format to specify directory name.
-l / --list: List all available spaces.
-s / --space: Specify the name of the space where the files will be uploaded, followed by a colon and the directory name if creating a directory (e.g., personal/test:foldername).
--topdir: Directory of OCIS storage (defaults to ~/.ocis or OCIS_TOPDIR environment variable if set).
Examples:

List all available spaces:
```bash
python3 ocis-import.py -l
```
Upload a file to a space:
```bash
python3 ocis-import.py myfile.txt -s personal/test
```
Upload a file to the folder in space:
```bash
python3 ocis-import.py myfile.txt -s personal/test:folder
```
Create a directory in a space:
```bash
python3 ocis-import.py -s personal/test:myfolder
```

Contribute:

Feedback, bug reports, and pull requests are welcome.
