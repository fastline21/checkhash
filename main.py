import hashlib
import os
import platform
import subprocess

# Star program
print("Starting program...")

# Select option hash
option_hash = input("Select hash (md5, sha256): ")

# Check current directory
check_dir_path = input("Directory: ")

# Printing your choose directory
print(f"Your directory to check files is {check_dir_path}")

# Get the base name of the directory (e.g., 'checkhash' from '.../checkhash')
dir_basename = os.path.basename(os.path.normpath(check_dir_path))
# Construct the output hash file path in a cross-platform way
current_hash = os.path.join(check_dir_path, f"{dir_basename}.{option_hash}")

# Validate hash option
if option_hash not in ["md5", "sha256"]:
    print(f"Unsupported hash algorithm: {option_hash}. Please use 'md5' or 'sha256'.")
    exit()

# Collect all files to be hashed to show progress
print("Collecting files...")
files_to_hash = []
for root, dirs, files in os.walk(check_dir_path):
    for file in files:
        file_path = os.path.join(root, file)
        # Exclude the output hash file from being hashed
        if os.path.normpath(file_path) != os.path.normpath(current_hash):
            files_to_hash.append(file_path)

total_files = len(files_to_hash)
if total_files == 0:
    print("No files to hash in the specified directory.")
    exit()

print(f"Found {total_files} files to hash.")

# Empty result hash list
result_hash = []

# Count files
count = 0

# Loop through collected files and calculate hashes
for file_path in files_to_hash:
    try:
        # Get file properties for progress display
        relative_path = os.path.relpath(file_path, check_dir_path)
        file_size = os.path.getsize(file_path)

        with open(file_path, "rb") as f:
            # Create a hash object based on the user's selection (e.g., 'md5', 'sha256')
            file_hash = hashlib.new(option_hash)
            bytes_read = 0
            # Read file in chunks
            while chunk := f.read(8192):
                file_hash.update(chunk)
                bytes_read += len(chunk)
                # For files > 10MB, show a live hashing progress bar to prevent "hang" perception
                if file_size > 10 * 1024 * 1024:
                    hashing_percent = (bytes_read / file_size) * 100
                    overall_percent = ((count + 1) / total_files) * 100
                    print(f"({overall_percent:6.2f}%) Hashing [{hashing_percent:3.0f}%] {relative_path}", end='\r')

            # Result hash
            result = f"{file_hash.hexdigest()} *{relative_path}"
            count += 1

            # Calculate and print final progress line for the file
            percent = (count / total_files) * 100
            final_line = f"({percent:6.2f}%) {count}: {result}"
            # Pad with spaces to clear the progress bar line, then print
            print(final_line.ljust(120))

            result_hash.append(result)
    except IOError as e:
        print(f"\nCould not read file {file_path}: {e}")

# If more than 1 count
is_files = "file" if count == 1 else "files"

# Count of check files.
print(f"Finish check files. You got {count} {is_files}.")

# Write in hash file
with open(current_hash, "w") as filehash:
    for content_hash in result_hash:
        filehash.write("%s\n" % content_hash)

# Attempt to open the output folder if on a GUI-based system
if platform.system() == "Windows":
    print(f"Opening the folder: {check_dir_path}")
    os.startfile(check_dir_path)
elif platform.system() == "Darwin":  # macOS
    print(f"Opening the folder: {check_dir_path}")
    subprocess.Popen(["open", check_dir_path])
else:  # Linux and other Unix-like systems
    # Check if a display server is running (for GUI environments)
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        try:
            print(f"Opening the folder: {check_dir_path}")
            subprocess.Popen(["xdg-open", check_dir_path])
        except (FileNotFoundError, OSError):
            print(f"Could not open folder. Please navigate to it manually: {check_dir_path}")
    else:
        # Headless environment (like a server), so just print the path to the output file.
        print(f"Hash file saved at: {current_hash}")
        print("Skipping folder opening on a headless system.")

# Close program
print("Stopping program... Thank you :)")