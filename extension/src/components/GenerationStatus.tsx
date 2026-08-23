import type { GenerationStatus as GenerationStatusType } from '../types/generation'

interface GenerationStatusProps {
  status: GenerationStatusType
  errorMessage?: string
}

// This component shows the current note generation status.
function GenerationStatus({
  status,
  errorMessage,
}: GenerationStatusProps) {
  if (status === 'idle') {
    return null
  }

  if (status === 'generating') {
    return (
      <div className="generation-status">
        <p>Generating detailed notes...</p>
      </div>
    )
  }

  if (status === 'success') {
    return (
      <div className="generation-status">
        <p>Notes generated successfully.</p>
      </div>
    )
  }

  return (
    <div className="generation-status">
      <p>{errorMessage ?? 'Failed to generate notes.'}</p>
    </div>
  )
}

export default GenerationStatus
