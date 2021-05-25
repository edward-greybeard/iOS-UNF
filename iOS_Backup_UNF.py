# iOS Backup UNF
# UNFunk iOS backups into something sensible
# Assumes presence of manifest.db, and uses the files present in 'Files' table to determine path.
# Also an example of dataclasses, F-strings, logging and argparse, whew

import plistlib
import sqlite3
import argparse
import logging
import os
import zipfile
import datetime
import ccl_bplist
from io import BytesIO
from dataclasses import dataclass
from sys import exit
from shutil import copyfile
from pathlib import Path

logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level='DEBUG')

# TODO: Add option to input a zipfile

BACKUP_ROOT = Path("private") / "var"
DOMAIN_TRANSLATION = {
    "AppDomain": BACKUP_ROOT / "mobile" / "Containers" / "Data" / "Application",
    "AppDomainGroup": BACKUP_ROOT / "mobile" / "Containers" / "Shared" / "AppGroup",
    "AppDomainPlugin": BACKUP_ROOT / "mobile" / "Containers" / "Data" / "PluginKitPlugin",
    "SysContainerDomain": BACKUP_ROOT / "containers" / "Data" / "System",
    "SysSharedContainerDomain": BACKUP_ROOT / "containers" / "Shared" / "SystemGroup",
    "KeychainDomain": BACKUP_ROOT / "Keychains",
    "CameraRollDomain": BACKUP_ROOT / "mobile",
    "MobileDeviceDomain": BACKUP_ROOT / "MobileDevice",
    "WirelessDomain": BACKUP_ROOT / "wireless",
    "InstallDomain": BACKUP_ROOT / "installd",
    "KeyboardDomain": BACKUP_ROOT / "mobile",
    "HomeDomain": BACKUP_ROOT / "mobile",
    "SystemPreferencesDomain": BACKUP_ROOT / "preferences",
    "DatabaseDomain": BACKUP_ROOT / "db",
    "TonesDomain": BACKUP_ROOT / "mobile",
    "RootDomain": BACKUP_ROOT / "root",
    "BooksDomain": BACKUP_ROOT / "mobile" / "Media" / "Books",
    "ManagedPreferencesDomain": BACKUP_ROOT / "Managed Preferences",
    "HomeKitDomain": BACKUP_ROOT / "mobile",
    "MediaDomain": BACKUP_ROOT / "mobile",
    "HealthDomain": BACKUP_ROOT / "mobile" / "Library"
}


@dataclass
class BackupFile:
    file_id: str
    domain: str
    relative_path: str
    file_meta: bytes
    is_dir: bool

    def translated_path(self):
        global DOMAIN_TRANSLATION

        try:
            domain, package_name = self.domain.split("-", 1)
        except ValueError:
            domain = self.domain
            package_name = ""

        if domain in DOMAIN_TRANSLATION:
            domain_subdir = DOMAIN_TRANSLATION[domain] / package_name
        else:
            domain_subdir = Path(domain) / package_name

        true_path = domain_subdir / self.relative_path

        # normalize path and convert it back to Path(); did not found a better way
        return Path(os.path.normpath(true_path))

    def get_mod_time(self):
        """
        Reads file_meta plist and returns modified date
        :return:
        """
        if self.file_meta[:2] == b'bp':
            file_meta_plist = ccl_bplist.load(BytesIO(self.file_meta))
            raw_date_time = file_meta_plist['$objects'][1]['LastModified']
            converted_time = datetime.datetime.fromtimestamp(raw_date_time)
            converted_time = converted_time.timetuple()
            return converted_time
        else:
            file_meta_plist = plistlib.loads(self.file_meta)
            return file_meta_plist['modified'].timetuple()

    def get_size(self):
        """
        Reads file_meta plist and returns reported file size
        :return:
        """
        if self.file_meta[:2] == b'bp':
            file_meta_plist = ccl_bplist.load(BytesIO(self.file_meta))
            size = file_meta_plist['$objects'][1]['Size']
            return size
        else:
            file_meta_plist = plistlib.loads(self.file_meta)
            return file_meta_plist['size']

    def get_zipinfo(self):
        """
        Generates and returns a zipinfo object. Used for zipfile output.
        :return:
        """
        zipinfo = zipfile.ZipInfo()
        zipinfo.filename = str(self.translated_path())
        zipinfo.date_time = self.get_mod_time()
        zipinfo.file_size = self.get_size()
        return zipinfo


def get_file_list(manifest_path):
    """
    Returns a dict of {'id': BackupFile..} from manifest.db.
    :param manifest_path: Path to the manifest.db file
    :return:
    """
    mani_conn = sqlite3.connect(str(manifest_path))
    cur = mani_conn.cursor()
    logging.debug('Connected to manifest.db')
    sql = 'select fileID, domain, relativePath, file, flags from Files'
    logging.debug('Connected OK. Running SQL..')
    try:
        cur.execute(sql)
    except sqlite3.DatabaseError:
        logging.critical("manifest.db is not a sqlite database; possibly encrypted.")
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


def process_into_zip(input_root, output_root, file_list):
    """
    Creates a zip file in the root of output_root and writes all data into it.
    :param input_root:
    :param output_root:
    :param file_list:
    :return:
    """
    output_path = output_root / "UNF_Backup.zip"
    new_zip = zipfile.ZipFile(str(output_path), "w")
    for backup_id, backup_file in file_list.items():
        if backup_file.is_dir is not True:
            zinfo = backup_file.get_zipinfo()
            data = get_file_data(backup_file, input_root)
            if data is None:
                logging.warning(f"Unable to find data: {backup_file.file_id} ({backup_file.relative_path})")
                continue
            else:
                new_zip.writestr(zinfo, data)
    new_zip.close()


def create_directory(backup_file, output_root):
    """
    Creates a directory
    :param backup_file: BackupFile object
    :param output_root: Output directory root
    :return:
    """
    full_output_path = get_output_path(backup_file, output_root)
    # logging.debug(f"{full_output_path}")
    full_output_path.mkdir(parents=True, exist_ok=True)


def create_file(backup_file, input_root, output_root):
    """
    Creates a file in our output folder, copied from our input folder.
    :param backup_file: BackupFile object
    :param input_root: Input directory root
    :param output_root: Output directory root
    :return:
    """
    input_path = get_input_path(backup_file, input_root)
    if input_path is None:
        logging.warning(f"Missing file: {backup_file.file_id} ({backup_file.relative_path})")
        return 0
    output_path = get_output_path(backup_file, output_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    copyfile(input_path, output_path)


def get_input_path(backup_file, input_root):
    """
    Gets our input path.
    :param backup_file: BackupFile object
    :param input_root: Input directory root
    :return:
    """
    # Case where backup files are in the same folder as manifest.db
    full_input_path = input_root / backup_file.file_id
    if full_input_path.exists():
        return full_input_path

    # Case where backup files exist in subdirectories
    sub_folder = backup_file.file_id[:2]
    full_input_path = input_root / sub_folder / backup_file.file_id
    if full_input_path.exists():
        return full_input_path

    # Otherwise we have no file!
    return None


def get_output_path(backup_file, output_root):
    """
    Generates for us a full path for our data
    :param backup_file: BackupFile object
    :param output_root: Output directory root
    :return:
    """
    dir_path = backup_file.translated_path()
    return output_root / dir_path


def get_file_data(backup_file, input_root):
    """
    Returns file data
    :param backup_file:
    :param input_root:
    :return:
    """
    input_path = get_input_path(backup_file, input_root)
    if input_path is None:
        logging.warning(f"Missing file: {backup_file.file_id} ({backup_file.relative_path})")
        return None
    file_data = open(str(input_path), 'rb').read()

    return file_data


if __name__ == '__main__':
    logging.info("-------------------")
    logging.info("iOS Backup UnFunker")
    logging.info("By Greybeard")
    logging.info("-------------------")

    parser = argparse.ArgumentParser(description="Unpack iOS backups")
    parser.add_argument('-z', '--zip', dest='to_zip', default=False, action="store_true",
                        help='Output to zip')
    parser.add_argument('-i', '--input', dest='input_dir', type=Path, required=True, action='store',
                        help='Input directory')
    parser.add_argument('-o', '--output', dest='output_dir', type=Path, default=Path("."),
                        help='Output directory (default: current directory)')

    args = parser.parse_args()

    input_dir = args.input_dir.resolve(strict=True)
    output_dir = args.output_dir.resolve(strict=True)
    to_zip = args.to_zip

    logging.info(f"Input Dir:  {str(input_dir)}")
    logging.info(f"Output Dir: {str(output_dir)}")

    manifest_path = next(input_dir.glob('[Mm]anifest.db'), None)

    if (manifest_path is None or
            not manifest_path.exists()):
        logging.critical(f"Cannot find manifest.db at: {str(manifest_path)}")
        logging.info("Exiting..")
        exit(1)

    file_list = get_file_list(manifest_path)

    logging.info(f"{len(file_list)} entries found in manifest.db")

    if to_zip is True:
        logging.info("Exporting to zip file..")
        logging.info("Beginning File Conversion..")
        process_into_zip(input_dir, output_dir, file_list)
        logging.info("Complete. Exiting..")
    else:
        logging.info("Exporting to filesystem..")
        logging.info("Beginning File Conversion..")
        process_file_list(input_dir, output_dir, file_list)
        logging.info("Complete. Exiting..")
