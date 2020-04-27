# iOS Backup UNF
# Unpack iOS backups into something sensible

import sqlite3
import argparse
import logging
logging.basicConfig()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Unpack iOS backups")
    parser.add_argument('-i', '--input', dest='input_dir', type=str, required=True, help='Input directory')
    parser.add_argument('-o', '--output', dest='output_dir', type=str, default=".\\",
                        help='Output directory (default: current directory)')

    args = parser.parse_args()

    logging.info(f"Input Dir: {input_dir}")
