📄 Resume Parsing with Mistral AI

This project is a resume parsing and job description (JD) matching system powered by Mistral AI and LangChain document loaders.
It loads resumes and job descriptions, sends them to Mistral’s LLM, and outputs a structured JSON for automated analysis.

🚀 Features

📂 Multi-format support: Load resumes in PDF, DOCX, or TXT.

📝 JD parsing: Works with DOCX and TXT job descriptions.

🤖 AI-powered analysis: Uses Mistral AI to process and structure resume–JD matches.

💾 Incremental JSON output: Saves results as parsed_output_1.json, parsed_output_2.json, …

⏱ Performance tracking: See timing logs for each step (loading, parsing, API call).

🔒 Secure API key handling: Managed via .env file.

🛠 Tech Stack

Python 3.10+

Mistral AI API (for LLM processing)

LangChain (document loaders only)

requests, dotenv, os, json, time

📂 Project Structure
resume_parsing_mistral/
├─ main_mistral.py        # Main script
├─ prompt.py              # Custom prompt template
├─ .env                   # API key stored here
├─ resume/                # Resumes (PDF/DOCX/TXT)
├─ jds/                   # Job descriptions (DOCX/TXT)
├─ outputs/               # Parsed JSON outputs

⚡ Setup & Usage
1. Clone the repository
git clone https://github.com/yourusername/resume-parsing-mistral.git
cd resume-parsing-mistral

2. Install dependencies
pip install -r requirements.txt

3. Add your Mistral API key

Create a .env file in the root directory:

API_KEY=your_mistral_api_key_here

4. Place your files

Put resumes in the resume/ folder

Put job descriptions in the jds/ folder

5. Run the script
python main_mistral.py

6. Get results

JSON files will be saved in the outputs/ folder.

📊 Example Output
{
  "name": "Narender Tiparthi",
  "experience": "8 years",
  "skills": ["Python", "SQL", "TensorFlow", "Kubernetes"],
  "matched_skills": ["Python", "SQL"]
}

🌟 Future Improvements

Add resume–JD matching score

Bulk parsing for multiple resumes at once

Support for more LLMs (OpenAI GPT, Claude, etc.)

Build a simple web dashboard (Flask/FastAPI)

📜 License

MIT License – free to use, modify, and share.

