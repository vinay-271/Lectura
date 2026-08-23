import { useEffect, useState } from 'react'
import './App.css'
import Header from './components/Header'
import GenerateButton from './components/GenerateButton'
import GenerationStatus from './components/GenerationStatus'
import NotesView from './components/NotesView'
import type { NoteResponse } from './types/api'
import type { GenerationError } from './types/errors'
import VideoInfo from './components/VideoInfo'
import { getCurrentYouTubeUrl } from './services/youtube'

// These mock notes are temporary test data for the notes UI.

function App() {
  const [notes, setNotes] = useState<NoteResponse[]>([])
  const [generationStatus, setGenerationStatus] =
    useState<'idle' | 'generating' | 'success' | 'error'>('idle')

  const [errorMessage, setErrorMessage] = useState<string | undefined>(
    undefined,
  )
  const [youtubeUrl, setYoutubeUrl] = useState<string | null>(null)

  // This callback receives generated notes and updates the app state.
  const handleNotesGenerated = (
    generatedNotes: NoteResponse[],
    url: string,
  ) => {
    setNotes(generatedNotes)
    setYoutubeUrl(url)
    setGenerationStatus('success')
  }

  useEffect(() => {
    const loadCurrentVideo = async () => {
      const url = await getCurrentYouTubeUrl()

      if (url) {
        setYoutubeUrl(url)
      }
    }

    void loadCurrentVideo()
  }, [])

  return (
    <main>
      <Header />

      {youtubeUrl && <VideoInfo youtubeUrl={youtubeUrl} />}

      {(generationStatus === 'idle' || generationStatus === 'error') && (
        <GenerateButton
          onNotesGenerated={handleNotesGenerated}
          onGenerationStart={() => {
            setGenerationStatus('generating')
            setErrorMessage(undefined)
          }}
          onGenerationError={(error: GenerationError) => {
            setGenerationStatus('error')

            if (error === 'invalid-youtube-url') {
              setErrorMessage('Please open a YouTube video.')
              return
            }

            setErrorMessage('Failed to generate notes.')
          }}
        />
      )}

      <GenerationStatus
        status={generationStatus}
        errorMessage={errorMessage}
      />

      {generationStatus === 'success' && <NotesView notes={notes} />}
    </main>
  )
}

export default App
