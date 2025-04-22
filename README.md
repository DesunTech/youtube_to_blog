# YouTube-to-Blog POC

This is a Proof-of-Concept (POC) for a FastAPI and React application that takes a YouTube video URL, downloads the audio, transcribes it using OpenAI's Whisper model, and generates a blog post using the Google Gemini API.

## Features

* Downloads audio from YouTube using `pytube`
* Transcribes audio using `openai-whisper` (using `small.en` model for better quality)
* Uses `youtube-transcript-api` as a fallback if Whisper transcription fails
* Generates blog posts using the Google Gemini API (via its OpenAI-compatible endpoint)
* Customizable blog generation:
  * Target audience (beginners, intermediate, experts, general)
  * Writing tone (formal, conversational, professional, enthusiastic, technical)
  * Output format (Markdown, HTML)
* Modern React frontend with:
  * Real-time preview
  * Copy to clipboard
  * Download as file
  * Responsive design

## Setup and Running

### Prerequisites:

* Python 3.8+
* Node.js 16+
* `pip` (Python package installer)
* `ffmpeg`:
  * Ubuntu/Debian: `sudo apt update && sudo apt install ffmpeg`
  * macOS (Homebrew): `brew install ffmpeg`
  * Windows (Chocolatey): `choco install ffmpeg`
  * Windows (Scoop): `scoop install ffmpeg`

### Backend Setup:

1. **Clone the repository (if applicable):**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create and configure the environment file:**
   * Create a file named `.env` in the project root directory
   * Add your Google Gemini API key and optionally specify the model:
     ```dotenv
     GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
     GEMINI_MODEL_NAME=gemini-2.5-pro-exp-03-25 # Or another compatible model
     WHISPER_MODEL_NAME=small.en # Current default for better quality
     ```
   * Replace `YOUR_GEMINI_API_KEY_HERE` with your actual key

5. **Run the FastAPI server:**
   ```bash
   python main.py
   ```
   The server will start on `http://localhost:8000`

### Frontend Setup:

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   The frontend will start on `http://localhost:5173`

## Usage

1. Open your browser to `http://localhost:5173`
2. Paste a YouTube URL into the input field
3. Configure your blog post preferences:
   * Select target audience
   * Choose writing tone
   * Pick output format
4. Click "Generate Blog Post"
5. Once generated, you can:
   * Preview the content
   * Copy to clipboard
   * Download as file

## Project Structure

```
.
├── .env                # Environment variables (API keys, model names)
├── main.py            # FastAPI application code
├── requirements.txt    # Python dependencies
├── frontend/          # React frontend application
│   ├── src/          # Source code
│   ├── package.json  # Node.js dependencies
│   └── ...          # Other frontend files
└── README.md         # This file
```

## Known Issues

* Long processing times for larger videos
* Need for progress indication during processing
* Memory usage with larger models

For more details, check the GitHub issues page.