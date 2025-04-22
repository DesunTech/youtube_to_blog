# Technical Context: YouTube-to-Blog Generator

## 1. Proposed Technology Stack (Based on PRD)
- **Frontend:** React, Tailwind CSS
- **Backend:** Python (FastAPI) - Confirmed due to ML/Whisper/LLM library support.
- **Transcription Service:**
    - **Primary:** Self-hosted Whisper (OpenAI's open-source model) - Targeting `tiny` or `base` models initially. Requires local setup/deployment.
    - **Fallback:** YouTube auto-caption extraction via `youtube-transcript-api` library (Python).
- **AI Blog Generation (LLM):**
    - **Primary:** **Google Gemini (e.g., `gemini-2.0-flash`, `gemini-1.5-flash`)** accessed via its **OpenAI-compatible REST API endpoint** (`https://generativelanguage.googleapis.com/v1beta/openai/`) using a user-provided API key. Utilizes the available free tier.
    - **Fallback (Free):** **Use a free model available via OpenRouter** (e.g., Mistral 7B Instruct, Gemma 7B, etc., depending on availability and limits on their free tier). Requires an OpenRouter API key and interaction via their OpenAI-compatible endpoint.
- **Temporary Storage:** Redis (for caching transcriptions during processing).
- **YouTube Audio Download:** `pytube` (or similar Python library).
- **Optional:** Grammar/Readability Check: LanguageTool API (open-source) or Grammarly free tier API (if available).

## 2. Development & Deployment
- **Hosting:** Cloud hosting required for backend (FastAPI + Redis). **Self-hosting Whisper (`tiny`/`base`) requires careful consideration of CPU/GPU resources.** **Using OpenRouter fallback requires managing their API key and understanding their free tier limits/availability.** Containerized deployment (Docker) recommended for backend, Whisper, and Ollama components.
- **Source Control:** Git (repository TBD).
- **Dependency Management:** pip/poetry (Python).
- **API Communication:** RESTful APIs for frontend-backend. Backend uses REST/SDK calls to Gemini API and local Ollama API.

## 3. Technical Constraints & Considerations
- **Free Tier Limits:**
    - *Gemini API:* Generous free tier exists, but usage beyond limits incurs costs. Rate limits (RPM/TPM) apply.
    - *`youtube-transcript-api` (Fallback Transcription):* Potential rate limits or blocks (may require proxies).
- **Whisper Resource Needs (Self-Hosted):** `tiny`/`base` models require ~1GB VRAM for GPU or can run on CPU (slower). Hosting costs depend on chosen infrastructure.
- **Fallback LLM Resource Needs (Self-Hosted):** Quantized models (`Mistral-7B`, `Phi-3-mini`) are designed for lower resources, but still need sufficient RAM (8-16GB+) and perform much better with GPU VRAM (4-8GB+ depending on quantization). CPU execution is possible but slow.
- **Fallback LLM (OpenRouter):** Performance/availability depends on OpenRouter's infrastructure and their free tier policies. Rate limits will apply.
- **Transcription Accuracy:** Whisper (`tiny`/`base`) quality is good. YouTube captions (fallback) quality is highly variable. **Post-processing crucial.**
- **Blog Generation Quality:** Gemini models are highly capable. Fallback OSS models (Mistral/Phi-3 small versions) will likely be less capable at matching complex tone/style instructions and generating highly nuanced, human-like text compared to Gemini.
- **Video Length Limit:** Initial 1-hour limit impacts processing time and resource usage for transcription.
- **Human-like Output:** Requires sophisticated prompt engineering for the LLM and potentially post-processing rules to avoid AI detection.
- **Scalability:** Transcription (especially Whisper) can be resource-intensive. Need a scalable deployment strategy (e.g., containerization, serverless functions for processing tasks) if high concurrency is expected.
- **Security:** Input sanitization (URL, preferences), HTTPS everywhere, secure handling of any potential API keys.
- **No Persistent User Data:** Transcriptions and generated blogs should be handled ephemerally.

## 4. Key Dependencies
- `openai-whisper` Python library.
- `ffmpeg` (system dependency for Whisper).
- `pytube` (or similar) Python library for YouTube audio download.
- `youtube-transcript-api` Python library (for fallback transcription).
- **`openai` Python library (for interacting with Gemini's OpenAI-compatible API).**
- **An OpenRouter API Key (managed via .env).** # Note: OpenAI library can interact with OpenRouter endpoint.
- Redis instance + Python client (`redis-py`).
- Optional: Grammar checking API/library.