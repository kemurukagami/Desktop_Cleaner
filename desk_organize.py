import os
import shutil
import argparse
import time
import json
from dotenv import load_dotenv
import requests
import fitz  # PyMuPDF for PDF processing
from docx import Document  # Word document processing
import pytesseract  # OCR for images
from PIL import Image  # Image processing
from abc import ABC, abstractmethod

class ContentExtractor(ABC):
    @abstractmethod
    def extract(self, file_path):
        """Abstract method to extract content from a file."""
        pass

class TxtExtractor(ContentExtractor):
    def extract(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()

class PdfExtractor(ContentExtractor):
    def extract(self, file_path, max_pages=10):
        chunks = []
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc):
                if page_num >= max_pages:  # Limit to first max_pages pages
                    break
                text = page.get_text()
                chunks.append(text)  # Store each page as its own chunk
        return chunks

class DocxExtractor(ContentExtractor):
    def extract(self, file_path):
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

class ImageExtractor(ContentExtractor):
    def extract(self, file_path):
        return pytesseract.image_to_string(Image.open(file_path))

class FileOrganizer:
    def __init__(self, base_dir):
        self.base_dir = os.path.abspath(base_dir)
        self.load_api_key()
        self.existing_dirs = self.get_existing_directories()
        self.extractors = {
            "txt": TxtExtractor(),
            "pdf": PdfExtractor(),
            "docx": DocxExtractor(),
            "png": ImageExtractor(),
            "jpg": ImageExtractor(),
            "jpeg": ImageExtractor()
        }
        self.rollback_log = os.path.join(self.base_dir, "rollback_log.json")
        self.moved_files = []
    
    def load_api_key(self):
        """Loads DeepSeek API key from environment variables."""
        load_dotenv()
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found. Set DEEPSEEK_API_KEY in a .env file or environment variable.")
    
    def get_existing_directories(self):
        """Returns a list of existing subdirectories in the base directory."""
        return [d for d in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, d))]
    
    def categorize_text_with_deepseek(self, filename, text, retries=3, wait=5):
        """Uses DeepSeek API to determine a category for the file, with retry logic."""
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are an assistant that organizes files into directories."},
                {"role": "user", "content": f"Given the following document {filename} with text content:\n{text}\nExisting categories: {', '.join(self.existing_dirs) if self.existing_dirs else 'None'}\nShould this file belong to an existing category or should a new one be created (propose a new one if you have a more suitable/specific category)? If new, suggest a name. Give a single word response"}
            ]
        }

        for attempt in range(retries):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=20)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"].strip()
            except requests.exceptions.RequestException as e:
                print(f"DeepSeek API request failed: {e}. Retrying ({attempt+1}/{retries})...")
                time.sleep(wait)
        raise Exception("Failed after multiple retries due to API issues.")
    
    def move_file_to_category(self, file_path, category):
        """Moves the file to the appropriate category directory and logs the move for rollback."""
        category_path = os.path.join(self.base_dir, category)
        os.makedirs(category_path, exist_ok=True)
        new_path = os.path.join(category_path, os.path.basename(file_path))
        shutil.move(file_path, new_path)
        print(f"Moved {file_path} to {category}/")
        self.moved_files.append({"original": file_path, "new": new_path})
    
    def save_rollback_log(self):
        """Saves moved files to a log for rollback purposes."""
        with open(self.rollback_log, "w") as log_file:
            json.dump(self.moved_files, log_file, indent=4)
    
    def rollback_changes(self):
        """Moves files back to their original locations based on the rollback log."""
        if not os.path.exists(self.rollback_log):
            print("No rollback log found.")
            return
        
        with open(self.rollback_log, "r") as log_file:
            moved_files = json.load(log_file)
        
        for entry in moved_files:
            original_path = entry["original"]
            new_path = entry["new"]
            if os.path.exists(new_path):
                shutil.move(new_path, original_path)
                print(f"Rolled back {new_path} to {original_path}")
        
        os.remove(self.rollback_log)  # Remove log after rollback
    
    def organize_files(self):
        """Organizes all supported files in the directory."""
        for file_name in os.listdir(self.base_dir):
            file_path = os.path.join(self.base_dir, file_name)
            if os.path.isfile(file_path):
                ext = file_name.split(".")[-1].lower()
                if ext in self.extractors:
                    print(f"Processing {file_name}...")
                    text_content = self.extractors[ext].extract(file_path)
                    category = self.categorize_text_with_deepseek(file_name, text_content)
                    self.move_file_to_category(file_path, category)
                    self.existing_dirs = self.get_existing_directories()
                else:
                    print(f"Skipping unsupported file: {file_name}")
        self.save_rollback_log()
        print("Organization complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize files into categorized directories.")
    parser.add_argument("base_directory", type=str, help="Path to the directory containing files.")
    parser.add_argument("--rollback", action="store_true", help="Rollback the last organization operation.")
    args = parser.parse_args()
    
    organizer = FileOrganizer(args.base_directory)
    
    if args.rollback:
        organizer.rollback_changes()
    else:
        organizer.organize_files()