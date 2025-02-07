import os
import shutil
import argparse
from dotenv import load_dotenv
import openai

class FileOrganizer:
    def __init__(self, base_dir):
        self.base_dir = os.path.abspath(base_dir)
        self.load_api_key()
        self.existing_dirs = self.get_existing_directories()
    
    def load_api_key(self):
        """Loads OpenAI API key from environment variables."""
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found. Set OPENAI_API_KEY in a .env file or environment variable.")
        openai.api_key = self.api_key
    
    def get_existing_directories(self):
        """Returns a list of existing subdirectories in the base directory."""
        return [d for d in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, d))]
    
    def extract_content(self, file_path):
        """Abstract method for extracting content from a file. To be implemented in subclasses."""
        raise NotImplementedError("Subclasses must implement extract_content.")
    
    def categorize_text_with_chatgpt(self, text):
        """Uses ChatGPT to determine a category for the text file."""
        prompt = f"""Given the following text:
        """
        {text}
        """
        Existing categories: {', '.join(self.existing_dirs) if self.existing_dirs else 'None'}
        Should this file belong to an existing category or should a new one be created? If new, suggest a name."""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are an assistant that organizes files into directories."},
                      {"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"].strip()
    
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
                category = self.categorize_text_with_chatgpt(text_content)
                self.move_file_to_category(file_path, category)
                self.existing_dirs = self.get_existing_directories()  # Refresh after adding a new directory
        print("Organization complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize text files into categorized directories.")
    parser.add_argument("base_directory", type=str, help="Path to the directory containing text files.")
    args = parser.parse_args()
    organizer = TxtFileOrganizer(args.base_directory)
    organizer.organize_files()
