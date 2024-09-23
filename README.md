# Photo Organizer

This repository contains a script designed to organize image and video files in a specified folder structure, using camera EXIF metadata and creation dates. It works by deduplicating files based on their content and creating symbolic links to the organized files.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Usage](#usage)
- [Folder Structure](#folder-structure)
- [Contributing](#contributing)
- [License](#license)

## Features
- **Organize Photos by Camera and Date:** Extracts EXIF metadata to determine the camera make, model, and creation date.
- **Deduplication:** Files are deduplicated based on their content (using MD5 hashing), and only unique images are organized.
- **Supports Symlinks:** Organizes files using symbolic links, so no files are duplicated in the output folder.
- **Supports Various Image Formats:** Common formats such as JPEG, PNG, GIF, BMP, TIFF, and RAW are supported.
- **Supports Video Files:** While video files don’t contain EXIF data, they are still organized based on creation date.

## Requirements
- Python 3.x
- Install the required dependencies using:

```bash
pip install -r requirements.txt
```

### Required Libraries:
- `Pillow`: For reading EXIF metadata from image files.
- `hashlib`: For computing MD5 hash of files to identify duplicates.
- `os`: For interacting with the file system.
- `time`: For working with file creation dates.
- `collections`: For handling file lists.

## Usage
1. **Clone the Repository:**
   Clone this repository into a folder that contains the media files (images/videos) you want to organize.

```bash
git clone https://github.com/adamosmi/photo-flow.git
```

2. **Run the Script:**
   The `run.py` script is designed to operate on the parent folder of where it is placed. After cloning the repository, simply run the `run.py` file:

```bash
python run.py
```

   This script will scan the parent folder, organize the files, and output the organized structure in a folder named `photo-flow` within the same parent directory.

3. **Output Folder:**
   The organized files will be placed in a newly created `photo-flow` directory within the parent folder. The folder structure will be based on the camera and date information, as shown below.

## Folder Structure
The output directory will have the following structure:

```bash
photo-flow/
  ├── CameraName_Model/
  │   ├── 2023/
  │   │   ├── 2023-09-20/
  │   │   │   └── image1.jpg
  │   │   ├── 2023-09-21/
  │   │   │   └── image2.jpg
  ├── UnknownCamera/
  │   ├── 2023/
  │   │   ├── 2023-09-20/
  │   │   │   └── video1.mp4
```
Where:
- **CameraName_Model:** The folder name is based on the camera's make and model (from EXIF metadata).
- **Year:** Organized by the year the photo or video was taken.
- **Date:** Further organized by the exact date of the media file.

If no EXIF data is available, the folder name will default to `UnknownCamera`.

## Contributing
Contributions are welcome! If you have ideas to improve the script or add new features, feel free to fork the repository and submit a pull request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.




