# Desktop Cleaner

Desktop Cleaner is a Python project designed to organize files on your desktop into categorized directories. It uses various content extractors to read the content of different file types and categorizes them using the DeepSeek API.

## Features

- Extracts content from text files, PDF documents, Word documents, and images.
- Categorizes files based on their content using the DeepSeek API.
- Moves files into appropriate directories based on their categories.
- Supports chunked text processing for large documents.

## Requirements

- Python 3.7+
- `requests`
- `fitz` (PyMuPDF)
- `python-docx`
- `pytesseract`
- `Pillow`
- `python-dotenv`

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/kemurukagami/Desktop_Cleaner.git
    cd desktop_cleaner
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Set up the DeepSeek API key:
    - Create a .env file in the project directory.
    - Add your DeepSeek API key to the .env file:
        ```
        DEEPSEEK_API_KEY=your_api_key_here
        ```

## Usage

1. Run the script with the path to the directory containing the files you want to organize:
    ```sh
    python [desk_organize.py](./desk_organize.py) /path/to/your/desktop
    ```

2. The script will process the files in the specified directory, categorize them using the DeepSeek API, and move them into appropriate directories.

## Example

```sh
python desk_organize.py C:/Users/Isaac/OneDrive/Desktop
```

## Project Structure

desktop_cleaner/
│
├── desk_organize.py       # Main script for organizing files
├── requirements.txt       # List of required packages
├── .env                   # Environment file for storing API keys
└── README.md              # Project documentation