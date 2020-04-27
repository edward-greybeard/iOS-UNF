# iOS Backup UNF
# UNFunk iOS backups into something sensible
# Assumes presence of manifest.db, and uses the files present in 'Files' table to make changes

import sqlite3
import argparse
import logging
import os
from dataclasses import dataclass
from sys import exit

logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level='DEBUG')

@dataclass
class BackupFile:
    file_id : str
    domain: str
    relative_path: str
    file_meta: str
    #TODO: timestamps pls


def get_file_list(manifest_path):
    """
    Returns a dict of {'id': 'file name'..} from manifest.db.
    :param manifest_path:
    :return:
    """
    mani_conn = sqlite3.connect(manifest_path)
    cur = mani_conn.cursor()
    logging.debug('Connected to manifest.db')
    sql = 'select fileID, domain, relativePath, file from Files'
    logging.debug('Connected OK. Running SQL..')
    cur.execute(sql)

    file_list = {}
    for file_info in cur.fetchall():
        backup_file = BackupFile(file_id=file_info[0],
                                 domain=file_info[1],
                                 relative_path=file_info[2],
                                 file_meta=file_info[3])
        file_list[backup_file.file_id] = backup_file

    logging.debug(f'SQL run complete. {len(file_list)} files found.')
    mani_conn.close()
    return file_list

if __name__ == '__main__':
    logging.info("-------------------")
    logging.info("iOS Backup UnFunker")
    logging.info("By Greybeard")
    logging.info("-------------------")


    parser = argparse.ArgumentParser(description="Unpack iOS backups")
    parser.add_argument('-i', '--input', dest='input_dir', type=str, required=True, action='store', help='Input directory')
    parser.add_argument('-o', '--output', dest='output_dir', type=str, default=".\\",
                        help='Output directory (default: current directory)')

    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    logging.info(f"Input Dir:  {input_dir}")
    logging.info(f"Output Dir: {output_dir}")

    manifest_path = os.path.join(input_dir, 'manifest.db')

    if os.path.exists(manifest_path) is not True:
        logging.critical(f'Cannot find manifest.db at: {manifest_path}')
        logging.info('Exiting..')
        exit(1)

    file_list = get_file_list(manifest_path)