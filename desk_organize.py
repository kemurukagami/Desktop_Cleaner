import openai

# Set your API key
openai.api_key = "your_openai_api_key"

def classify_file_content(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a file categorization assistant."},
                  {"role": "user", "content": f"Classify this file content: {text}"}]
    )
    return response["choices"][0]["message"]["content"]

# Example usage
sample_text = "This is a project report about AI and deep learning."
category = classify_file_content(sample_text)
print(f"Category: {category}")
