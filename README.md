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
## Some things to note
The manfiest.db file does not contain a fully qualified path - instead, it defines a _Domain_ and a relative path - for example, it might list 'MediaDomain' and a relative path of 'Media/Recordings/Recordings.db'.

### Known Domains
iDevices list the root path of most of these domains in '/System/Library/Backup/Domains.plist'. This file isn't backed up by default, but the mappings it defines (and the ones this script uses) are as follows:

| Domain | Mapped path |
|:--------:| -------- |
| KeychainDomain |  /var/Keychains |
| CameraRollDomain |  /var/mobile |
| MobileDeviceDomain |  /var/MobileDevice |
| WirelessDomain |  /var/wireless |
| InstallDomain |  /var/installd |
| KeyboardDomain |  /var/mobile |
| HomeDomain |  /var/mobile |
| SystemPreferencesDomain |  /var/preferences |
| DatabaseDomain |  /var/db |
| TonesDomain |  /var/mobile |
| RootDomain |  /var/root |
| BooksDomain |  /var/mobile/Media/Books |
| ManagedPreferencesDomain |  /var/Managed Preferences |
| HomeKitDomain |  /var/mobile |
| MediaDomain |  /var/mobile |
| HealthDomain |  /var/mobile/Library |

### Unknown Domains
There are (as I've found _so far_) 5 more domains which aren't included in Domains.plist. With some examination of full file system extractions vs backups, I've mapped them to the following file structures:

| Domain | Mapped Path |
|:-----:|-------|
| AppDomain | /var/mobile/Containers/Data/Application |
| AppDomainGroup | /var/mobile/Containers/Shared/AppGroup |
| AppDomainPlugin | /var/mobile/Containers/Data/PluginKitPlugin |
| SysContainerDomain | /var/containers/Data/System |
| SysSharedContainerDomain | /var/containers/Shared/SystemGroup |

In true full file system extractions, apps are stored in subfolders underneath these with their BundleIDs, not with their package names; but hey, we do what we can short of including a list of every possible BundleID. 

### /private/
I've taken the courtesy of prefixing the path with "/private/", just like it would be in the "real thing" :)
