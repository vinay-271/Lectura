import type { NoteResponse } from '../types/api'

// These are temporary notes used to simulate a backend response.
export const mockNotes: NoteResponse[] = [
  {
    heading: 'Introduction to Machine Learning',
    content:
      'Machine learning enables computers to learn patterns from data and use those patterns to make predictions or decisions.',
    timestamp: '00:42',
  },
  {
    heading: 'Supervised Learning',
    content:
      'Supervised learning uses labelled training data to learn a relationship between inputs and expected outputs.',
    timestamp: '04:18',
  },
  {
    heading: 'Model Evaluation',
    content:
      'Model evaluation helps determine how well a trained model performs on data it has not seen during training.',
    timestamp: '08:35',
  },
]
