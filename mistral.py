# main_mistral.py
import os
import json
import time
import requests
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from prompt import PROMPT_TEMPLATE  # Ensure this exists
import re
# -----------------
# 1. Load Environment Variables
# -----------------
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_URL = "https://api.mistral.ai/v1/chat/completions"

if not API_KEY:
    raise ValueError("❌ API_KEY not found. Please set it in the .env file.")

# -----------------
# 2. Helper Functions
# -----------------
def load_resume(file_path):
    """Load resume text from PDF/DOCX/TXT and clean it."""
    print(f"📄 Loading resume: {file_path}")
    start_time = time.time()
    
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith(".txt"):
        loader = TextLoader(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")
    
    docs = loader.load()
    
    text = "\n\n".join([d.page_content for d in docs])
    print(text)
    # Clean non-printable characters
    clean_text = re.sub(r'[^\x20-\x7E\n]', '', text)
    
    print(f"⏱ Resume loaded in {time.time() - start_time:.2f}s")
    return clean_text


def load_text(file_path):
    """Load JD text from DOCX/TXT."""
    print(f"📄 Loading JD: {file_path}")
    start_time = time.time()
    
    if file_path.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
        docs = loader.load()
        text = "\n\n".join([d.page_content for d in docs])
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    print(text)
    print(f"⏱ JD loaded in {time.time() - start_time:.2f}s")
    return text


def call_mistral_api(prompt: str):
    """Call Mistral API and return the response text."""
    print("🤖 Calling Mistral API...")
    start_time = time.time()
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "open-mistral-7b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 4000
    }
    
    response = requests.post(API_URL, headers=headers, json=data)
    print(f"⏱ API call completed in {time.time() - start_time:.2f}s | Status: {response.status_code}")
    
    if response.status_code != 200:
        print("❌ API call failed:", response.text)
        return None
    
    try:
        res_json = response.json()
        return res_json['choices'][0]['message']['content']
    except (json.JSONDecodeError, KeyError):
        print("❌ Failed to parse API response JSON")
        print(response.text)
        return None


def save_json_incremental(parsed_json, resume_file_path, folder="outputs"):
    """
    Save JSON with filename based on the resume PDF name.
    - First run: <pdf_name>_output.json
    - Subsequent runs: <pdf_name>_output2.json, <pdf_name>_output3.json, etc.
    """
    os.makedirs(folder, exist_ok=True)

    # Extract base name of the PDF without extension
    base_name = os.path.splitext(os.path.basename(resume_file_path))[0]
    base_file = f"{base_name}_output"

    # Check existing files starting with base_file
    existing_files = [
        f for f in os.listdir(folder)
        if f.startswith(base_file) and f.endswith(".json")
    ]
    
    if not existing_files:
        output_file = os.path.join(folder, f"{base_file}.json")
    else:
        # Get numbers from existing files
        numbers = []
        for f in existing_files:
            num_part = f.replace(base_file, "").replace(".json", "")
            if num_part.isdigit():
                numbers.append(int(num_part))
        next_number = max(numbers) + 1 if numbers else 2
        output_file = os.path.join(folder, f"{base_file}{next_number}.json")

    # Save JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(parsed_json, f, indent=2, ensure_ascii=False)

    print(f"✅ JSON saved successfully: {output_file}")



# -----------------
# 3. Main Logic
# -----------------
def main():
    jd_path = r"D:\RESUME_PARSING_MISTRAL\jds\Seniour_devops_.docx"
    resume_path = r"D:\RESUME_PARSING_MISTRAL\resume\George_bert.pdf"
    
    # Load files
    jd_text = load_text(jd_path).replace("\n", " ").replace('"', "'")
    print(jd_text)
    resume_text = load_resume(resume_path).replace("\n", " ").replace('"', "'")
    print(resume_text)
    # Format prompt
    print("📝 Formatting prompt...")
    start_time = time.time()
    formatted_prompt = PROMPT_TEMPLATE.replace("{jd}", jd_text).replace("{resume}", resume_text)
    print(f"⏱ Prompt formatted in {time.time() - start_time:.2f}s | Length: {len(formatted_prompt)} chars")
    
    # Call API
    response_text = call_mistral_api(formatted_prompt)
    
    if response_text:
        print("💾 Parsing response and saving JSON...")
        try:
            parsed_json = json.loads(response_text)
            save_json_incremental(parsed_json, resume_path)
        except json.JSONDecodeError:
            print("❌ Failed to parse JSON, raw response:")
            print(response_text)
    else:
        print("❌ No response from Mistral API")


# -----------------
# 4. Run
# -----------------
if __name__ == "__main__":
    total_start = time.time()
    print("🚀 Starting resume parsing...")
    main()
    print(f"🎉 Done! Total elapsed time: {time.time() - total_start:.2f}s")
