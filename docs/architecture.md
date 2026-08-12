# NoteTube AI - Architecture Document

**Version**: 0.1
**Status**: Draft
**Last Updated**: 2024

---

## 1. Project Overview

### 1.1 Purpose
NoteTube AI is a Chrome Extension that generates textbook-quality notes from YouTube educational videos using Google's Gemini AI.

### 1.2 Goals
- Provide students/learners with structured notes from video content
- Enable timestamp-based navigation back to source material
- Extract visual context (screenshots) alongside text
- Deliver as a lightweight browser extension

### 1.3 Non-Goals (MVP)
- User accounts / authentication
- Flashcards / quiz generation
- PDF export
- Multi-language support
- Video download
- Offline mode

---

## 2. System Architecture

```
┌─────────────────┐     HTTPS      ┌─────────────────┐
│  Chrome Ext     │ ──────────────▶│  FastAPI        │
│  (React + TS)   │ ◀──────────────│  Backend        │
└─────────────────┘  JSON Response  └────────┬────────┘
                                             │
                              ┌──────────────┼──────────────┐
                              ▼              ▼              ▼
                       ┌───────────┐  ┌───────────┐  ┌───────────┐
                       │YouTube    │  │Gemini AI  │  │FFmpeg/    │
                       │Transcript │  │API        │  │OpenCV     │
                       │API        │  │           │  │           │
                       └───────────┘  └───────────┘  └───────────┘
```

### 2.1 Components

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| Extension Popup | React + TypeScript | UI, user interaction, display results |
| Content Script | TypeScript | YouTube page detection, DOM interaction |
| Background Script | TypeScript | Message routing, API calls |
| FastAPI Server | Python 3.12 | REST API, orchestration |
| Transcript Service | youtube-transcript-api | Extract captions |
| Video Processor | OpenCV + FFmpeg | Keyframe extraction, scene detection |
| AI Service | Google Generative AI | Notes & summary generation |

### 2.2 Data Flow

1. User navigates to YouTube video
2. Content script detects video ID, sends to popup
3. User clicks "Generate Notes" in popup
4. Popup sends `POST /generate-notes` with YouTube URL
5. Backend:
   - Extracts transcript
   - Downloads video, extracts keyframes
   - Sends transcript + frames to Gemini
   - Returns structured notes
6. Extension displays notes with timestamps & images
7. User clicks timestamp → video seeks to position

---

## 3. Folder Structure

```
notetube-ai/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # /generate-notes endpoint
│   │   ├── core/
│   │   │   ├── config.py          # Settings, env vars
│   │   │   └── security.py        # API key validation
│   │   ├── models/
│   │   │   └── schemas.py         # Pydantic models
│   │   ├── services/
│   │   │   ├── transcript.py      # YouTube transcript extraction
│   │   │   ├── video_processor.py # FFmpeg/OpenCV keyframes
│   │   │   └── gemini.py          # AI notes generation
│   │   └── main.py                # FastAPI app entry
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│
├── extension/
│   ├── public/
│   │   └── manifest.json          # Manifest V3
│   ├── src/
│   │   ├── background/
│   │   │   └── index.ts           # Service worker
│   │   ├── content/
│   │   │   └── index.ts           # YouTube page script
│   │   ├── popup/
│   │   │   ├── App.tsx            # Main popup component
│   │   │   ├── components/        # UI components
│   │   │   ├── hooks/             # Custom React hooks
│   │   │   ├── types/             # TypeScript interfaces
│   │   │   └── api.ts             # Backend API client
│   │   └── styles/
│   │       └── globals.css        # Tailwind imports
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── docs/
│   └── architecture.md            # This file
│
├── .gitignore
├── README.md
└── LICENSE
```

---

## 4. API Contract

### POST `/generate-notes`

**Request**
```json
{
  "youtube_url": "https://youtu.be/dQw4w9WgXcQ"
}
```

**Response** (200 OK)
```json
{
  "title": "Video Title",
  "summary": "AI-generated summary...",
  "notes": [
    {
      "heading": "Introduction",
      "content": "Detailed notes content...",
      "timestamp": "0:00",
      "image": "base64_or_url"
    }
  ]
}
```

**Error Response** (4xx/5xx)
```json
{
  "detail": "Error message",
  "code": "TRANSCRIPT_NOT_FOUND"
}
```

### Error Codes
| Code | HTTP | Description |
|------|------|-------------|
| `INVALID_URL` | 400 | Not a valid YouTube URL |
| `TRANSCRIPT_NOT_FOUND` | 404 | No captions available |
| `VIDEO_DOWNLOAD_FAILED` | 502 | Could not fetch video |
| `GEMINI_API_ERROR` | 502 | AI service failure |
| `RATE_LIMITED` | 429 | Too many requests |

---

## 5. Data Models

### Backend (Pydantic)

```python
# app/models/schemas.py
class NoteItem(BaseModel):
    heading: str
    content: str
    timestamp: str  # "MM:SS" or "HH:MM:SS"
    image: Optional[str] = None  # base64 or URL

class GenerateNotesRequest(BaseModel):
    youtube_url: HttpUrl

class GenerateNotesResponse(BaseModel):
    title: str
    summary: str
    notes: List[NoteItem]
```

### Frontend (TypeScript)

```typescript
// src/popup/types/index.ts
export interface NoteItem {
  heading: string;
  content: string;
  timestamp: string;
  image?: string;
}

export interface GenerateNotesResponse {
  title: string;
  summary: string;
  notes: NoteItem[];
}
```

---

## 6. Team Responsibilities

| Member | Role | Primary Areas |
|--------|------|---------------|
| Member 1 | **Frontend Lead** | Extension UI, popup, content script, Tailwind styling, API integration |
| Member 2 | **Backend Lead** | FastAPI, Gemini prompts, transcript extraction, video processing, deployment |
| Member 3 | **Full-Stack** | Integration testing, CI/CD, architecture docs, cross-cutting concerns, unblocking |

### Communication
- Daily 15-min standup (async or sync)
- Weekly integration test session
- PR reviews required (1 approval)
- Architecture changes = team consensus

---

## 7. Development Workflow

### Git Flow
```
main (protected)
  ↑ PR (monthly)
develop (integration)
  ↑ PR (per feature)
feature/<short-name>
```

### Branch Naming
- `feat/<description>` - New feature
- `fix/<description>` - Bug fix
- `refactor/<description>` - Code improvement
- `docs/<description>` - Documentation

### Commit Convention
```
feat: add transcript extraction service
fix: handle missing captions gracefully
refactor: simplify gemini prompt builder
docs: update api contract in architecture.md
```

### Definition of Done
- [ ] Code compiles, no lint errors
- [ ] Works locally (frontend + backend)
- [ ] Unit tests pass (backend)
- [ ] Manual test in Chrome extension
- [ ] No console errors
- [ ] `architecture.md` updated if API changes
- [ ] PR merged to `develop`

---

## 8. Future Roadmap (Post-MVP)

### Phase 2 (Month 2-3)
- [ ] Flashcard generation from notes
- [ ] Quiz generation
- [ ] PDF/Markdown export
- [ ] User settings (AI model, note detail level)
- [ ] Side panel UI (alternative to popup)

### Phase 3 (Future)
- [ ] User accounts & cloud sync
- [ ] Multi-language transcript support
- [ ] Playlist/batch processing
- [ ] Community notes sharing
- [ ] Mobile companion app

---

## 9. Appendix

### 9.1 Environment Variables

**Backend (`.env`)**
```
GEMINI_API_KEY=your_key_here
BACKEND_CORS_ORIGINS=["chrome-extension://<extension_id>"]
LOG_LEVEL=INFO
```

**Extension (`.env`)**
```
VITE_API_URL=http://localhost:8000
```

### 9.2 Key Dependencies

**Backend**
- `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`
- `google-generativeai`, `youtube-transcript-api`
- `opencv-python`, `ffmpeg-python`
- `httpx`, `python-dotenv`

**Extension**
- `react`, `react-dom`, `typescript`
- `vite`, `@vitejs/plugin-react`
- `tailwindcss`, `postcss`, `autoprefixer`
- `axios` or native `fetch`

### 9.3 References
- [Chrome Extensions MV3 Docs](https://developer.chrome.com/docs/extensions/mv3/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Gemini API Docs](https://ai.google.dev/docs)
- [FFmpeg Keyframe Extraction](https://stackoverflow.com/a/5286222)