# Lectura

A Chrome Extension that generates textbook-quality notes from YouTube educational videos using AI.

## Overview

Lectura transforms YouTube educational content into structured, timestamped notes with AI-generated summaries, key screenshots, and navigation. Built as a college major project with a production-grade architecture.

## Features (MVP)

- 🎥 Detect current YouTube video
- 📝 Extract transcript (with fallback)
- 🖼️ Extract key screenshots from video
- 🤖 Generate AI notes using Google Gemini
- 📋 Generate summary
- ⏱️ Timestamp navigation
- ⏳ Loading states & error handling

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic, Google Generative AI |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Chrome Extension Manifest V3 |
| **Video Processing** | OpenCV, FFmpeg |
| **Deploy** | Render/Railway (backend), Chrome Web Store (extension) |

## Project Structure

```
lectura/
│
├── backend/          # FastAPI backend
├── extension/        # Chrome Extension (React + Vite)
├── docs/             # Documentation
├── .gitignore
├── README.md
└── LICENSE
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- Git
- Google AI Studio API key (for Gemini)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Add your GEMINI_API_KEY
uvicorn main:app --reload
```

### Extension Setup

```bash
cd extension
npm install
npm run dev
# Load the `dist/` folder as unpacked extension in Chrome
```

## Development

### Branch Strategy

- `main` - Production releases (protected)
- `develop` - Integration branch
- `feature/*` - Feature branches

### API Contract

**POST** `/generate-notes`

```json
// Request
{
  "youtube_url": "https://youtu.be/..."
}

// Response
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

## Documentation

See [docs/architecture.md](docs/architecture.md) for:
- System architecture
- Folder structure details
- API contract
- Team responsibilities
- Development workflow
- Future roadmap

## Team

- **Frontend Lead** - Chrome Extension UI & integration
- **Backend Lead** - FastAPI, Gemini, video processing
- **Full-Stack** - Integration, testing, CI/CD, docs

## License

MIT License - see [LICENSE](LICENSE)