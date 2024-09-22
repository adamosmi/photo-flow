import os
import hashlib
from pathlib import Path
import shutil


def calculate_hash(file_path, chunk_size=4096):
    """Calculate the hash of a file to identify duplicates."""
    hash_obj = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def find_duplicates(root_folder):
    """Find and return a dictionary of duplicates. The key will be the hash of the file,
    and the value will be a list of files with that hash."""
    file_hashes = {}
    
    for foldername, _, filenames in os.walk(root_folder):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            file_hash = calculate_hash(file_path)
            
            if file_hash not in file_hashes:
                file_hashes[file_hash] = [file_path]
            else:
                file_hashes[file_hash].append(file_path)
    
    # Filter out non-duplicate hashes
    duplicates = {hash_val: files for hash_val, files in file_hashes.items() if len(files) > 1}
    
    return duplicates


def create_symlinks(duplicates, output_folder):
    """Create symbolic links for duplicate files in the output folder."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for file_hash, files in duplicates.items():
        # Use the first file as the original
        original_file = files[0]
        original_file_name = os.path.basename(original_file)
        original_output_path = os.path.join(output_folder, original_file_name)

        # Copy the original file to the output folder if not already done
        if not os.path.exists(original_output_path):
            shutil.copy2(original_file, original_output_path)

        # Create symbolic links for all other duplicates
        for duplicate_file in files[1:]:
            symlink_name = os.path.join(output_folder, os.path.basename(duplicate_file))
            if not os.path.exists(symlink_name):
                os.symlink(original_output_path, symlink_name)
                print(f"Created symlink: {symlink_name} -> {original_output_path}")


def main(root_folder, output_folder):
    """Main function to find duplicates and create symlinks."""
    print(f"Searching for duplicates in folder: {root_folder}")
    
    # Step 1: Find duplicates
    duplicates = find_duplicates(root_folder)
    if duplicates:
        print(f"Found {len(duplicates)} sets of duplicates. Creating symlinks...")
        
        # Step 2: Create symlinks in the output folder
        create_symlinks(duplicates, output_folder)
        print(f"Symlinks created in folder: {output_folder}")
    else:
        print("No duplicates found.")


if __name__ == "__main__":
    # Define the folder to search and the output folder
    root_folder = "/path/to/your/folder"  # Replace with the path you want to search
    output_folder = "/path/to/output/folder"  # Replace with the path for output
    
    main(root_folder, output_folder)
