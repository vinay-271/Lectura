function Header() {
  // This component shows the main Lectura branding and status.
  return (
    <header className="app-header">
      <div>
        <h1>Lectura</h1>
        <p>AI study assistant</p>
      </div>

      <span
        className="status-indicator"
        aria-label="Lectura is ready"
        title="Lectura is ready"
      />
    </header>
  )
}

export default Header
