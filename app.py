import streamlit as st
import PyPDF2
import json
import requests

st.set_page_config(page_title="CV Fit: AI ATS Simulator", layout="wide")
st.title("CV Fit: AI ATS Simulator")

# Load API Key securely
api_key = st.secrets["GEMINI_API_KEY"]

col1, col2 = st.columns(2)

with col1:
    st.header("1. Upload Your CV")
    job_desc = st.text_area("Job Description (حط الإعلان هنا)", height=200)
    uploaded_file = st.file_uploader("Upload CV (PDF)", type=["pdf"])
    analyze_btn = st.button("Analyze CV", use_container_width=True)

with col2:
    st.header("2. ATS Results")
    if analyze_btn:
        if not uploaded_file or not job_desc:
            st.warning("Please upload a cv and paste a Job Description first.")
        else:
            with st.spinner("AI is analyzing your CV..."):
                reader = PyPDF2.PdfReader(uploaded_file)
                cv_text = "".join([page.extract_text() for page in reader.pages])

                prompt = f"""
                Act as a strict ATS software. Analyze this CV against the Job Description.
                Return ONLY a valid JSON object with no markdown formatting. The JSON must have these keys:
                "match_rate": an integer between 0 and 100,
                "missing_keywords": an array of max 6 important missing skills/keywords,
                "strengths": an array of max 6 strong matching skills.

                Job Description:
                {job_desc}

                CV:
                {cv_text}
                """

                # Updated request headers for AQ format keys
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                data = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ]
                }

                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    res_json = response.json()
                    result_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    result_text = result_text.replace("```json", "").replace("```", "").strip()
                    result = json.loads(result_text)

                    st.subheader(f"Match Rate: {result.get('match_rate', 0)}%")
                    st.progress(result.get('match_rate', 0) / 100)

                    st.write("### Missing Keywords")
                    for kw in result.get('missing_keywords', []):
                        st.error(kw)

                    st.write("### Strengths")
                    for st_point in result.get('strengths', []):
                        st.success(st_point)
                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")
