import os
import hashlib
import time
from collections import defaultdict
from PIL import Image
from PIL.ExifTags import TAGS
from pymediainfo import MediaInfo
import json

IMAGE_EXTENSIONS = [
    ".jpeg", ".jpg", ".png", ".gif", ".bmp", ".tiff", ".tif", 
    ".webp", ".heic", ".heif", ".svg", ".raw", ".cr2", 
    ".nef", ".arw", ".dng"
]

VIDEO_EXTENSIONS = [
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", 
    ".webm", ".3gp", ".mpeg", ".mpg", ".mts", ".m2ts"
]

CAMERA_NAME_ALIASES = {"FUJIFILM_X-T4": "Fuji_XT4", "FUJIFILM_X-T20": "Fuji_XT20"}

def hash_file(file_path):
    """Compute the hash of a file based on its content."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def output_image_path(file_path):
    """Retrieve camera name and photo creation date from the file's EXIF metadata."""
    try:
        image = Image.open(file_path)
        exif_data = image._getexif()
        exif = {TAGS.get(tag): value for tag, value in exif_data.items() if tag in TAGS}
        camera_make = exif.get('Make')
        camera_model = exif.get('Model')
        camera_name = '_'.join([camera_make, camera_model]) if (camera_make is not None) & (camera_model is not None) else 'UnknownCamera'
        date_taken = exif.get('DateTime', time.strftime("%Y:%m:%d", time.gmtime(os.path.getmtime(file_path))))
        year, month, day = date_taken[:10].split(":")
        return camera_name, year, f"{year}-{month}-{day}"
    except Exception:
        return "UnknownCamera", time.strftime("%Y", time.gmtime(os.path.getmtime(file_path))), time.strftime("%Y-%m-%d", time.gmtime(os.path.getmtime(file_path)))

def output_video_path(file_path):
    """Retrieve camera name and video creation date from the file's metadata using pymediainfo."""
    try:
        media_info = MediaInfo.parse(file_path)
        data = json.loads(media_info.to_json())
        camera_name = "UnknownCamera"
        date_taken = time.strftime("%Y:%m:%d", time.gmtime(os.path.getmtime(file_path)))
        for track in data.get('tracks'):
            if track.get('track_type') == "General":
                if track.get('movie_more') == "FUJIFILM DIGITAL CAMERA X-T4":
                    camera_name = "Fuji_XT4"
                if track.get('comapplequicktimemake') == 'Apple':
                    camera_make = track.get('comapplequicktimemake')
                    camera_model = track.get('comapplequicktimemodel')
                    camera_name = '_'.join([camera_make, camera_model]).replace(' ', '_')
                date_taken = track.get('file_last_modification_date__local')
                year, month, day = date_taken[:10].split("-")
                return camera_name, year, f"{year}-{month}-{day}"
    except Exception:
        return "UnknownCamera", time.strftime("%Y", time.gmtime(os.path.getmtime(file_path))), time.strftime("%Y-%m-%d", time.gmtime(os.path.getmtime(file_path)))

def organize_files(source_folder, output_folder):
    """Organize files in the output folder, deduplicating by content and using symlinks."""
    image_hash_map = defaultdict(list)
    video_hash_map = defaultdict(list)

    for path, _, files in os.walk(source_folder):
        for file_name in files:
            file_path = os.path.join(path, file_name)
            extension = os.path.splitext(file_name)[1].lower().strip()
            
            if extension in IMAGE_EXTENSIONS:
                if not os.path.islink(file_path):
                    file_hash = hash_file(file_path)
                    camera_name, creation_year, creation_date = output_image_path(file_path)
                    image_hash_map[file_hash].append(file_path)
            
            if extension in VIDEO_EXTENSIONS:
                if not os.path.islink(file_path):
                    file_hash = hash_file(file_path)
                    camera_name, creation_year, creation_date = output_video_path(file_path)
                    video_hash_map[file_hash].append(file_path)

    # Deduplicate and organize images
    for file_hash, file_list in image_hash_map.items():
        most_recent_file = min(file_list, key=lambda f: os.path.getmtime(f))
        camera_name, creation_year, creation_date = output_image_path(most_recent_file)
        camera_name = CAMERA_NAME_ALIASES.get(camera_name, camera_name)
        target_dir = os.path.join(output_folder, camera_name, creation_year, creation_date)
        os.makedirs(target_dir, exist_ok=True)
        target_symlink = os.path.join(target_dir, os.path.basename(most_recent_file))
        if not os.path.exists(target_symlink):
            os.symlink(most_recent_file, target_symlink)

    # Deduplicate and organize videos
    for file_hash, file_list in video_hash_map.items():
        most_recent_file = min(file_list, key=lambda f: os.path.getmtime(f))
        camera_name, creation_year, creation_date = output_video_path(most_recent_file)
        camera_name = CAMERA_NAME_ALIASES.get(camera_name, camera_name)
        target_dir = os.path.join(output_folder, camera_name, creation_year, creation_date)
        os.makedirs(target_dir, exist_ok=True)
        target_symlink = os.path.join(target_dir, os.path.basename(most_recent_file))
        if not os.path.exists(target_symlink):
            os.symlink(most_recent_file, target_symlink)
