import type { GenerateNotesResponse } from '../types/api'
import { mockGenerateNotes } from './mockApi'

// This function is the single entry point for generating notes.
export async function generateVideoNotes(
  youtubeUrl: string,
): Promise<GenerateNotesResponse> {
  return mockGenerateNotes(youtubeUrl)
}
