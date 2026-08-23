// These are the possible states while Lectura generates notes.
export type GenerationStatus =
  | 'idle'
  | 'generating'
  | 'success'
  | 'error'
