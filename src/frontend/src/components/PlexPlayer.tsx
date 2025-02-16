import React, { useEffect, useRef, useState } from 'react';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
import { io } from 'socket.io-client';
import { Library, Film, PlayCircle, PauseCircle, Volume2, Maximize2 } from 'lucide-react';

interface PlexPlayerProps {
  token: string;
}

interface MediaInfo {
  title: string;
  duration: number;
  thumbnail: string;
  streamUrl: string;
}

const PlexPlayer: React.FC<PlexPlayerProps> = ({ token }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const playerRef = useRef<any>(null);
  const socketRef = useRef<any>(null);
  const [currentMedia, setCurrentMedia] = useState<MediaInfo | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(1);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Initialize video.js
    if (!playerRef.current && videoRef.current) {
      playerRef.current = videojs(videoRef.current, {
        controls: true,
        fluid: true,
        html5: {
          hls: {
            enableLowInitialPlaylist: true,
            smoothQualityChange: true,
            overrideNative: true
          }
        }
      });
    }

    // Initialize WebSocket
    socketRef.current = io('http://localhost:5000', {
      auth: { token }
    });

    // WebSocket event handlers
    socketRef.current.on('playback_update', (data: any) => {
      if (data.action === 'play') {
        playerRef.current?.play();
        setIsPlaying(true);
      } else if (data.action === 'pause') {
        playerRef.current?.pause();
        setIsPlaying(false);
      }
    });

    socketRef.current.on('queue_changed', (data: any) => {
      if (data.media) {
        setCurrentMedia(data.media);
        playerRef.current?.src({ src: data.media.streamUrl });
      }
    });

    return () => {
      if (playerRef.current) {
        playerRef.current.dispose();
      }
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [token]);

  const handlePlayPause = () => {
    if (isPlaying) {
      playerRef.current?.pause();
      socketRef.current?.emit('playback_state', { action: 'pause' });
    } else {
      playerRef.current?.play();
      socketRef.current?.emit('playback_state', { action: 'play' });
    }
    setIsPlaying(!isPlaying);
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value);
    playerRef.current.volume(newVolume);
    setVolume(newVolume);
  };

  const handleProgress = () => {
    if (playerRef.current) {
      const duration = playerRef.current.duration();
      const currentTime = playerRef.current.currentTime();
      setProgress((currentTime / duration) * 100);
    }
  };

  return (
    <div className="bg-gray-900 text-white p-4 w-full h-96 flex flex-col">
      {/* Header */}
      <div className="flex items-center mb-4 border-b border-gray-700 pb-2">
        <Library className="w-6 h-6 mr-2" />
        <h1 className="text-xl font-bold">Plex Player</h1>
      </div>

      {/* Player */}
      <div className="flex-1 relative">
        <video
          ref={videoRef}
          className="video-js vjs-theme-dark"
          onTimeUpdate={handleProgress}
        />
      </div>

      {/* Controls */}
      <div className="bg-gray-800 p-3 rounded-lg mt-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-4">
            <button onClick={handlePlayPause}>
              {isPlaying ? (
                <PauseCircle className="w-8 h-8 hover:text-blue-400" />
              ) : (
                <PlayCircle className="w-8 h-8 hover:text-blue-400" />
              )}
            </button>
            <div className="flex items-center gap-2">
              <Volume2 className="w-5 h-5" />
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={volume}
                onChange={handleVolumeChange}
                className="w-24"
              />
            </div>
          </div>
          <Maximize2 className="w-5 h-5 cursor-pointer" />
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-700 h-1 rounded-full">
          <div
            className="bg-blue-500 h-full rounded-full"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Media Info */}
        {currentMedia && (
          <div className="mt-2 text-sm text-gray-400">
            <span>{currentMedia.title}</span>
            <span className="mx-2">•</span>
            <span>
              {Math.floor(progress * currentMedia.duration / 100 / 60)}:
              {Math.floor(progress * currentMedia.duration / 100 % 60)
                .toString()
                .padStart(2, '0')}
              /
              {Math.floor(currentMedia.duration / 60)}:
              {Math.floor(currentMedia.duration % 60)
                .toString()
                .padStart(2, '0')}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default PlexPlayer; 