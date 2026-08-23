// This function checks if a URL belongs to a YouTube video.
export function isYouTubeVideoUrl(url: string): boolean {
  try {
    const parsedUrl = new URL(url)

    const isYouTubeHost =
      parsedUrl.hostname === 'www.youtube.com' ||
      parsedUrl.hostname === 'youtube.com'

    const isWatchPage =
      parsedUrl.pathname === '/watch' &&
      parsedUrl.searchParams.has('v')

    const isShortUrl =
      parsedUrl.hostname === 'youtu.be' &&
      parsedUrl.pathname.length > 1

    return isYouTubeHost && isWatchPage || isShortUrl
  } catch {
    return false
  }
}

// This function extracts the YouTube video ID from a supported video URL.
export function getYouTubeVideoId(url: string): string | null {
  try {
    const parsedUrl = new URL(url)

    if (
      parsedUrl.hostname === 'www.youtube.com' ||
      parsedUrl.hostname === 'youtube.com'
    ) {
      if (parsedUrl.pathname === '/watch') {
        return parsedUrl.searchParams.get('v')
      }
    }

    if (parsedUrl.hostname === 'youtu.be') {
      const videoId = parsedUrl.pathname.slice(1)
      return videoId || null
    }

    return null
  } catch {
    return null
  }
}
