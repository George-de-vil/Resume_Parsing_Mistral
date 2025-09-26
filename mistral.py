# mistral.py
import os
import json
import time
import requests
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from prompt import PROMPT_TEMPLATE
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
def incremental_save(text, base_name, folder="outputs", suffix=""):
    """Save text incrementally with _1, _2, _3..."""
    os.makedirs(folder, exist_ok=True)
    file_base = f"{base_name}{('_' + suffix) if suffix else ''}"

    # Find existing files
    existing_files = [f for f in os.listdir(folder) if f.startswith(file_base) and f.endswith(".txt")]
    
    if not existing_files:
        file_name = f"{file_base}.txt"
    else:
        numbers = []
        for f in existing_files:
            num_part = f.replace(file_base, "").replace(".txt", "")
            if num_part.startswith("_") and num_part[1:].isdigit():
                numbers.append(int(num_part[1:]))
        next_number = max(numbers) + 1 if numbers else 1
        file_name = f"{file_base}_{next_number}.txt"

    file_path = os.path.join(folder, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    return file_path

def load_file(file_path):
    """Load resume or JD from PDF/DOCX/TXT and return text."""
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
    clean_text = re.sub(r'[^\x20-\x7E\n]', '', text)
    return clean_text

def call_mistral_api(prompt: str):
    """Call Mistral API and return response text."""
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
    if response.status_code != 200:
        print(f"\033[91m❌ API call failed:\033[0m {response.text}")
        return None
    try:
        res_json = response.json()
        return res_json['choices'][0]['message']['content']
    except (json.JSONDecodeError, KeyError):
        print("\033[91m❌ Failed to parse API response JSON\033[0m")
        return None

def save_json_incremental(parsed_json, base_name, folder="outputs"):
    """Save JSON incrementally and also parsed JD/Resume text."""
    os.makedirs(folder, exist_ok=True)
    
    # Incremental JSON file
    json_base = f"{base_name}_output"
    existing_json = [f for f in os.listdir(folder) if f.startswith(json_base) and f.endswith(".json")]
    if not existing_json:
        json_file = os.path.join(folder, f"{json_base}.json")
    else:
        numbers = []
        for f in existing_json:
            num_part = f.replace(json_base, "").replace(".json", "")
            if num_part.startswith("_") and num_part[1:].isdigit():
                numbers.append(int(num_part[1:]))
        next_number = max(numbers) + 1 if numbers else 1
        json_file = os.path.join(folder, f"{json_base}_{next_number}.json")
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(parsed_json, f, indent=2, ensure_ascii=False)

    # Incremental parsed JD & Resume text files
    parsed_jd_text = parsed_json.get("ParsedJD", "")
    parsed_resume_text = parsed_json.get("ParsedResume", "")
    
    if parsed_jd_text:
        incremental_save(parsed_jd_text, base_name, folder, suffix="parsed_jd")
    if parsed_resume_text:
        incremental_save(parsed_resume_text, base_name, folder, suffix="parsed_resume")

    return json_file

# -----------------
# 3. Terminal Styling Functions
# -----------------
def print_stage(title, content="", file_path="", time_taken=None):
    cyan = "\033[1;36m"
    green = "\033[92m"
    yellow = "\033[93m"
    blue = "\033[1;34m"
    reset = "\033[0m"

    print(f"{cyan}────────────────────────────────────────{reset}")
    print(f"{yellow}{title}{reset}")
    if content:
        print(content)
    if file_path:
        print(f"✅  Saved at: {green}{file_path}{reset}")
    if time_taken:
        print(f"⏱  Time taken: {cyan}{time_taken:.2f}s{reset}")
    print(f"{cyan}────────────────────────────────────────{reset}")

# -----------------
# 4. Main Logic
# -----------------
def main():
    total_start = time.time()
    cyan = "\033[1;36m"
    reset = "\033[0m"
    print(f"{cyan}╔════════════════════════════════════════════════════════╗{reset}")
    print(f"{cyan}║ 🚀  RESUME PARSING PIPELINE STARTED                     ║{reset}")
    print(f"{cyan}╚════════════════════════════════════════════════════════╝{reset}\n")

    jd_path = r"jds/java_deveploper.docx"
    resume_path = r"resume/George_bert.pdf"

    # JD Extraction
    start = time.time()
    jd_text = load_file(jd_path)
    jd_file = incremental_save(jd_text, os.path.splitext(os.path.basename(jd_path))[0], folder="extracted_texts")
    print_stage("📄 JD EXTRACTION", file_path=jd_file, time_taken=time.time() - start)

    # Resume Extraction
    start = time.time()
    resume_text = load_file(resume_path)
    resume_file = incremental_save(resume_text, os.path.splitext(os.path.basename(resume_path))[0], folder="extracted_texts")
    print_stage("📄 RESUME EXTRACTION", file_path=resume_file, time_taken=time.time() - start)

    # Mistral Parsing
    start = time.time()
    formatted_prompt = PROMPT_TEMPLATE.replace("{jd}", jd_text.replace("\n"," ").replace('"',"'")) \
                                      .replace("{resume}", resume_text.replace("\n"," ").replace('"',"'"))
    print(f"\033[1;33m🤖 MISTRAL AI PARSING...\033[0m")
    response_text = call_mistral_api(formatted_prompt)

    if response_text:
        try:
            parsed_json = json.loads(response_text)
            output_file = save_json_incremental(parsed_json, os.path.splitext(os.path.basename(resume_path))[0])
            print_stage("🎯 PARSING COMPLETED", file_path=output_file, time_taken=time.time() - start)
        except json.JSONDecodeError:
            raw_file = incremental_save(response_text, os.path.splitext(os.path.basename(resume_path))[0], folder="outputs", suffix="raw_response")
            print(f"\033[91m⚠️ Failed to parse JSON. Raw response saved: {raw_file}{reset}")
    else:
        print(f"\033[91m❌ No response from Mistral API{reset}")

    print(f"{cyan}╔════════════════════════════════════════════════════════╗{reset}")
    print(f"{cyan}║ ✅  PIPELINE COMPLETED SUCCESSFULLY                     ║{reset}")
    print(f"{cyan}║ ⏱  Total Pipeline Time: {reset}\033[93m {time.time() - total_start:.2f}s \033[0m{' '*(15-len(str(time.time()-total_start)))}║")
    print(f"{cyan}╚════════════════════════════════════════════════════════╝{reset}\n")

# -----------------
# 5. Run
# -----------------
if __name__ == "__main__":
    main()
