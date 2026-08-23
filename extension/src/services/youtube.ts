import { getActiveTabUrl } from './chrome'
import { isYouTubeVideoUrl } from '../utils/youtube'

// This function gets the current YouTube video URL from the active tab.
export async function getCurrentYouTubeUrl(): Promise<string | null> {
  const url = await getActiveTabUrl()

  if (!url || !isYouTubeVideoUrl(url)) {
    return null
  }

  return url
}
