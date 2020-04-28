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
from shutil import copyfile

logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level='DEBUG')

# TODO: Add option to input a zipfile
# TODO: Add option to output straight to zipfile

domain_translation = {
    "AppDomain": "private\\var\\mobile\\Containers\\Data\\Application",
    "AppDomainGroup": "private\\var\\mobile\\Containers\\Shared\\AppGroup",
    "AppDomainPlugin": "private\\var\\mobile\\Containers\\Data\\PluginKitPlugin",
    "SysContainerDomain": "private\\var\\containers\\Data\\System",
    "SysSharedContainerDomain": "private\\var\\containers\\Shared\\SystemGroup",
    "KeychainDomain": "private\\var\\Keychains",
    "CameraRollDomain": "private\\var\\mobile",
    "MobileDeviceDomain": "private\\var\\MobileDevice",
    "WirelessDomain": "private\\var\\wireless",
    "InstallDomain": "private\\var\\installd",
    "KeyboardDomain": "private\\var\\mobile",
    "HomeDomain": "private\\var\\mobile",
    "SystemPreferencesDomain": "private\\var\\preferences",
    "DatabaseDomain": "private\\var\\db",
    "TonesDomain": "private\\var\\mobile",
    "RootDomain": "private\\var\\root",
    "BooksDomain": "private\\var\\mobile\\Media\\Books",
    "ManagedPreferencesDomain": "private\\var\\Managed Preferences",
    "HomeKitDomain": "private\\var\\mobile",
    "MediaDomain": "private\\var\\mobile",
    "HealthDomain": "private\\var\\mobile\\Library",

}


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
    Returns a dict of {'id': BackupFile..} from manifest.db.
    :param manifest_path: Path to the manifest.db file
    :return:
    """
    mani_conn = sqlite3.connect(manifest_path)
    cur = mani_conn.cursor()
    logging.debug('Connected to manifest.db')
    sql = 'select fileID, domain, relativePath, file, flags from Files'
    logging.debug('Connected OK. Running SQL..')
    try:
        cur.execute(sql)
    except sqlite3.DatabaseError:
        logging.critical("Manifest.db is not a sqlite database; possibly encrypted.")
        logging.info("Exiting..")
        exit(1)

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

    logging.debug(f'SQL complete. {len(file_list)} entries found and objects added.')
    mani_conn.close()
    return file_list


def process_file_list(input_root, output_root, file_list):
    """
    For each file, reads the file content then writes to a new file in the right "path".
    v1: use domain as top level folder.
    :param input_root: Input directory
    :param output_root: Output directory
    :param file_list: Dict of BackupFile objects
    :return:
    """
    for backup_id, backup_file in file_list.items():
        # logging.debug(f"{backup_id}: {backup_file.relative_path}")
        if backup_file.is_dir:
            create_directory(backup_file, output_root)
        else:
            create_file(backup_file, input_root, output_root)


def create_directory(backup_file, output_root):
    """
    Creates a directory
    :param backup_file: BackupFile object
    :param output_root: Output directory root
    :return:
    """
    full_output_path = get_output_path(backup_file, output_root)
    # logging.debug(f"{full_output_path}")
    os.makedirs(full_output_path, exist_ok=True)


def create_file(backup_file, input_root, output_root):
    """
    Creates a file in our output folder, copied from our input folder.
    :param backup_file: BackupFile object
    :param input_root: Input directory root
    :param output_root: Output directory root
    :return:
    """
    input_path = get_input_path(backup_file, input_root)
    output_path = get_output_path(backup_file, output_root)
    logging.debug(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    copyfile(input_path, output_path)


def get_input_path(backup_file, input_root):
    """
    Gets our input path.
    :param backup_file: BackupFile object
    :param input_root: Input directory root
    :return:
    """
    sub_folder = backup_file.file_id[:2]
    full_input_path = os.path.join(input_root, sub_folder, backup_file.file_id)
    return os.path.normpath(full_input_path)


def get_output_path(backup_file, output_root):
    """
    Generates for us a full path for our data
    :param backup_file: BackupFile object
    :param output_root: Output directory root
    :return:
    """
    # TODO refactor this mess
    global domain_translation
    try:
        major_domain = backup_file.domain.split("-", 1)[0]
    except ValueError:
        major_domain = backup_file.domain
    if major_domain in domain_translation:
        domain_subdir = domain_translation[major_domain]
    else:
        try:
            minor_domain = backup_file.domain.split("-", 1)[1]
            domain_subdir = os.path.join(major_domain, minor_domain)
        except ValueError:
            domain_subdir = backup_file.domain

    dir_path = os.path.join(domain_subdir, backup_file.relative_path)
    full_output_path = os.path.join(output_root, dir_path)
    return os.path.normpath(full_output_path)


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
    logging.info("Complete. Exiting..")
