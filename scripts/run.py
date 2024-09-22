import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '../src')
sys.path.append(src_dir)

from main import organize_files
from pathlib import Path

source_folder = Path('/mnt/nfs/Projects/photo-flow/data')
output_folder = Path('/mnt/nfs/Projects/photo-flow/output')

organize_files(source_folder=source_folder, output_folder=output_folder)

