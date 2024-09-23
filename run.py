"""
This repo is meant to be cloned into the folder of the dump. This is meant to operate on the parent folder.
"""
import os
from src.main import organize_files

# Get the absolute path of the current script
current_script_path = os.path.abspath(__file__)

# Get the directory containing the script
current_directory = os.path.dirname(current_script_path)

# Get the parent directory of the current directory
parent_directory = os.path.dirname(current_directory)
output_directory = os.path.join(parent_directory, 'photo-flow-output')

organize_files(source_folder=parent_directory, output_folder=output_directory)

