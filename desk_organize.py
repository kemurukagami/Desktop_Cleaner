import os
import shutil
import argparse
import time
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
    def extract(self, file_path, max_pages=5, max_chars=2000, max_chunk_size=1000):
        text = ""
        chunks = []
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc):
                if page_num >= max_pages:  # Limit pages to avoid too much text
                    break
                text += page.get_text()
                if len(text) > max_chars:
                    text = text[:max_chars]  # Truncate if too long
                chunks.extend([text[i:i + max_chunk_size] for i in range(0, len(text), max_chunk_size)])
                text = ""  # Reset text after adding to chunks
        return chunks if len(chunks) > 1 else text

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
                print(response.json()["choices"][0]["message"]["content"].strip())
                return response.json()["choices"][0]["message"]["content"].strip()
            except requests.exceptions.RequestException as e:
                print(f"DeepSeek API request failed: {e}. Retrying ({attempt+1}/{retries})...")
                time.sleep(wait)
        raise Exception("Failed after multiple retries due to API issues.")
    
    def move_file_to_category(self, file_path, category):
        """Moves the file to the appropriate category directory."""
        category_path = os.path.join(self.base_dir, category)
        os.makedirs(category_path, exist_ok=True)
        shutil.move(file_path, os.path.join(category_path, os.path.basename(file_path)))
        print(f"Moved {file_path} to {category}/")
    
    def organize_files(self):
        """Organizes all supported files in the directory."""
        for file_name in os.listdir(self.base_dir):
            file_path = os.path.join(self.base_dir, file_name)
            if os.path.isfile(file_path):
                ext = file_name.split(".")[-1].lower()
                if ext in self.extractors:
                    print(f"Processing {file_name}...")
                    text_content = self.extractors[ext].extract(file_path)
                    if isinstance(text_content, list):  # Handle chunked text
                        categories = []
                        for chunk in text_content:
                            category = self.categorize_text_with_deepseek(file_name, chunk)
                            categories.append(category)
                        category = max(set(categories), key=categories.count)  # Choose most common category
                    else:
                        category = self.categorize_text_with_deepseek(file_name, text_content)
                    self.move_file_to_category(file_path, category)
                    self.existing_dirs = self.get_existing_directories()
                else:
                    print(f"Skipping unsupported file: {file_name}")
        print("Organization complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize files into categorized directories.")
    parser.add_argument("base_directory", type=str, help="Path to the directory containing files.")
    args = parser.parse_args()
    organizer = FileOrganizer(args.base_directory)
    organizer.organize_files()
