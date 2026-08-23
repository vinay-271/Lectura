import { getYouTubeVideoId } from '../utils/youtube'

interface VideoInfoProps {
  youtubeUrl: string
}

// This component shows the YouTube video selected for note generation.
function VideoInfo({ youtubeUrl }: VideoInfoProps) {

  const videoId = getYouTubeVideoId(youtubeUrl)

  return (
    <section className="video-info">
      <p className="video-info-label">Current video</p>

      <p className="video-info-url" title={youtubeUrl}>
        {videoId ?? 'Unknown video'}
      </p>
    </section>
  )
}

export default VideoInfo
