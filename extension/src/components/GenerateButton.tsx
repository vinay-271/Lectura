import { useState } from 'react'
import { getCurrentYouTubeUrl } from '../services/youtube'
import { generateVideoNotes } from '../services/notes'
import type { NoteResponse } from '../types/api'
import type { GenerationError } from '../types/errors'

interface GenerateButtonProps {
  onNotesGenerated: (notes: NoteResponse[], url: string) => void
  onGenerationStart: () => void
  onGenerationError: (error: GenerationError) => void
}

function GenerateButton({
  onNotesGenerated,
  onGenerationStart,
  onGenerationError,
}: GenerateButtonProps) {
  const [isLoading, setIsLoading] = useState(false)

  // Get the YouTube URL and generate notes using the mock API.
  const handleGenerateClick = async () => {
    const youtubeUrl = await getCurrentYouTubeUrl()

    if (!youtubeUrl) {
      onGenerationError('invalid-youtube-url')
      return
    }

    try {
      setIsLoading(true)
      onGenerationStart()

      const response = await generateVideoNotes(youtubeUrl)

      onNotesGenerated(response.notes, youtubeUrl)
    } catch {
      onGenerationError('generation-failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <section className="generate-section">
      <div className="generate-content">
        <h2>Ready to learn?</h2>

        <p>
          Generate detailed notes from the YouTube video you're watching.
        </p>

        <button
          type="button"
          className="generate-button"
          onClick={handleGenerateClick}
          disabled={isLoading}
        >
          {isLoading ? 'Generating...' : 'Generate Notes'}
        </button>
      </div>
    </section>
  )
}

export default GenerateButton
