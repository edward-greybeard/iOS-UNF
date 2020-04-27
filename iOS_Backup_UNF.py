# iOS Backup UNF
# UNFunk iOS backups into something sensible
# Assumes presence of manifest.db, and uses the files present in 'Files' table to determine path.
# Also an example of dataclasses, F-strings, logging and argparse, whew

import sqlite3
import argparse
import logging
import os
from dataclasses import dataclass
from sys import exit

logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level='DEBUG')


@dataclass
class BackupFile:
    file_id: str
    domain: str
    relative_path: str
    file_meta: str
    is_dir: bool
    # TODO: timestamps pls


def get_file_list(manifest_path):
    """
    Returns a dict of {'id': 'file name'..} from manifest.db.
    :param manifest_db_path:
    :return:
    """
    mani_conn = sqlite3.connect(manifest_path)
    cur = mani_conn.cursor()
    logging.debug('Connected to manifest.db')
    sql = 'select fileID, domain, relativePath, file, flags from Files'
    logging.debug('Connected OK. Running SQL..')
    cur.execute(sql)

    file_list = {}
    for file_info in cur.fetchall():
        if file_info[4] == 2:
            is_dir = True
        else:
            is_dir = False
        backup_file = BackupFile(file_id=file_info[0],
                                 domain=file_info[1],
                                 relative_path=file_info[2],
                                 file_meta=file_info[3],
                                 is_dir=is_dir)
        file_list[backup_file.file_id] = backup_file

    logging.debug(f'SQL complete. {len(file_list)} files found and objects added.')
    mani_conn.close()
    return file_list


def process_file_list(input_root, output_root, file_list):
    """
    For each file, reads the file content then writes to a new file in the right "path".
    v1: use domain as top level folder.
    :param output_path:
    :return:
    """
    for backup_id, backup_file in file_list.items():
        # logging.debug(f"{backup_id}: {backup_file.relative_path}")
        if backup_file.is_dir:
            create_directory(backup_file, output_root)


def create_directory(backup_file, output_root):
    """
    Creates a directory
    :param backup_file:
    :param output_root:
    :return:
    """
    dir_path = get_full_path(backup_file)
    full_output_path = os.path.join(output_root, dir_path)
    logging.debug(f"{full_output_path}")
    os.makedirs(full_output_path, exist_ok=True)

def get_full_path(backup_file):
    """
    Generates for us a full path for our data
    :param backup_file:
    :return:
    """
    return os.path.join(backup_file.domain, backup_file.relative_path)

if __name__ == '__main__':
    logging.info("-------------------")
    logging.info("iOS Backup UnFunker")
    logging.info("By Greybeard")
    logging.info("-------------------")

    parser = argparse.ArgumentParser(description="Unpack iOS backups")
    parser.add_argument('-i', '--input', dest='input_dir', type=str, required=True, action='store',
                        help='Input directory')
    parser.add_argument('-o', '--output', dest='output_dir', type=str, default=".\\",
                        help='Output directory (default: current directory)')
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    logging.info(f"Input Dir:  {input_dir}")
    logging.info(f"Output Dir: {output_dir}")

    manifest_path = os.path.join(input_dir, 'manifest.db')

    if os.path.exists(manifest_path) is not True:
        logging.critical(f"Cannot find manifest.db at: {manifest_path}")
        logging.info("Exiting..")
        exit(1)

    file_list = get_file_list(manifest_path)

    logging.info(f"{len(file_list)} entries found in manifest.db")

    logging.info("Beginning File Conversion..")
    process_file_list(input_dir, output_dir, file_list)