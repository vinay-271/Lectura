# Lectura — Architecture & Project Plan

## 1. Project Overview

**Lectura** is a Chrome Extension that helps students turn educational YouTube videos into structured, textbook-quality notes.

The core idea is simple:

> **Watch less. Understand more.**

A user opens an educational YouTube video, opens Lectura, and requests notes. Lectura processes the video, extracts its transcript and important visual information, sends the relevant information to the AI pipeline, and returns structured notes and a concise summary.

The MVP is focused on educational YouTube videos.

---

## 2. MVP Goals

The first version of Lectura will support:

- Detecting the currently opened YouTube video
- Extracting the video's transcript
- Identifying important visual moments
- Extracting important screenshots
- Generating detailed AI-powered notes
- Generating a short summary
- Displaying notes and screenshots in the Chrome extension
- Clicking timestamps to jump to that point in the YouTube video
- Loading/progress states
- Error handling

### Out of Scope for MVP

The following will **not** be built initially:

- User accounts
- Authentication
- Database
- Note history
- Payments
- Cloud storage
- Flashcards
- Quiz generation
- Notion export
- Multiple AI providers
- Collaboration features

These may be considered after the MVP is stable.

---

## 3. System Architecture

The high-level data flow is:

```text
┌─────────────────────────────┐
│        YouTube Video        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│     Lectura Chrome          │
│        Extension            │
│                             │
│ React + TypeScript          │
│ Chrome Side Panel           │
└──────────────┬──────────────┘
               │
               │ POST /generate-notes
               ▼
┌─────────────────────────────┐
│       FastAPI Backend       │
│                             │
│ Transcript Processing       │
│ Video Processing            │
│ AI Pipeline                 │
└──────────────┬──────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│  Transcript  │  │    Video     │
│  Extraction  │  │  Processing  │
└──────┬───────┘  └──────┬───────┘
       │                 │
       │           OpenCV / FFmpeg
       │                 │
       └────────┬────────┘
                ▼
       ┌─────────────────┐
       │  Gemini AI      │
       │  Multimodal     │
       └────────┬────────┘
                │
                ▼
       ┌─────────────────┐
       │ Structured Notes│
       │ + Summary       │
       │ + Screenshots   │
       └────────┬────────┘
                │
                ▼
       ┌─────────────────┐
       │ Chrome Extension│
       │       UI        │
       └─────────────────┘
```

---

## 4. Technology Stack

### Backend

- Python 3.12
- FastAPI
- Uvicorn
- Pydantic
- Gemini API

### Frontend / Extension

- React
- TypeScript
- Vite
- Tailwind CSS
- Chrome Extension Manifest V3
- Chrome Side Panel API

### Video Processing

- OpenCV
- FFmpeg

### Version Control

- Git
- GitHub

---

## 5. Repository Structure

The repository starts with the following structure:

```text
Lectura/
│
├── backend/
├── extension/
├── docs/
│   └── architecture.md
│
├── .gitignore
├── README.md
└── LICENSE
```

Detailed internal structures will be created incrementally as each part of the project is implemented.

We will avoid creating unnecessary folders or files before their purpose is established.

---

## 6. Team Responsibilities

### Member 1 — Backend + AI

Responsible for the core backend and AI pipeline.

Responsibilities:

- FastAPI backend
- API endpoints
- Transcript extraction
- AI pipeline
- Gemini API integration
- Prompt engineering
- Structured note generation
- Summary generation
- API schemas
- Backend error handling
- Integration of video-processing services
- Future PDF generation

Primary branch:

```text
backend-ai
```

---

### Member 2 — Chrome Extension + UI

Responsible exclusively for the extension and user interface.

Responsibilities:

- Chrome Extension Manifest V3
- React + TypeScript
- Chrome Side Panel
- YouTube URL detection
- Backend communication
- Loading states
- Notes rendering
- Screenshot rendering
- Timestamp navigation
- Error states
- Export UI

Primary branch:

```text
extension-ui
```

The extension developer does not implement AI or video-processing logic.

---

### Member 3 — Video Processing

Responsible for video intelligence and processing.

Responsibilities:

- OpenCV
- FFmpeg
- Scene detection
- Important-frame detection
- Screenshot extraction
- Duplicate screenshot prevention
- Image optimization
- Image compression
- OCR if required
- Processing benchmarks
- Video-processing tests

Primary branch:

```text
video-processing
```

This module should remain independent from the FastAPI API layer as much as possible.

---

## 7. Git Branch Strategy

The repository currently uses five branches:

```text
main
develop
backend-ai
extension-ui
video-processing
```

### `main`

Stable, tested, release-ready code.

### `develop`

Integration branch where completed work from the three development branches is combined and tested.

### `backend-ai`

Backend and AI development.

### `extension-ui`

Chrome extension and UI development.

### `video-processing`

Video processing development.

### Development Flow

```text
backend-ai ────────┐
                    │
extension-ui ──────┼──► develop ───► main
                    │
video-processing ──┘
```

Development branches should not directly modify unrelated modules without coordination.

The API contract should remain stable so that all three members can work independently.

---

## 8. API Contract

The primary MVP API endpoint is:

```http
POST /generate-notes
```

### Request

```json
{
  "youtube_url": "https://youtu.be/..."
}
```

### Response

```json
{
  "title": "",
  "summary": "",
  "notes": [
    {
      "heading": "",
      "content": "",
      "timestamp": "",
      "image": ""
    }
  ]
}
```

### Notes Object

| Field | Description |
|---|---|
| `heading` | Topic or section heading |
| `content` | Detailed explanation |
| `timestamp` | Relevant point in the video |
| `image` | Important screenshot associated with the note |

This contract is the primary integration boundary between the backend and extension.

Changes to the contract should be discussed and agreed upon before implementation.

---

## 9. Core Data Flow

The MVP follows this sequence:

```text
1. User opens YouTube
        ↓
2. User opens Lectura
        ↓
3. Extension detects current YouTube URL
        ↓
4. User clicks "Generate Notes"
        ↓
5. Extension sends YouTube URL to backend
        ↓
6. Backend obtains transcript
        ↓
7. Video-processing pipeline identifies important frames
        ↓
8. Important screenshots are extracted
        ↓
9. Transcript + visual information are provided to Gemini
        ↓
10. Gemini generates structured notes
        ↓
11. Backend returns structured JSON
        ↓
12. Extension renders summary, notes and screenshots
        ↓
13. User clicks timestamp
        ↓
14. YouTube jumps to the relevant moment
```

---

## 10. Development Philosophy

Lectura will be developed incrementally.

We will:

1. Build one component at a time.
2. Explain the purpose of each file before creating it.
3. Keep modules independent.
4. Test each milestone before moving forward.
5. Commit after meaningful completed work.
6. Keep the API contract stable.
7. Avoid premature complexity.
8. Integrate through `develop`.
9. Keep the MVP focused.
10. Add advanced features only after the MVP works reliably.

We will **not** build the entire project at once.

---

## 11. Development Roadmap

### Stage 0 — Foundation

- Repository setup
- Folder structure
- Git branches
- Architecture documentation
- MVP definition
- API contract

**Goal:** Establish a stable foundation.

---

### Stage 1 — Communication Pipeline

Build the simplest possible end-to-end connection:

```text
Chrome Extension
       ↓
FastAPI
       ↓
"Hello from Backend"
       ↓
Chrome Extension
```

**Goal:** Prove that the extension and backend can communicate successfully.

---

### Stage 2 — Transcript Extraction

Implement:

- YouTube URL handling
- Transcript retrieval
- Transcript validation
- Error handling

**Goal:** Backend can reliably obtain the video's textual content.

---

### Stage 3 — Video Processing

Implement:

- Video/frame access
- Scene detection
- Important-frame detection
- Screenshot extraction
- Duplicate prevention
- Image optimization

**Goal:** Produce useful screenshots with timestamps.

---

### Stage 4 — AI Integration

Implement:

- Gemini integration
- Prompt engineering
- Transcript + visual context
- Structured note generation
- Summary generation

**Goal:** Produce high-quality educational notes.

---

### Stage 5 — Frontend Integration

Implement:

- Notes rendering
- Summary rendering
- Screenshots
- Timestamp navigation
- Loading states
- Error handling

**Goal:** Complete end-to-end MVP.

---

### Stage 6 — Polish & Release

Implement:

- UI refinement
- Performance improvements
- Edge-case handling
- Testing
- Documentation
- Deployment
- Demo preparation

**Goal:** Produce a polished, portfolio-quality release.

---

## 12. MVP Milestone

The MVP is considered complete when a user can:

```text
Open an educational YouTube video
            ↓
Open Lectura
            ↓
Click "Generate Notes"
            ↓
Wait for processing
            ↓
Receive a short summary
            ↓
Read structured notes
            ↓
View relevant screenshots
            ↓
Click a timestamp
            ↓
Jump to that point in the video
```

Everything beyond this flow is secondary until this works reliably.

---

## 13. Future Roadmap

After the MVP is stable, possible future features include:

- PDF export
- Flashcards
- Quiz generation
- Note history
- User accounts
- Notion export
- Multiple AI models
- Cloud storage
- Sharing notes
- Collaborative study features

These features should not interfere with the initial MVP development.

---

## 14. Project Principle

> **Build the smallest complete version first, then make it better.**

Lectura should prioritize reliability, clean architecture, useful output, and a good user experience over unnecessary features.

The first goal is not to build a huge platform.

The first goal is to make:

**YouTube → Lectura → High-quality notes**

work extremely well.
architecture.md
Displaying architecture.md.
