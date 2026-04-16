import hashlib
import os
import platform
import subprocess
import datetime
import zlib
import re

class CRC32Wrapper:
    def __init__(self):
        self.crc = 0
    def update(self, data):
        self.crc = zlib.crc32(data, self.crc)
    def hexdigest(self):
        return format(self.crc & 0xFFFFFFFF, '08x')

# Star program
print("Starting program...")

# Select option hash
supported_algorithms = ["md5", "sha1", "sha224", "sha256", "sha384", "sha512", "blake2b", "blake2s", "crc32"]
print(f"Supported algorithms: {', '.join(supported_algorithms)}")
option_hash = input("Select hash: ").lower().strip()

# Check current directory
check_dir_path = input("Directory: ")

# Printing your choose directory
print(f"Your directory to check files is {check_dir_path}")

# Get the base name of the directory (e.g., 'checkhash' from '.../checkhash')
dir_basename = os.path.basename(os.path.normpath(check_dir_path))
# Construct the output hash file path in a cross-platform way
current_hash = os.path.join(check_dir_path, f"{dir_basename}.{option_hash}")

# Validate hash option
if option_hash not in supported_algorithms:
    print(f"Unsupported hash algorithm: {option_hash}. Please use one of: {', '.join(supported_algorithms)}")
    exit()

# Collect all files to be hashed/validated to show progress
print("Collecting files...")
files_to_process = []
for root, dirs, files in os.walk(check_dir_path):
    for file in files:
        file_path = os.path.join(root, file)
        # Exclude the output hash file from being hashed (relevant for non-crc32 modes)
        if option_hash != "crc32" and os.path.normpath(file_path) == os.path.normpath(current_hash):
             continue
        # Also exclude report file if it exists
        if file == "corrupted_report.md":
             continue
        files_to_process.append(file_path)

total_files = len(files_to_process)
if total_files == 0:
    print("No files to process in the specified directory.")
    exit()

print(f"Found {total_files} files to process.")

# Mode setup
is_crc_filename_mode = (option_hash == "crc32")
is_validation = False
existing_hashes = {}

if not is_crc_filename_mode:
    is_validation = os.path.exists(current_hash)
    if is_validation:
        print(f"Hash file '{os.path.basename(current_hash)}' already exists. Validating...")
        try:
            with open(current_hash, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split(" *", 1)
                        if len(parts) == 2:
                            h, path = parts
                            existing_hashes[path] = h
        except Exception as e:
            print(f"Error reading existing hash file: {e}")
            is_validation = False

# Result states
result_hash = []
corrupted_log_entries = []
matches = 0
mismatches = 0
new_files = 0
renamed_files = 0
seen_files = set()

# Pattern for CRC32 in filename: [AABBCCDD] or (AABBCCDD)
crc_pattern = re.compile(r'[\[\({]([0-9a-fA-F]{8})[\]\)}]')

# Loop through collected files and calculate hashes
for i, file_path in enumerate(files_to_process):
    try:
        count = i + 1
        relative_path = os.path.relpath(file_path, check_dir_path)
        file_size = os.path.getsize(file_path)
        seen_files.add(relative_path)
        filename = os.path.basename(file_path)

        # Hash calculation
        with open(file_path, "rb") as f:
            if option_hash == "crc32":
                file_hash = CRC32Wrapper()
            else:
                file_hash = hashlib.new(option_hash)
            bytes_read = 0
            while chunk := f.read(8192):
                file_hash.update(chunk)
                bytes_read += len(chunk)
                if file_size > 10 * 1024 * 1024:
                    hashing_percent = (bytes_read / file_size) * 100
                    overall_percent = (count / total_files) * 100
                    print(f"({overall_percent:6.2f}%) Hashing [{hashing_percent:3.0f}%] {relative_path}", end='\r')

            calculated_hash = file_hash.hexdigest()

        # Logic separation
        if is_crc_filename_mode:
            match = crc_pattern.search(filename)
            if match:
                expected_crc = match.group(1).lower()
                if calculated_hash == expected_crc:
                    matches += 1
                    # "do nothing" for valid files
                else:
                    mismatches += 1
                    print(f"({(count/total_files)*100:6.2f}%) {count}: {calculated_hash} (Found) != {expected_crc} (Name) *{relative_path} [CORRUPT]".ljust(120))
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    corrupted_log_entries.append({
                        "hashfile": "FILENAME_CRC",
                        "file": relative_path,
                        "timestamp": timestamp
                    })
            else:
                # No CRC in filename, rename it
                name, ext = os.path.splitext(file_path)
                new_path = f"{name} [{calculated_hash.upper()}]{ext}"
                try:
                    os.rename(file_path, new_path)
                    renamed_files += 1
                    print(f"({(count/total_files)*100:6.2f}%) {count}: RENAMED -> {os.path.basename(new_path)}".ljust(120))
                except Exception as e:
                    print(f"\nCould not rename {relative_path}: {e}")
        else:
            # Standard Hashfile Logic
            result = f"{calculated_hash} *{relative_path}"
            if is_validation:
                if relative_path in existing_hashes:
                    if calculated_hash == existing_hashes[relative_path]:
                        matches += 1
                        result_hash.append(result)
                        continue
                    else:
                        mismatches += 1
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        corrupted_log_entries.append({
                            "hashfile": os.path.basename(current_hash),
                            "file": relative_path,
                            "timestamp": timestamp
                        })
                        result_hash.append(f"{existing_hashes[relative_path]} *{relative_path}")
                        print(f"({(count/total_files)*100:6.2f}%) {count}: {result} [CORRUPT]".ljust(120))
                else:
                    new_files += 1
                    result_hash.append(result)
                    print(f"({(count/total_files)*100:6.2f}%) {count}: {result} [NEW]".ljust(120))
            else:
                print(f"({(count/total_files)*100:6.2f}%) {count}: {result}".ljust(120))
                result_hash.append(result)

    except IOError as e:
        print(f"\nCould not read file {file_path}: {e}")

# Missing check for hashfile mode
missing_files = []
if is_validation:
    for path in existing_hashes:
        if path not in seen_files:
            missing_files.append(path)

# Summary
print("\n--- Final Summary ---")
print(f"Total files in directory: {total_files}")
if is_crc_filename_mode:
    print(f"Correct CRC in Name: {matches}")
    print(f"Corrupt CRC in Name: {mismatches}")
    print(f"Files Renamed with CRC: {renamed_files}")
else:
    print(f"Validated files (Matches): {matches}")
    print(f"Corrupt files (Mismatches): {mismatches}")
    print(f"New files (Not exists before): {new_files}")
    print(f"Files not exists now (Missing): {len(missing_files)}")

# Updates
if not is_crc_filename_mode:
    if is_validation:
        count_mismatch = (len(existing_hashes) != total_files)
        if count_mismatch or new_files > 0 or mismatches > 0 or len(missing_files) > 0:
            print("\nChange detected. Updating records...")
            with open(current_hash, "w") as filehash:
                for content_hash in result_hash:
                    filehash.write("%s\n" % content_hash)
            if new_files > 0: print(f"Hash file updated with {new_files} NEW entries.")
            if mismatches > 0: print(f"Corrupted entries PRESERVED in record keeping.")
        else:
            print("\nNo changes detected. Integrity preserved.")
    else:
        if total_files > 0:
            with open(current_hash, "w") as filehash:
                for content_hash in result_hash:
                    filehash.write("%s\n" % content_hash)
            print(f"Hash file saved at: {current_hash}")

# Corrupted Report
if mismatches > 0:
    report_file = os.path.join(check_dir_path, "corrupted_report.md")
    with open(report_file, "a") as f:
        if not os.path.exists(report_file) or os.path.getsize(report_file) == 0:
            f.write("| Timestamp | Source | Corrupted File |\n")
            f.write("| --- | --- | --- |\n")
        source = "FILENAME_CRC" if is_crc_filename_mode else os.path.basename(current_hash)
        for entry in corrupted_log_entries:
            f.write(f"| {entry['timestamp']} | {source} | {entry['file']} |\n")
    print(f"Corrupted files details logged in: {report_file}")

# Open folder
if platform.system() == "Windows":
    os.startfile(check_dir_path)
elif platform.system() == "Darwin":
    subprocess.Popen(["open", check_dir_path])

print("Stopping program... Thank you :)")