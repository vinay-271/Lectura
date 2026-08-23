import type { NoteResponse } from '../types/api'

// This component displays the detailed notes generated for the video.
interface NotesViewProps {
  notes: NoteResponse[]
}

function NotesView({ notes }: NotesViewProps) {
  return (
    <section className="notes-section">
      <h2 className="notes-title">Detailed Notes</h2>

      <div className="notes-list">
        {notes.map((note, index) => (
          <article className="note-card" key={index}>
            <div className="note-number">
              {String(index + 1).padStart(2, '0')}
            </div>

            <div className="note-content">
              <h3>{note.heading}</h3>
              <p>{note.content}</p>

              {note.timestamp && (
                <span className="note-timestamp">
                  {note.timestamp}
                </span>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

export default NotesView
