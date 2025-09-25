# app.py
import streamlit as st
from mistral import load_resume, load_text, call_mistral_api, save_json_incremental, PROMPT_TEMPLATE
import os
import json

st.set_page_config(page_title="Resume Parser with Mistral", layout="wide")
st.title("📄 Resume & JD Parser with Mistral AI")

# -----------------------
# 1. Upload Files
# -----------------------
jd_file = st.file_uploader("Upload Job Description (DOCX/TXT)", type=["docx", "txt"])
resume_file = st.file_uploader("Upload Resume (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])

if jd_file and resume_file:
    st.info("Files uploaded successfully. Processing...")

    # -----------------------
    # 2. Save uploaded files temporarily
    # -----------------------
    jd_path = f"temp_{jd_file.name}"
    resume_path = f"temp_{resume_file.name}"

    with open(jd_path, "wb") as f:
        f.write(jd_file.getbuffer())
    with open(resume_path, "wb") as f:
        f.write(resume_file.getbuffer())

    # -----------------------
    # 3. Load text from files
    # -----------------------
    jd_text = load_text(jd_path).replace("\n", " ").replace('"', "'")
    resume_text = load_resume(resume_path).replace("\n", " ").replace('"', "'")

    # -----------------------
    # 4. Prepare prompt
    # -----------------------
    formatted_prompt = PROMPT_TEMPLATE.replace("{jd}", jd_text).replace("{resume}", resume_text)
    st.write(f"📝 Prompt prepared (~{len(formatted_prompt)//4} tokens)")

    # -----------------------
    # 5. Call Mistral API
    # -----------------------
    with st.spinner("Calling Mistral API..."):
        response_text = call_mistral_api(formatted_prompt)

    if response_text:
        st.success("✅ API response received!")
        try:
            parsed_json = json.loads(response_text)
            st.json(parsed_json)  # Display JSON in Streamlit

            # Optional: save JSON locally
            save_json_incremental(parsed_json, resume_path)
            st.info("Response saved in outputs folder.")
        except json.JSONDecodeError:
            st.error("❌ Failed to parse JSON. Showing raw response:")
            st.text(response_text)
    else:
        st.error("❌ No response from Mistral API")
