# System Patterns: YouTube-to-Blog Generator

## 1. High-Level Architecture
A standard web application architecture is proposed:

```mermaid
flowchart LR
    User[User Browser] --> FE[Frontend (React + Tailwind)]
    FE -->|API Request (URL, Prefs)| BE[Backend API (Node/Python)]
    BE -->|URL| V[Validation Service]
    V --> BE
    BE -->|URL| T[Transcription Service]
    T -->|Transcription Text| BE
    BE -->|Text, Prefs| AI[AI Blog Generation Service]
    AI -->|Generated Blog| BE
    BE -->|Blog Post| FE
    FE --> User

    subgraph External/Managed Services
        T -- Uses --> Whisper[Whisper (OSS) / YouTube Captions]
        AI -- Uses --> LLM[LLM (Grok 3 / LLaMA)]
        BE -- Uses --> Cache[(Redis Cache)]
    end
```

## 2. Key Architectural Decisions (Initial)
- **Decoupled Services:** Separate concerns for transcription and AI generation, allowing flexibility in choosing and potentially swapping implementations.
- **API-Driven:** Frontend interacts with a dedicated backend API, enabling potential future use by other clients.
- **Stateless Backend (where possible):** Rely on temporary storage (cache) for intermediate data like transcriptions, avoiding persistent user data storage.
- **Emphasis on Free/Open-Source:** Prioritize free transcription methods (Whisper, YouTube captions) and potentially open-source LLMs to meet the 'free service' requirement.
- **Asynchronous Processing:** Transcription might take time. The backend should handle this asynchronously, potentially using a queue system if load increases, and provide feedback to the user.

## 3. Data Flow
1.  User submits YouTube URL and preferences via Frontend.
2.  Frontend sends data to Backend API.
3.  Backend validates the URL.
4.  Backend requests transcription from the Transcription Service (providing the URL).
5.  Transcription Service processes the video (using Whisper or fetching captions) and returns text to the Backend.
6.  Backend temporarily stores the transcription (e.g., Redis cache).
7.  Backend sends transcription text and user preferences to AI Blog Generation Service.
8.  AI Service uses an LLM, guided by prompts incorporating tone/type/length/human-like constraints, to generate the blog post.
9.  AI Service returns the generated blog text to the Backend.
10. Backend returns the blog post to the Frontend.
11. Frontend displays the result to the user.
12. Temporary transcription data is cleared after a short period or session end.