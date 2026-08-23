import type { GenerateNotesResponse } from '../types/api'

// This is the URL of the Lectura backend.
const API_BASE_URL = 'http://localhost:8000'

// This function sends a YouTube URL to the backend to generate notes.
export async function generateNotes(
  youtubeUrl: string,
): Promise<GenerateNotesResponse> {
  const response = await fetch(`${API_BASE_URL}/generate-notes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      youtube_url: youtubeUrl,
    }),
  })

  if (!response.ok) {
    throw new Error('Failed to generate notes.')
  }

  return response.json()
}
