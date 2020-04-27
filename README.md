# iOS Backup UNFunker
Easy method to re-arrange iOS backups into something more sensible to examine. Assumes there is a manifest.db ion the root of the backup folder with all the details. Doesn't check any plists - just goes straight to renaming files.

## Usage
```
usage: iOS_Backup_UNF.py [-h] -i INPUT_DIR [-o OUTPUT_DIR]

Unpack iOS backups

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_DIR, --input INPUT_DIR
                        Input directory
  -o OUTPUT_DIR, --output OUTPUT_DIR
                        Output directory (default: current directory)

```
