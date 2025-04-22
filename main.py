# main.py
import os
import tempfile
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
# from pytube import YouTube # Commented out, replaced by yt-dlp
import yt_dlp # Import yt-dlp
import whisper
from openai import OpenAI
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound # Import for fallback
import re

# --- Configuration & Setup ---
load_dotenv() # Load environment variables from .env file

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants ---
# Use a small, efficient model for the POC, running on CPU
# Ensure ffmpeg is installed: sudo apt update && sudo apt install ffmpeg
# Or on macOS: brew install ffmpeg
WHISPER_MODEL_NAME = "small.en"  # Options: tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large-v2, large-v3
# Default model if not specified in .env
DEFAULT_GEMINI_MODEL = "gemini-2.5-pro-exp-03-25"
# Read model name from environment variable, fallback to default
GEMINI_MODEL_TO_USE = os.getenv("GEMINI_MODEL_NAME", DEFAULT_GEMINI_MODEL)
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/openai/"

# --- OpenRouter Fallback Configuration ---
OPENROUTER_API_KEY_ENV_VAR = "OPENROUTER_API_KEY" # Environment variable name
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "mistralai/mistral-7b-instruct:free" # Example free model
# Read OpenRouter model name from environment variable, fallback to default
OPENROUTER_MODEL_TO_USE = os.getenv("OPENROUTER_MODEL_NAME", DEFAULT_OPENROUTER_MODEL)

AUDIO_DOWNLOAD_DIR = tempfile.gettempdir() # Use system's temp directory

# --- FastAPI App Initialization ---
app = FastAPI(
    title="YouTube-to-Blog POC",
    description="Proof-of-concept API to transcribe YouTube videos and generate summaries.",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Helper Functions ---

def download_audio(video_id: str) -> str | None:
    """Downloads the audio from a YouTube video ID using yt-dlp."""
    yt_url = f"https://www.youtube.com/watch?v={video_id}"
    # Define filename using video_id within the temp directory
    # yt-dlp might append its own extension based on format
    output_template = os.path.join(AUDIO_DOWNLOAD_DIR, f"{video_id}.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best', # Select best audio quality
        'outtmpl': output_template, # Set output path and filename template
        'noplaylist': True, # Ensure only single video is downloaded
        'quiet': True, # Suppress console output from yt-dlp
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio', # Extract audio using ffmpeg
            'preferredcodec': 'mp3', # Prefer mp3 format (adjust if needed)
            'preferredquality': '192', # Set audio quality
        }],
    }

    try:
        logger.info(f"Attempting to download audio using yt-dlp for: {yt_url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            error_code = ydl.download([yt_url])
            if error_code != 0:
                 logger.error(f"yt-dlp download failed with error code: {error_code} for {video_id}")
                 return None

            # yt-dlp replaces %(ext)s after download, we need the final path
            # Assuming mp3 as the preferred codec
            expected_path = os.path.join(AUDIO_DOWNLOAD_DIR, f"{video_id}.mp3")
            if os.path.exists(expected_path):
                logger.info(f"Audio downloaded successfully via yt-dlp to: {expected_path}")
                return expected_path
            else:
                 # Fallback check if format wasn't mp3 (e.g., m4a, opus) - more robust check needed for production
                 logger.warning(f"Expected mp3 path not found, checking common alternatives for {video_id}")
                 for ext in ['m4a', 'opus', 'webm', 'wav']:
                      alt_path = os.path.join(AUDIO_DOWNLOAD_DIR, f"{video_id}.{ext}")
                      if os.path.exists(alt_path):
                           logger.info(f"Audio downloaded successfully via yt-dlp to: {alt_path}")
                           return alt_path
                 logger.error(f"Downloaded file not found after yt-dlp run for {video_id} at expected paths.")
                 return None

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"yt-dlp DownloadError for {video_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"General error downloading audio with yt-dlp for {video_id}: {e}")
        return None

def transcribe_audio_with_whisper(audio_path: str) -> str | None:
    """Transcribes the audio file using the primary Whisper method."""
    # Separate function for clarity
    try:
        logger.info(f"Loading Whisper model: {WHISPER_MODEL_NAME}")
        # Load model once - consider moving outside function if performance becomes issue
        # For POC, loading here is fine. For production, consider loading once at startup.
        model = whisper.load_model(WHISPER_MODEL_NAME)
        logger.info(f"Transcribing audio file with Whisper: {audio_path}...")
        result = model.transcribe(audio_path, fp16=False) # fp16=False for CPU
        transcription = result["text"]
        logger.info("Whisper transcription complete.")
        return transcription
    except Exception as e:
        logger.error(f"Error transcribing audio {audio_path} with Whisper: {e}")
        return None
    finally:
        # Clean up the downloaded audio file after attempting transcription
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logger.info(f"Cleaned up temporary audio file: {audio_path}")
            except OSError as e:
                logger.error(f"Error deleting temporary file {audio_path}: {e}")

def get_youtube_captions(video_id: str) -> str | None:
    """Fetches YouTube captions using the fallback youtube-transcript-api method."""
    try:
        logger.info(f"Attempting to fetch YouTube captions for video ID: {video_id}...")
        # Fetch available transcripts, prioritizing English ('en')
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en'])

        # Fetch the actual transcript data
        transcript_data = transcript.fetch()

        # Combine the text parts into a single string
        full_transcript = " ".join([item.text for item in transcript_data])
        logger.info(f"Successfully fetched YouTube captions for video ID: {video_id}")
        return full_transcript

    except TranscriptsDisabled:
        logger.warning(f"Transcripts are disabled for video ID: {video_id}")
        return None
    except NoTranscriptFound:
        logger.warning(f"No English transcript found for video ID: {video_id}")
        # Optionally, you could try fetching auto-generated captions explicitly here
        # try:
        #    transcript = transcript_list.find_generated_transcript(['en'])
        #    # ... fetch and process ...
        # except NoTranscriptFound:
        #    logger.warning(f"No auto-generated English transcript found either.")
        #    return None
        return None
    except Exception as e:
        logger.error(f"Error fetching YouTube captions for {video_id}: {e}")
        return None

def generate_blog_post(transcription: str,
                       output_format: str = "markdown",
                       tone: str | None = None,
                       audience: str | None = None) -> str | None:
    """
    Generates a structured blog post from a transcription using the configured LLM API
    (Gemini primary, OpenRouter fallback), applying optional tone and audience guidance,
    in the specified output format (markdown or html).
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    blog_post = None
    llm_method = "unknown" # Track which LLM succeeded

    # --- Dynamically build the system prompt ---
    prompt_lines = [
        f"You are an expert copywriter specializing in creating engaging, human-like, and SEO-optimized blog posts from video transcripts.",
        f"Your output MUST be only the raw content formatted in {output_format}. Do NOT include any conversational preamble, explanations, or text whatsoever before or after the {output_format} content.",
        f"The very first line of your response MUST be the H1 title ('# Title' for markdown, '<h1>Title</h1>' for html) with absolutely no preceding characters, spaces, or text.",
        f"Use standard {output_format} syntax and ensure proper newlines for formatting.",
        "Follow this structure:",
        "1.  Create a catchy, SEO-friendly Title (as the very first line).",
        "2.  Write a brief, engaging Introduction (2-3 sentences).",
        "3.  Identify the main themes/sections in the transcript.",
        "4.  For each theme, create a keyword-rich Section Heading (e.g., H2 in HTML, ## Heading in Markdown).",
        "5.  Under each heading, write detailed paragraph(s) expanding on the theme with a natural, conversational flow.",
        "6.  Conclude with a Key Takeaways or Conclusion section (paragraph or bullet points).",
        "Ensure the language is natural and avoids simply listing transcript points."
    ]

    # Add dynamic instructions
    if tone:
        prompt_lines.append(f"Adopt a {tone} tone throughout the blog post.")
    if audience:
        prompt_lines.append(f"Write the blog post specifically for an audience of {audience}.")

    system_prompt = "\n".join(prompt_lines)
    # --- End of dynamic prompt building ---

    user_prompt = f"Generate a blog post in {output_format} based on the following transcript:\n\n--TRANSCRIPT START--\n{transcription}\n--TRANSCRIPT END--"

    # --- Try Primary LLM: Gemini ---
    if gemini_api_key:
        try:
            client = OpenAI(
                api_key=gemini_api_key,
                base_url=GEMINI_ENDPOINT
            )
            logger.info(f"Attempting blog post generation with Gemini ({GEMINI_MODEL_TO_USE}). Prompt includes Tone: '{tone}', Audience: '{audience}'.")
            response = client.chat.completions.create(
                model=GEMINI_MODEL_TO_USE,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
            )
            blog_post = response.choices[0].message.content
            llm_method = "gemini"
            logger.info(f"Blog post successfully generated using Gemini.")
            # **** Log raw repr of the string ****
            logger.debug(f"Raw LLM output repr: {repr(blog_post)}")

        except Exception as e:
            logger.warning(f"Gemini blog post generation failed: {e}. Attempting fallback...")
    else:
        logger.warning("GEMINI_API_KEY not found. Skipping Gemini, attempting fallback...")

    # --- Try Fallback LLM: OpenRouter ---
    if not blog_post:
        openrouter_api_key = os.getenv(OPENROUTER_API_KEY_ENV_VAR)
        if openrouter_api_key:
            try:
                client = OpenAI(
                    api_key=openrouter_api_key,
                    base_url=OPENROUTER_ENDPOINT,
                    default_headers={ "HTTP-Referer": "http://localhost",
                                      "X-Title": "youtube-to-blog-poc" }
                )
                logger.info(f"Attempting blog post generation with OpenRouter ({OPENROUTER_MODEL_TO_USE}). Prompt includes Tone: '{tone}', Audience: '{audience}'.")
                response = client.chat.completions.create(
                    model=OPENROUTER_MODEL_TO_USE,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                )
                blog_post = response.choices[0].message.content
                llm_method = "openrouter"
                logger.info(f"Blog post successfully generated using OpenRouter.")
                # **** Log raw repr of the string ****
                logger.debug(f"Raw LLM output repr: {repr(blog_post)}")

            except Exception as e:
                logger.error(f"OpenRouter blog post generation failed: {e}")
        else:
            logger.error("OpenRouter fallback failed: " + OPENROUTER_API_KEY_ENV_VAR + " not found.")

    if blog_post:
        # Attempt to clean potential unwanted prefixes/suffixes first
        cleaned_post = blog_post.strip()
        prefix_removed = False # Flag to track if prefix cleaning happened

        if output_format == "markdown":
             if not cleaned_post.startswith("#"):
                  match = re.search(r"^#\s+\S+", cleaned_post, re.MULTILINE)
                  if match:
                       logger.warning("Removed potential prefix before first Markdown header.")
                       cleaned_post = cleaned_post[match.start():].strip()
                       prefix_removed = True
        elif output_format == "html":
             if not (cleaned_post.startswith("<") and cleaned_post.endswith(">")):
                  match = re.search(r"<[^>]+>", cleaned_post)
                  if match:
                       logger.warning("Removed potential prefix before first HTML tag.")
                       cleaned_post = cleaned_post[match.start():].strip()
                       prefix_removed = True

        if not prefix_removed and not (cleaned_post.startswith("#") or cleaned_post.startswith("<")):
             # Only log warning if prefix wasn't removed and it doesn't start as expected
             logger.warning("LLM output might contain non-content prefixes/suffixes despite instructions.")

        # Return the cleaned post (newline replacement removed as repr shows it's unnecessary)
        return cleaned_post

    else:
        logger.error("Failed to generate blog post using both Gemini and OpenRouter.")
        return None

# --- API Endpoint ---

@app.post("/process-video/")
async def process_video(video_id: str,
                        output_format: str = Query("markdown", description="Output format: 'markdown' or 'html'"),
                        tone: str | None = Query(None, description="Optional tone for the blog post (e.g., 'casual', 'formal', 'enthusiastic')"),
                        audience: str | None = Query(None, description="Optional audience for the blog post (e.g., 'beginners', 'experts')") ):
    """
    Processes a YouTube video: downloads audio, transcribes (with fallback),
    and generates a blog post (with fallback) in the specified format, optionally tailored by tone and audience.

    - **video_id**: The unique ID of the YouTube video (e.g., 'dQw4w9WgXcQ').
    - **output_format**: The desired output format ('markdown' or 'html'). Defaults to 'markdown'.
    - **tone**: Optional tone for the blog post (e.g., 'casual', 'formal', 'enthusiastic').
    - **audience**: Optional audience for the blog post (e.g., 'beginners', 'experts').
    """
    logger.info(f"Received request to process video ID: {video_id} (Format: {output_format}, Tone: {tone}, Audience: {audience})")
    # Validate output format
    if output_format not in ["markdown", "html"]:
        raise HTTPException(status_code=400, detail="Invalid output_format. Must be 'markdown' or 'html'.")

    transcription = None
    transcription_method = "whisper" # Assume primary initially

    # --- Primary Method: Whisper ---
    audio_path = download_audio(video_id)
    if audio_path:
        logger.info("Attempting transcription using Whisper (primary)...")
        transcription = transcribe_audio_with_whisper(audio_path)
    else:
        logger.warning("Audio download failed, cannot use Whisper. Will attempt fallback.")

    # --- Fallback Method: YouTube Captions ---
    if not transcription:
        logger.warning("Whisper transcription failed or was skipped. Attempting fallback (YouTube Captions)...")
        transcription_method = "youtube-captions"
        transcription = get_youtube_captions(video_id)

    # --- Final Check and Blog Post Generation ---
    if not transcription:
        logger.error(f"Both Whisper and YouTube Caption methods failed for video ID: {video_id}")
        raise HTTPException(status_code=500, detail="Failed to obtain transcription.")

    logger.info(f"Transcription obtained using method: {transcription_method}")
    # Pass the output_format to the blog post generation function
    blog_post_content = generate_blog_post(transcription, output_format, tone, audience)
    if not blog_post_content:
        raise HTTPException(status_code=500, detail="Failed to generate blog post.")

    logger.info(f"Successfully processed video ID: {video_id}")
    return {
        "video_id": video_id,
        "transcription_method": transcription_method,
        "output_format": output_format,
        "tone": tone,
        "audience": audience,
        "transcription": transcription, # Still useful to return?
        "blog_post": blog_post_content
    }

# --- Main Execution (for local testing) ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server for local testing...")
    # Make sure to set GEMINI_API_KEY in your environment or .env file
    if not os.getenv("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY environment variable not set. API calls to Gemini will fail.")
    if not os.getenv("GEMINI_MODEL_NAME"):
        logger.warning(f"GEMINI_MODEL_NAME environment variable not set. Using default: {DEFAULT_GEMINI_MODEL}")
    else:
        logger.info(f"Using Gemini model from .env: {GEMINI_MODEL_TO_USE}")

    uvicorn.run(app, host="0.0.0.0", port=8000)