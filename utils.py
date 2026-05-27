import os
import fitz  # PyMuPDF
import streamlit as st
from dotenv import load_dotenv
from tavily import TavilyClient
import google.generativeai as genai

# Load env variables for local development
load_dotenv()

# --- SECURE API KEY CONFIGURATION ---
# Pehle Streamlit Secrets check karega (Cloud ke liye), fir os.getenv (Local ke liye)
gemini_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
tavily_key = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")

if not gemini_key:
    st.error("Error: GEMINI_API_KEY missing! Set it in Streamlit Secrets or .env file.")
else:
    genai.configure(api_key=gemini_key)

# --- INITIALIZE THE PRODUCTION ENGINE ---
# Switch to the active and faster Gemini 2.5 architecture (No 'models/' prefix needed)
model = genai.GenerativeModel('gemini-2.5-flash')

if tavily_key:
    tavily = TavilyClient(api_key=tavily_key)
else:
    st.error("Error: TAVILY_API_KEY missing!")


def extract_text_from_pdf(pdf_file):
    text = ""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    for page in doc:
        text += page.get_text()
    return text


def extract_claims(text):
    prompt = f"""
    Extract factual claims from the text below.
    Focus ONLY on:
    - statistics
    - percentages
    - dates
    - financial figures
    - technical facts
    - numerical statements

    Return ONLY bullet points. Do not include any introductory or concluding text.

    TEXT:
    {text}
    """
    
    response = model.generate_content(prompt)
    output = response.text

    claims = [
        line.strip("-•* ").strip()
        for line in output.split("\n")
        if len(line.strip()) > 10
    ]
    return claims


def verify_claim(claim):
    # Dynamic year context injection for accuracy check
    search_query = f"{claim} current global data 2026"
    
    search_result = tavily.search(
        query=search_query,
        search_depth="advanced"
    )

    evidence = ""
    source_urls = []

    if "results" in search_result:
        for result in search_result["results"][:3]:
            url = result.get("url")
            source_urls.append(url)
            evidence += f"""
            Title: {result.get('title')}
            Content: {result.get('content')}
            URL: {url}
            \n"""

    prompt = f"""
    You are an elite, professional data-driven fact checker. Analyse the claim based STRICTLY on the live web evidence provided.

    CLAIM:
    {claim}

    WEB EVIDENCE:
    {evidence}

    Decide whether the claim is:
    - Verified (Matches live authoritative data)
    - Inaccurate (Contains outdated figures or partial truths)
    - False (Contradicted by data or no supporting evidence found)

    FORMAT RULES: Return data exactly in the format below without any extra text.

    Status: <Status Word Only>
    Explanation: <Clear explanation detailing the contradiction or verification using the sources>
    Correct Fact: <The accurate data from web evidence, or 'N/A' if Verified>
    """

    response = model.generate_content(prompt)
    return response.text, source_urls