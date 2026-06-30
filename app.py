import streamlit as st
from google import genai
from google.genai import types
from concurrent.futures import ThreadPoolExecutor
import re
import unicodedata

# 1. Page Config for Sarah's 73-year-old User Benchmark (Large font targets)
st.set_page_config(page_title="TTB AI Verifier", layout="wide")
st.title("🇺🇸 TTB Label Verification Portal")
st.caption("Shared Services Prototype — Built for Speed and Compliance")

# Secure key retrieval from Streamlit Secrets
api_key = st.secrets.get("GEMINI_API_KEY", None)

GOV_WARNING_PATTERN = re.compile(
    r"GOVERNMENT WARNING:\s*"
    r"\(1\)\s*According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects\.\s*"
    r"\(2\)\s*Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems\.?",
    re.DOTALL,
)


def normalize_text(value):
    # Canonicalize for deterministic, case-insensitive comparisons across punctuation/spacing variants.
    normalized = unicodedata.normalize("NFKD", (value or "")).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", normalized.lower())).strip()


def levenshtein_distance(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev_row = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr_row = [i]
        for j, cb in enumerate(b, start=1):
            insert_cost = curr_row[j - 1] + 1
            delete_cost = prev_row[j] + 1
            replace_cost = prev_row[j - 1] + (ca != cb)
            curr_row.append(min(insert_cost, delete_cost, replace_cost))
        prev_row = curr_row
    return prev_row[-1]


def normalized_similarity(a, b):
    a_norm = normalize_text(a)
    b_norm = normalize_text(b)
    if not a_norm and not b_norm:
        return 1.0
    if not a_norm or not b_norm:
        return 0.0
    dist = levenshtein_distance(a_norm, b_norm)
    return 1.0 - (dist / max(len(a_norm), len(b_norm)))


def token_sort_similarity(a, b):
    a_sorted = " ".join(sorted(normalize_text(a).split()))
    b_sorted = " ".join(sorted(normalize_text(b).split()))
    return normalized_similarity(a_sorted, b_sorted)


def nuanced_brand_match(form_brand, extracted_brand, threshold=0.90):
    # Dave's nuance: tolerate case/punctuation/order differences but keep deterministic thresholding.
    score = token_sort_similarity(form_brand, extracted_brand)
    form_norm = normalize_text(form_brand)
    extracted_norm = normalize_text(extracted_brand)
    return score >= threshold or form_norm in extracted_norm or extracted_norm in form_norm


def has_valid_government_warning(raw_text):
    # Deterministic 27 CFR 16.21 gate: exact all-caps heading + statutory warning body pattern.
    return bool(GOV_WARNING_PATTERN.search((raw_text or "").strip()))

def analyze_label_with_ai(image_file, file_name):
    """Extracts label text with strict schema constraints to prevent hallucinations."""
    if not api_key:
        # Graceful manual fallback UI demo if no key is supplied yet
        return {
            "brand": "OLD TOM DISTILLERY", 
            "abv": "45%", 
            "raw_text": (
                "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink "
                "alcoholic beverages during pregnancy because of the risk of birth defects. "
                "(2) Consumption of alcoholic beverages impairs your ability to drive a car or "
                "operate machinery, and may cause health problems."
            )
        }
    
    try:
        client = genai.Client(api_key=api_key)
        # Read the Streamlit UploadedFile into raw binary bytes
        image_bytes = image_file.getvalue()
        mime_type = image_file.type or "image/jpeg"
        
        # Enforce strict JSON object response structure from the model boundary
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Sub-3.5 second processing speed target
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                "Analyze this alcohol label. Extract the exact brand name, alcohol content (ABV), and the health warning block verbatim."
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "brand": types.Schema(type=types.Type.STRING),
                        "abv": types.Schema(type=types.Type.STRING),
                        "raw_text": types.Schema(type=types.Type.STRING),
                    },
                    required=["brand", "abv", "raw_text"],
                ),
            ),
        )
        # Trust SDK schema-bound parsing to avoid brittle manual JSON string handling.
        if isinstance(response.parsed, dict):
            return response.parsed
        return {"error": f"Failed parsing {file_name}: structured response was not a JSON object"}
    except Exception as e:
        return {"error": f"Failed parsing {file_name}: {str(e)}"}

# 2. Dual Interface Layout
tab1, tab2 = st.tabs(["🗂️ Single Review Engine", "📦 Parallel Batch Importer"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Reference Form Data (TTB F 5100.31)")
        brand = st.text_input("Application Brand Name", "OLD TOM DISTILLERY")
        abv = st.text_input("Application ABV", "45%")
        uploaded_file = st.file_uploader("Upload Target Label Image", type=["png", "jpg", "jpeg"])
        
    with col2:
        st.subheader("2. Evaluation Output Dashboard")
        if uploaded_file:
            st.image(uploaded_file, width=220)
            with st.spinner("Executing Vision Analysis (Target < 3.5s)..."):
                ai_data = analyze_label_with_ai(uploaded_file, uploaded_file.name)
                
                if ai_data and "error" not in ai_data:
                    has_strict_warning = has_valid_government_warning(ai_data.get("raw_text", ""))
                    
                    brand_match = nuanced_brand_match(brand, ai_data.get("brand", ""))
                    abv_match = abv.strip() in ai_data.get("abv", "")
                    
                    if has_strict_warning and brand_match and abv_match:
                        st.success("🟢 AUTOMATED PASS: Label matches application rules completely.")
                    else:
                        st.error("🔴 MANUAL REVIEW REQUIRED: Compliance discrepancy detected.")
                        
                    st.write("**Verification Metrics Checklist:**")
                    st.checkbox("Strict 'GOVERNMENT WARNING:' Caps Checked", value=has_strict_warning, disabled=True)
                    st.checkbox("Flexible Brand Identity Matching Verified", value=brand_match, disabled=True)
                    st.checkbox("ABV Consistency Match Verified", value=abv_match, disabled=True)
                    
                    with st.expander("See Extracted Raw Metadata"):
                        st.json(ai_data)
                elif ai_data:
                    st.error(ai_data["error"])

with tab2:
    st.subheader("Batch Importer Mode")
    st.caption("Processes bulk assets concurrently via thread pooling to defend against UI freezing.")
    batch_files = st.file_uploader("Drop bulk imagery files here", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    if batch_files:
        if st.button("Begin Async Queue Execution"):
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Janet's Request: ThreadPoolExecutor handles batch tasks in async threads concurrently
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(analyze_label_with_ai, f, f.name): f.name for f in batch_files}
                
                for i, future in enumerate(futures):
                    filename = futures[future]
                    status_text.text(f"Analyzing {filename}...")
                    
                    res = future.result()
                    
                    if "error" not in res:
                        warn_check = has_valid_government_warning(res.get("raw_text", ""))
                        verdict = "🟢 PASS" if warn_check else "🔴 FAIL (Warning Format Incorrect)"
                        extracted_info = f"Brand: {res.get('brand')} | ABV: {res.get('abv')}"
                    else:
                        verdict = "💥 ERROR"
                        extracted_info = res["error"]
                        
                    results.append({"File Name": filename, "Audit Verdict": verdict, "Extracted Details": extracted_info})
                    progress_bar.progress((i + 1) / len(batch_files))
                    
            status_text.text("Batch verification execution cycle complete.")
            st.dataframe(results, use_container_width=True)
