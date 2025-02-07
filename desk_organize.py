import os
import shutil
import argparse
import time
from dotenv import load_dotenv
import requests

class FileOrganizer:
    def __init__(self, base_dir):
        self.base_dir = os.path.abspath(base_dir)
        self.load_api_key()
        self.existing_dirs = self.get_existing_directories()
    
    def load_api_key(self):
        """Loads DeepSeek API key from environment variables."""
        load_dotenv()
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found. Set DEEPSEEK_API_KEY in a .env file or environment variable.")
    
    def get_existing_directories(self):
        """Returns a list of existing subdirectories in the base directory."""
        return [d for d in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, d))]
    
    def extract_content(self, file_path):
        """Abstract method for extracting content from a file. To be implemented in subclasses."""
        raise NotImplementedError("Subclasses must implement extract_content.")
    
    def categorize_text_with_deepseek(self, text, retries=3, wait=5):
        """Uses DeepSeek API to determine a category for the text file, with retry logic."""
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {
            "model": "deepseek-chat",  # Adjust model as needed
            "messages": [
                {"role": "system", "content": "You are an assistant that organizes files into directories."},
                {"role": "user", "content": f"Given the following text:\n{text}\nExisting categories: {', '.join(self.existing_dirs) if self.existing_dirs else 'None'}\nShould this file belong to an existing category or should a new one be created? If new, suggest a name. Give a single word response, no more no less"}
            ]
        }
        
        print("Sending to DeepSeek API:")
        print(data["messages"][1]["content"])

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
        """Moves the file to the appropriate category directory."""
        category_path = os.path.join(self.base_dir, category)
        os.makedirs(category_path, exist_ok=True)
        shutil.move(file_path, os.path.join(category_path, os.path.basename(file_path)))
        print(f"Moved {file_path} to {category}/")
    
    def organize_files(self):
        """Abstract method for organizing files. To be implemented in subclasses."""
        raise NotImplementedError("Subclasses must implement organize_files.")

class TxtFileOrganizer(FileOrganizer):
    def extract_content(self, file_path):
        """Reads text content from a .txt file."""
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    
    def organize_files(self):
        """Scans and organizes .txt files in a directory."""
        for file_name in os.listdir(self.base_dir):
            file_path = os.path.join(self.base_dir, file_name)
            if os.path.isfile(file_path) and file_name.endswith(".txt"):
                print(f"Processing {file_name}...")
                text_content = self.extract_content(file_path)
                category = self.categorize_text_with_deepseek(text_content)
                self.move_file_to_category(file_path, category)
                self.existing_dirs = self.get_existing_directories()  # Refresh after adding a new directory
        print("Organization complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize text files into categorized directories.")
    parser.add_argument("base_directory", type=str, help="Path to the directory containing text files.")
    args = parser.parse_args()
    organizer = TxtFileOrganizer(args.base_directory)
    organizer.organize_files()