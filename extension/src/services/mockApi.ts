import type { GenerateNotesResponse } from '../types/api'
import { mockNotes } from './mockData'

// This function simulates the backend response for frontend development.
export async function mockGenerateNotes(
  _youtubeUrl: string,
): Promise<GenerateNotesResponse> {
  // This delay simulates the time needed by the real backend.
  await new Promise((resolve) => setTimeout(resolve, 1500))

  return {
    title: 'Introduction to Machine Learning',
    summary:
      'This video explains the basic concepts of machine learning, supervised learning, and model evaluation.',
    notes: mockNotes,
  }
}
