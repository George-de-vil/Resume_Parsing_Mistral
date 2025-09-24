# main_mistral.py
import os
import json
import time
import requests
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from prompt import PROMPT_TEMPLATE  # Ensure this exists

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
    """Load resume text from PDF/DOCX/TXT."""
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
    
    print(f"⏱ Resume loaded in {time.time() - start_time:.2f}s")
    return text


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


def save_json_incremental(parsed_json, folder="outputs", base_name="parsed_output"):
    """Save JSON with incremental numbering."""
    os.makedirs(folder, exist_ok=True)
    
    existing_files = [
        f for f in os.listdir(folder) if f.startswith(base_name) and f.endswith(".json")
    ]
    numbers = [
        int(f.replace(base_name + "_", "").replace(".json", ""))
        for f in existing_files if f.replace(base_name + "_", "").replace(".json", "").isdigit()
    ]
    next_number = max(numbers) + 1 if numbers else 1
    output_file = os.path.join(folder, f"{base_name}_{next_number}.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(parsed_json, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON saved successfully: {output_file}")


# -----------------
# 3. Main Logic
# -----------------
def main():
    jd_path = r"D:\RESUME_PARSING_MISTRAL\jds\Role.docx"
    resume_path = r"D:\RESUME_PARSING_MISTRAL\resume\Narender Tiparthi-8 years_Redacted.pdf"
    
    # Load files
    jd_text = load_text(jd_path).replace("\n", " ").replace('"', "'")
    resume_text = load_resume(resume_path).replace("\n", " ").replace('"', "'")
    
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
            save_json_incremental(parsed_json)
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
