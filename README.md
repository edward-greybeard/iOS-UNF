# iOS Backup UnFunker
Easy method to re-arrange iOS backups into something more sensible to examine. Assumes there is a manifest.db ion the root of the backup folder with all the details. Doesn't check any plists - just goes straight to renaming files.

## Usage
```
usage: iOS_Backup_UNF.py [-h] [-z] -i INPUT_DIR [-o OUTPUT_DIR]

Unfunk iOS backups

optional arguments:
  -h, --help            show this help message and exit
  -z, --zip             Output to zip
  -i INPUT_DIR, --input INPUT_DIR
                        Input directory
  -o OUTPUT_DIR, --output OUTPUT_DIR
                        Output directory (default: current directory)
```
## Some things to note
The manifest.db file does not contain a fully qualified path - instead, it defines a _Domain_ and a _relative path_. For example, it might list 'MediaDomain' and a relative path of 'Media/Recordings/Recordings.db'. But 'MediaDomain' isn't a directory on an iOS filesystem - so where does it map to?

### Known Domains
iDevices list the root path of _most_ of these domains in '/System/Library/Backup/Domains.plist'. This file isn't backed up so it only appears in full extractions - but it doesn't really seem to change between devices. The mappings it defines (and the ones this script uses) are as follows:

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

In true full file system extractions, apps are stored in subfolders underneath these with their BundleIDs, not with their package names; while it is my aim to eventually obtaint he BundleID through the appstate.db and do a true conversion, currently the data is stuck in under the package name and it seems to work OK.

### /private/
I've taken the courtesy of prefixing the path with "/private/", just like it would be in the "real thing" :)

## FAQs
 - *Can it decrypt backups?* No it cannot.
 - *Is this like a full filesystem?* No it isn't. It doesn't magically add files, it just restores them to their proper filepath.
 - *Why do this?* Some examiners prefer to be able to resolve the content back to the actual file name and path. Also, some tools seem to prefer the reconstructed output and pull more artefacts out. Weird, huh.
 - ```<Insert vendor tool here>``` does this already, why bother with this?* It's free and I thought it would be fun (it was).
 - UNFunker? UNFunker.
