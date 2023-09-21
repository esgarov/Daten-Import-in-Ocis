# Daten-Import-in-Ocis

OCIS Storage Management Tool

This tool provides functionality to manage OCIS storage, allowing for the creation of files and directories, and the retrieval of space information.

Features:

Upload files or directories to OCIS storage.
Create directories recursively.
View available spaces.
Compute checksums (SHA1, MD5, Adler32) for files.
Symlink files and directories in OCIS storage.
Requirements:

Python 3.x
msgpack library (you can install it using pip: pip install msgpack)

Usage:

bash
Copy code
python script_name.py [OPTIONS] [ITEMS]
Options:

items: Paths of the files or directories to be uploaded. Use -s arg format to specify directory name.
-l / --list: List all available spaces.
-s / --space: Specify the name of the space where the files will be uploaded, followed by a colon and the directory name if creating a directory (e.g., personal/test:foldername).
--topdir: Directory of OCIS storage (defaults to ~/.ocis or OCIS_TOPDIR environment variable if set).
Examples:

List all available spaces:
bash
Copy code
python3 ocis-import.py -l
Upload a file to a space:
bash
Copy code
python3 ocis-import.py -s personal/test myfile.txt
Create a directory in a space:
bash
Copy code
python3 ocis-import.py -s personal/test:myfolder
Contribute:

Feedback, bug reports, and pull requests are welcome.
