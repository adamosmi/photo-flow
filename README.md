# Goal
For my current photo workflow, I am currently dumping all my camera files into a single folder on my local machine.
I want to build a system where I am deduplicating all the files that exist in this folder, looking recursively incase the same file was copied over multiple times.
I want to organize by metadata, with an output as follows:
Camera Name/Year of photo creation (YYYY)/Date of photo creation (YYYY/MM/DD)/File name

# Tests
### Test 1:
* 1 File per folder, all created/updated at the same time, same data in each file, same file names.
* 3 Folders
* 0 Subfolders

Expected outcome:
* Output folder with the format: Camera Name/Year of photo creation (YYYY)/Date of photo creation (YYYY/MM/DD)/
* One symlink inside the folder pointing to the most recently created file on the filesystem. If there are multiple instances of the same file created at the same time on the filesystem, pick one at random.

### Test 2:
* 1 File per folder, all created/updated at the same time, same data in each file, different file names.
* 3 Folders
* 0 Subfolders

Expected outcome (same as Test 1):
* Output folder with the format: Camera Name/Year of photo creation (YYYY)/Date of photo creation (YYYY/MM/DD)/
* One symlink inside the folder pointing to the most recently created file on the filesystem. If there are multiple instances of the same file created at the same time on the filesystem, pick one at random.

### Test 3:
* 1 File per folder, same camera, all created/updated at the same time, different data in each file, different file names.
* 3 Folders
* 0 Subfolders

Expected outcome:
* Output folder with the format: Camera Name/Year of photo creation (YYYY)/Date of photo creation (YYYY/MM/DD)/
* 3 symlinks inside the folder pointing to the most recently created file on the filesystem. If there are multiple instances of the same file created at the same time on the filesystem, pick one at random.

### Test 4:
* 1 File per folder, same cameras, all created/updated at the same time, different data in each file, same file name.
* 3 Folders
* 0 Subfolders

### Test 5:
* 1 File per folder, all created/updated at the same time, same data in each file, same file name.
* 3 Folders
* 0 Subfolders

