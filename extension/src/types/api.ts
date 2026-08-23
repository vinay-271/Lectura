// This type describes one note returned by the backend.
export interface NoteResponse {
  heading: string
  content: string
  timestamp?: string
  image?: string
}

// This type describes the complete response from the notes API.
export interface GenerateNotesResponse {
  title: string
  summary: string
  notes: NoteResponse[]
}
