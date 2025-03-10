# File Organizer

A Python-based utility for **automatically categorizing files** in a directory using the **DeepSeek API**. This tool can also **roll back** the last organization event, supports **smart tagging**, and honors user-provided **file lists** and **excluded directories**.

## Features

1. **DeepSeek-based Categorization**  
   - Each file’s content is extracted and analyzed via the DeepSeek API, which suggests an appropriate category.

2. **Smart Tagging**  
   - Adds flexible “tags” to files in `file_tags.json`, allowing you to list, add, or remove tags and to search for files by tag.

3. **Rollback**  
   - A `rollback_log.json` is maintained after organizing files. Running the script with `--rollback` moves files back to their original locations.

4. **Selective Organization**  
   - A `.files_to_organize` file (optional) may list which files should be processed. If absent, **all supported files** are organized.

5. **Excluded Directories**  
   - A `.excluded_dirs` file (optional) prevents certain subdirectories from being suggested as categories or scanned.

6. **OCR & Document Parsing**  
   - Uses `pytesseract` for images, `PyMuPDF` for PDFs, `python-docx` for Word docs, and built-in reading for `.txt` files.

## Installation

1. **Clone or Download** 
   ```bash
   git clone https://github.com/kemurukagami/Desktop_Cleaner.git
   ```
2. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. (Optional) **Tesseract Installation**:
   - For OCR on images, ensure Tesseract OCR is installed (e.g., `brew install tesseract` on macOS, or use the official [Tesseract for Windows](https://github.com/UB-Mannheim/tesseract/wiki)).

## Setup

1. **DeepSeek API Key**:
   - Create a `.env` file in the **base directory** or set an environment variable:
     ```ini
     DEEPSEEK_API_KEY=your_deepseek_api_key
     ```

2. **Optional `.files_to_organize`** (in the **base directory**):
   - Lists **exact filenames** or **relative paths** of files to be organized.
   - If absent/empty, **all** supported files (`.txt`, `.pdf`, `.docx`, `.png`, `.jpg`, `.jpeg`) are processed.

3. **Optional `.excluded_dirs`** (in the **base directory**):
   - Lists **directory names** to **exclude** from categorization.
   - These directories are neither scanned nor used as possible categories.

## Usage

1. **Organize Files**:
   ```bash
   python desk_organize.py /path/to/base_directory
   ```
   - Extracts text from each file and queries the DeepSeek API for a suitable **category**.
   - Moves files into category-named folders.
   - Logs moves in `rollback_log.json` for potential rollback.
   - Tags files in `file_tags.json` with the assigned category.

2. **Rollback**:
   ```bash
   python desk_organize.py /path/to/base_directory --rollback
   ```
   - Reads `rollback_log.json` and restores moved files to their original locations.
   - Removes `rollback_log.json` upon completion.

3. **Smart Tagging**:
   - After moving a file, the script adds a **tag** with the assigned category in `file_tags.json`.
   - You can add/remove/list/search tags programmatically by importing or extending the class:
     ```python
     from organize import FileOrganizer

     organizer = FileOrganizer("/path/to/base_directory")
     organizer.add_tag("C:/full/path/to/file.txt", "Research")
     print(organizer.list_file_tags("C:/full/path/to/file.txt"))
     # => ["Research", "<CategoryFromDeepSeek>"]
     ```
   - **Search by tag**:
     ```python
     results = organizer.search_by_tag("Research")
     print(results)  # => ["C:/full/path/to/file.txt", ...]
     ```

## Configuration Files

- **`.files_to_organize`**  
  ```text
  report.pdf
  notes.txt
  images/photo.jpg
  ```
  Only these files will be organized. If missing, **all** supported files are processed.

- **`.excluded_dirs`**  
  ```text
  old_projects
  private_docs
  ```
  Directories **excluded** from categorization.

- **`file_tags.json`** (Auto-generated)  
  A database of file paths → list-of-tags mappings.

- **`rollback_log.json`** (Auto-generated)  
  Records file moves from the last organization step for rollback.

## Supported File Types

- **TXT** (plain text)
- **PDF** (via PyMuPDF)
- **DOCX** (via `python-docx`)
- **PNG, JPG, JPEG** (via `pytesseract` for OCR)