# 🇺🇸 TTB AI-Powered Alcohol Label Verification Portal
**Target Position:** IT Specialist (AI) — Treasury Shared Services (GS-15)

An AI-native, high-velocity decision support prototype designed to optimize label audit pipelines. By consolidating execution boundaries into a single-file Streamlit layout, the solution completely avoids the high total cost of ownership (TCO), maintenance overhead, and cross-origin security friction of multi-tier web infrastructure.

### 🏛️ Architectural Philosophy: AI-Native Simplicity
Instead of over-engineering a traditional, heavy multi-tier web stack (Java/Node/CORS infrastructure) for a prototype, this solution leverages an **AI-Native Single-File Architecture**. 

By consolidating the pipeline into a single, highly optimized Streamlit engine, we achieve:
- **Zero Configuration Friction:** Reviewers can run the entire system with two terminal commands. No separate backend/frontend builds required.
- **Maximum Velocity:** Production-grade UI components are tied directly to backend execution threads, cutting latency and eliminating network serialization bottlenecks.
- **Ultra-Low Maintenance:** It drastically lowers the total cost of ownership (TCO) for the Treasury's Common Services Center.

### 🧠 Stakeholder & Regulatory Compliance Matrix
- **Inference Latency Optimization (Sarah's Req):** Employs `gemini-2.5-flash` alongside strict, structured object schemas to secure predictable multi-modal extractions under 3.5 seconds—beating the legacy pilot failure threshold.
- **Deterministic Rule Enforcement (Jenny's Req):** Isolates vision extraction from compliance logic. Evaluates statutory requirements (27 CFR 16.21) using an immutable, hardcoded regex pattern to prevent LLM structural hallucinations and catch subtle title-case errors.
- **Algorithmic Nuance (Dave's Req):** Features Token-Sort normalization alongside Levenshtein Distance matrix valuations to calculate string similarity, letting the system tolerate stylistic punctuation and case differences.
- **Zero-Infrastructure Concurrent Pool (Janet's Req):** Utilizes Python's native `ThreadPoolExecutor` and `as_completed` loops to stream concurrent asynchronous network requests concurrently without requiring database or queue backends (Celery/Redis).

### 🚀 Setup & Execution Engine
1. **Initialize and Isolate Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Execute Automated Verification Suite (DevSecOps Readiness):**
   ```bash
   pytest -v test_app.py
   ```
3. **Launch Live Portal:**
   ```bash
   streamlit run app.py
   ```

### 🔒 Enterprise Zero-Trust & GovCloud Roadmap
- **Dynamic Authentication Gate (Marcus's Req):** Implements transient pass-through parsing using client browser memory headers in a secure Sidebar module. This eliminates administrative backend key leakage, accommodates network firewall isolation boundaries, and strictly adheres to federal data retention policies.
- **Air-Gapped Isolation Path:** The system architecture is built to pivot instantly from public web endpoints to an internal **Azure Government Private Link** or host a containerized open-source alternative (e.g., Llama-Vision via Ollama) inside an isolated, secure treasury network.
