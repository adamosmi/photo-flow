import os
import hashlib
import shutil
import time
from pathlib import Path
from collections import defaultdict
from PIL import Image
from PIL.ExifTags import TAGS

def hash_file(file_path):
    """Compute the hash of a file based on its content."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_camera_and_creation_date(file_path):
    """Retrieve camera name and photo creation date from the file's EXIF metadata.
['PrintImageMatching', 'ResolutionUnit', 'ExifOffset', 'Make', 'Model', 'Software', 'Orientation', 'DateTime', 'YCbCrPositioning', 'YResolution', 'Copyright', 'XResolution', 'Artist', 'ExifVersion', 'ComponentsConfiguration', 'CompressedBitsPerPixel', 'DateTimeOriginal', 'DateTimeDigitized', 'ShutterSpeedValue', 'ApertureValue', 'BrightnessValue', 'ExposureBiasValue', 'MaxApertureValue', 'MeteringMode', 'LightSource', 'Flash', 'FocalLength', 'UserComment', 'ColorSpace', 'OffsetTime', 'OffsetTimeOriginal', 'OffsetTimeDigitized', 'ExifImageWidth', 'ExifImageHeight', 'FocalPlaneXResolution', 'FocalPlaneYResolution', 'FocalPlaneResolutionUnit', 'SensingMethod', 'FileSource', 'ExposureTime', 'ExifInteroperabilityOffset', 'FNumber', 'SceneType', 'ExposureProgram', 'CustomRendered', 'ISOSpeedRatings', 'ExposureMode', 'FlashPixVersion', 'SensitivityType', 'WhiteBalance', 'BodySerialNumber', 'LensSpecification', 'LensMake', 'LensModel', 'LensSerialNumber', 'FocalLengthIn35mmFilm', 'SceneCaptureType', 'Sharpness', 'SubjectDistanceRange', 'MakerNote']


    """
    try:
        image = Image.open(file_path)
        exif_data = image._getexif()
        exif = {TAGS.get(tag): value for tag, value in exif_data.items() if tag in TAGS}

        # Extract camera make and model
        camera_make = exif.get('Make')
        camera_model = exif.get('Model')

        camera_name = '_'.join([camera_make, camera_model]) if (camera_make is not None) & (camera_model is not None) else 'UnknownCamera'

        # Extract creation date
        date_taken = exif.get('DateTime', time.strftime("%Y:%m:%d", time.gmtime(os.path.getmtime(file_path))))
        year, month, day = date_taken[:10].split(":")

        return camera_name, f"{year}/{month}/{day}"
    except Exception as e:
        print(f"Could not process EXIF data for {file_path}: {e}")
        return "UnknownCamera", time.strftime("%Y/%m/%d", time.gmtime(os.path.getmtime(file_path)))

def organize_files(source_folder, output_folder):
    """Organize files in the output folder, deduplicating by content and using symlinks."""
    hash_map = defaultdict(list)
    
    # Walk through all files in the source folder recursively
    for root, dirs, files in os.walk(source_folder):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_hash = hash_file(file_path)
            hash_map[file_hash].append(file_path)

    # Deduplicate and organize based on EXIF data
    for file_hash, file_list in hash_map.items():
        # Pick the most recent or random file if multiple instances exist
        most_recent_file = max(file_list, key=lambda f: os.path.getmtime(f))
        
        # Extract camera name and creation date
        camera_name, creation_date = get_camera_and_creation_date(most_recent_file)

        # Create the target folder structure
        target_dir = os.path.join(output_folder, camera_name, creation_date)
        os.makedirs(target_dir, exist_ok=True)

        # Symlink or copy the most recent file into the target folder
        for file_path in file_list:
            target_symlink = os.path.join(target_dir, os.path.basename(file_path))
            if not os.path.exists(target_symlink):
                os.symlink(file_path, target_symlink)

