#! /usr/bin/python3

import os
import datetime
import shutil
import hashlib
import uuid
import argparse
import msgpack
import zlib
import sys
import struct

def fourslashes(s):
    if s is None:
        return ''
    s = decode_if_bytes(s)
    split_id = [s[i:i+2] for i in range(0, 8, 2)]
    split_id.append(s[8:])
    return '/'.join(split_id)

def decode_if_bytes(s):
    if isinstance(s, bytes):
        return s.decode("utf-8")
    else:
        return s

def compute_sha1(file_path):
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha1.update(chunk)
    return sha1.digest()

def compute_md5(file_path):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.digest()

def compute_adler32(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    adler32_value = zlib.adler32(data) & 0xffffffff
    return struct.pack('!I', adler32_value)

def create_recursive_owncloud_entity(top_dir, space_path, entity_path, parent_uuid=None):
    # Check if the current path is a directory or file
    is_file = os.path.isfile(entity_path)
    
    # Create the entity and get its UUID
    current_uuid = create_owncloud_entity(top_dir, space_path, entity_path, parent_uuid, is_file)
    
    # If it's an existing directory, handle the subdirectories/files recursively
    if not is_file and os.path.isdir(entity_path):
        for sub_item in os.listdir(entity_path):
            sub_item_path = os.path.join(entity_path, sub_item)
            create_recursive_owncloud_entity(top_dir, space_path, sub_item_path, current_uuid)
    
    return current_uuid  # Add a return statement to get the UUID of the last created directory


def create_owncloud_entity(top_dir, space_path, entity_path, parent_uuid=None, is_file=False):
    entity_name = os.path.basename(entity_path)
    # File specific operations
    file_size = os.path.getsize(entity_path) if is_file else 0

    # Adjust symlink directory path for subfolders
    if parent_uuid:
        if is_file:
            symlink_dir_path_components = [
                top_dir,
                "storage",
                "users",
                "spaces",
                space_path,
                "nodes",
                parent_uuid[0:2],
                parent_uuid[2:4],
                parent_uuid[4:6],
                parent_uuid[6:8],
                parent_uuid[8:]
            ]
        else:
            symlink_dir_path_components = [
                top_dir,
                "storage",
                "users",
                "spaces",
                space_path,
                "nodes",
                parent_uuid[0:2],
                parent_uuid[2:4],
                parent_uuid[4:6],
                parent_uuid[6:8],
                parent_uuid[8:]
            ]
    else:
        symlink_dir_path_components = [
            top_dir,
            "storage",
            "users",
            "spaces",
            space_path,
            "nodes",
            space_path.split('/')[0],
            space_path.split('/')[1][0:2],
            space_path.split('/')[1][2:4],
            space_path.split('/')[1][4:6],
            space_path.split('/')[1][6:]
        ]
    symlink_dir_path = os.path.join(*symlink_dir_path_components)

    # Create symlink directory path if it doesn't exist
    os.makedirs(symlink_dir_path, exist_ok=True)

    # Define the symlink entity path
    symlink_entity_path = os.path.join(symlink_dir_path, entity_name)





    # Handle name conflicts
    original_name, extension = os.path.splitext(entity_name)
    counter = 1
    while os.path.exists(symlink_entity_path):
        if is_file:
            entity_name = f"{original_name} ({counter}){extension}"
        else:
            entity_name = f"{original_name} ({counter})"
        symlink_entity_path = os.path.join(symlink_dir_path, entity_name)
        counter += 1

    if is_file:
        # Blob creation process
        blob_uuid = str(uuid.uuid4())
        blob_path_components = [top_dir, "storage", "users", "spaces", space_path, "blobs", blob_uuid[0:2], blob_uuid[2:4], blob_uuid[4:6], blob_uuid[6:8]]
        blob_path = os.path.join(*blob_path_components)
        os.makedirs(blob_path, exist_ok=True)
        destination_path = os.path.join(blob_path, blob_uuid[8:])
        shutil.copy(entity_path, destination_path)
        print(f"File {entity_name} uploaded successfully to {destination_path}!")

    # Node creation process
    node_uuid = str(uuid.uuid4())
    node_path_components = [top_dir, "storage", "users", "spaces", space_path, "nodes", node_uuid[0:2], node_uuid[2:4], node_uuid[4:6], node_uuid[6:8]]
    node_dir = os.path.join(*node_path_components)
    os.makedirs(node_dir, exist_ok=True)

    parentid = ''.join(space_path.split('/')[-2:])
    mpk_file_path = os.path.join(node_dir, node_uuid[8:] + ".mpk")

    parentid = parent_uuid if parent_uuid else ''.join(space_path.split('/')[-2:])

    # File or Directory metadata
    if is_file:
        metadata = {
            'user.ocis.blobid': blob_uuid.encode('utf-8'),
            'user.ocis.blobsize': str(file_size).encode('utf-8'),
            'user.ocis.cs.adler32': compute_adler32(entity_path),
            'user.ocis.cs.md5': compute_md5(entity_path),
            'user.ocis.cs.sha1': compute_sha1(entity_path),
            'user.ocis.name': entity_name.encode('utf-8'),
            'user.ocis.parentid': (parent_uuid if parent_uuid else ''.join(space_path.split('/')[-2:])).encode('utf-8'),
            'user.ocis.type': b'1'
        }
    else:
        metadata = {
            'user.ocis.name': entity_name.encode('utf-8'),
            'user.ocis.parentid': (parent_uuid if parent_uuid else ''.join(space_path.split('/')[-2:])).encode('utf-8'),
            'user.ocis.propagation': b'1',
            'user.ocis.treesize': b'0',
            'user.ocis.type': b'2'
        }
    # If the current directory is the root directory (no parent_uuid)
    if not parent_uuid:
        current_time = datetime.datetime.utcnow().isoformat() + "Z"
        metadata['user.ocis.tmp.etag'] = b''  # Empty value for tmp.etag
        metadata['user.ocis.tmtime'] = current_time.encode('utf-8')



    with open(mpk_file_path, 'wb') as mpk_file:
        mpk_file.write(msgpack.packb(metadata))

    # If this is a file and it has a parent, update the parent's treesize
    if is_file and parent_uuid:
        update_parent_treesize(top_dir, space_path, parent_uuid, file_size)

    node_entity_path = os.path.join(node_dir, node_uuid[8:])
    if is_file:
        with open(node_entity_path, 'w') as empty_file:
            pass
    else:
        os.makedirs(node_entity_path, exist_ok=True)

    # Symlink creation process
    symlink_target_path = os.path.relpath(node_entity_path, symlink_dir_path)
    os.symlink(symlink_target_path, symlink_entity_path)
    print(f"Symlink {os.path.basename(symlink_entity_path)} created at {symlink_entity_path}, pointing to the {'empty node file' if is_file else 'OCIS directory'}!")

    return node_uuid


def update_parent_treesize(top_dir, space_path, child_uuid, size_increase):
    while child_uuid:
        # Constructing the path to the child's .mpk file to get its parent's UUID
        node_path_components = [
            top_dir, "storage", "users", "spaces", space_path, 
            "nodes", child_uuid[0:2], child_uuid[2:4], 
            child_uuid[4:6], child_uuid[6:8], child_uuid[8:] + ".mpk"
        ]
        mpk_file_path = os.path.join(*node_path_components)
        
        # Read and unpack the current metadata
        with open(mpk_file_path, 'rb') as mpk_file:
            metadata = msgpack.unpackb(mpk_file.read(), raw=True)
        
        # Update the treesize
        current_treesize = int(metadata.get('user.ocis.treesize', 0))
        metadata['user.ocis.treesize'] = str(current_treesize + size_increase).encode('utf-8')
        
        # Write the updated metadata back to the file
        with open(mpk_file_path, 'wb') as mpk_file:
            mpk_file.write(msgpack.packb(metadata))

        # Update the child UUID to the parent UUID for the next loop iteration
        child_uuid = metadata.get('user.ocis.parentid')
        if child_uuid:
            child_uuid = child_uuid.decode("utf-8")



def get_available_spaces(top):
    storage_dir = os.path.join(top, "storage")
    if not os.path.isdir(storage_dir):
        print(f"'storage' folder not found in {top}")
        sys.exit(1)
    
    spaces = []
    sprefix = "storage/users/spaces"

    for dirpath, dirnames, filenames in os.walk(os.path.join(top, sprefix)):
        if 'nodes' in dirnames:
            space_nodes_dir = dirpath
            spaceid = dirpath.split('/')[-2] + os.path.basename(dirpath)
            root = os.path.join(space_nodes_dir, "nodes", fourslashes(spaceid))

            mpk_file = f"{root}.mpk"
            with open(mpk_file, 'rb') as f:
                mpk_content = msgpack.unpackb(f.read(), raw=True)  # Fixed this line

            space_name = mpk_content.get(b'user.ocis.space.name', b'N/A').decode('utf-8')
            space_type = mpk_content.get(b'user.ocis.space.type', b'N/A').decode('utf-8')
            
            # Append the actual folder path as the third item in the tuple.
            spaces.append((space_type, space_name, os.path.relpath(dirpath, os.path.join(top, sprefix))))
            
    return spaces

if __name__ == '__main__':
    default_topdir=os.getenv('OCIS_TOPDIR', os.getenv('HOME') + "/.ocis")

    parser = argparse.ArgumentParser(description='Upload files or create directories in the OCIS storage.')

    parser.add_argument('items', nargs='*', help='Paths of the files or directories to be uploaded. Use -s arg format to specify directory name.')
    parser.add_argument('-l', '--list', action='store_true', help='List all available spaces')
    parser.add_argument('-s', '--space', help='The name of the space where the files will be uploaded, followed by a colon and the directory name if creating a directory (e.g., personal/test:foldername)')
    parser.add_argument('--topdir', nargs='?', default=default_topdir, help='The directory of OCIS storage')

    args = parser.parse_args()
    print(args.items)

    if args.list:
        spaces = get_available_spaces(args.topdir)
        print("Available spaces:")
        for space_type, space_name, _ in spaces:
            print(f"{space_type}/{space_name}")
        sys.exit(0)

    if not args.space:  
        print("Error: the -s/--space argument is required unless using -l.")
        sys.exit(1)

    if os.getuid() == 0:
        ocis_uid=os.stat(args.topdir).st_uid
        print(f"Info: changing uid to {ocis_uid}")
        os.setuid(ocis_uid)

    if os.stat(args.topdir).st_uid != os.getuid():
        print(f"Error: uid of topdir {os.stat(args.topdir).st_uid} - you are {os.getuid()}")
        sys.exit(1)

    space_parts = args.space.split(':')
    space = space_parts[0]

    # Extracting space_type and space_name
    space_name_parts = space.split('/')
    if len(space_name_parts) != 2:
        print("Invalid space name. It should be in format 'type/name'.")
        sys.exit(1)
    space_type, space_name = space_name_parts

    # Finding the matching space
    spaces = get_available_spaces(args.topdir)
    matching_spaces = [s for s in spaces if s[0] == space_type and s[1] == space_name]
    if not matching_spaces:
        print(f"No matching space found for {args.space}.")
        sys.exit(1)
    _, _, chosen_space_path = matching_spaces[0]

    # Handling directory or file creation
    last_parent_uuid = None
    if len(space_parts) > 1:
        # It means we're specifying directories inside the space
        for dir_name in space_parts[1].split('/'):
            last_parent_uuid = create_recursive_owncloud_entity(args.topdir, chosen_space_path, dir_name, last_parent_uuid)
    
    # Finally, create the main directories/files
    for item in args.items:
        create_recursive_owncloud_entity(args.topdir, chosen_space_path, item, last_parent_uuid)

