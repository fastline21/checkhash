# CheckHash

CheckHash is a high-integrity Python utility for calculating and validating file checksums. It supports two distinct modes of operation: **Standard Hashfile Mode** (for traditional integrity tracking) and **Special CRC32 Mode** (for filename-based tagging and validation).

## Features

- **Wide Algorithm Support**: Supports `md5`, `sha1`, `sha224`, `sha256`, `sha384`, `sha512`, `blake2b`, `blake2s`, and `crc32`.
- **Intelligent Skip-on-Success**: Skips successful matches in the console to focus your attention on **CORRUPT** and **NEW** files.
- **Proof-of-State Preservation**: In Standard Mode, the script preserves original hashes in the record file even if a file is found to be corrupted. This maintains historical context and "proof of state."
- **Special CRC32 Filename tagging**: Automatically detects CRC32 codes in filenames (e.g., `file [AABBCCDD].txt`) for validation, or tags unlabeled files by renaming them.
- **Automated Reporting**: Logs detailed corruption events to `corrupted_report.md` with timestamps and source references.
- **No Dependencies**: Built entirely using Python standard libraries.

## Installation

Ensure you have Python 3 installed. No external packages are required.

```bash
git clone https://github.com/yourusername/checkhash.git
cd checkhash
```

## Usage

1. Run the script:
   ```bash
   python main.py
   ```
2. Follow the interactive prompts:
   - **Select hash**: Enter a supported algorithm (e.g., `sha256`, `crc32`).
   - **Directory**: Provide the path to the folder you wish to process.

## How it Works

### Standard Hashfile Mode (MD5, SHA256, etc.)
1. **First Run**: Calculates hashes for all files and saves them to `<directory_name>.<algorithm>`.
2. **Subsequent Runs**: 
   - Compares current files against the stored records.
   - Successful matches are hidden for clarity.
   - New files are appended to the hash file.
   - Corrupted files are preserved in the hash file (keeping the original hash as proof) and logged to the report.

### Special CRC32 Mode
1. **Filename Scan**: Searches filenames for 8-character hex codes in `[ ]`, `( )`, or `{ }`.
2. **Validation**: If a code is found, the file's current CRC32 is verified against it.
3. **Auto-Tagging**: If no code is found, the script calculates the CRC32 and renames the file to include the hash (e.g., `movie.mp4` → `movie [A1B2C3D4].mp4`).

## Example Output (Standard Mode)

```text
Starting program...
Supported algorithms: md5, sha1, sha224, sha256, sha384, sha512, blake2b, blake2s, crc32
Select hash: sha256
Directory: ./backups
Found 4 files to process.
Hash file 'backups.sha256' already exists. Validating...

( 25.00%) 1: 5891b5b355... *image.png [CORRUPT]
(100.00%) 4: c912c89872... *new_notes.txt [NEW]

--- Final Summary ---
Total files in directory: 4
Validated files (Matches): 2
Corrupt files (Mismatches): 1
New files (Not exists before): 1
Files not exists now (Missing): 0

Change detected. Updating records...
Hash file 'backups.sha256' updated with 1 NEW entries.
Corrupted entries PRESERVED in 'backups.sha256' for record keeping.
Corrupted files details logged in: backups/corrupted_report.md
```

## Reports

All integrity failures are logged in `corrupted_report.md`:

| Timestamp | Source | Corrupted File |
| --- | --- | --- |
| 2026-04-16 18:40:22 | backups.sha256 | image.png |
| 2026-04-16 18:50:11 | FILENAME_CRC | video [AABBCCDD].mkv |

## License

MIT