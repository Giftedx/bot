import React from 'react';
import { Library, Film, PlayCircle, PauseCircle, Volume2, Maximize2 } from 'lucide-react';

const PlexPlayerMockup = () => {
  return (
    <div className="bg-gray-900 text-white p-4 w-full h-96 flex flex-col">
      {/* Header */}
      <div className="flex items-center mb-4 border-b border-gray-700 pb-2">
        <Library className="w-6 h-6 mr-2" />
        <h1 className="text-xl font-bold">Plex Player</h1>
      </div>
      
      {/* Main Content Area */}
      <div className="flex flex-1 gap-4">
        {/* Library List */}
        <div className="w-48 border-r border-gray-700">
          <div className="p-2 bg-gray-800 rounded mb-2 flex items-center">
            <Film className="w-4 h-4 mr-2" />
            <span>Movies</span>
          </div>
          <div className="p-2 hover:bg-gray-800 rounded">TV Shows</div>
          <div className="p-2 hover:bg-gray-800 rounded">Music</div>
        </div>
        
        {/* Player Area */}
        <div className="flex-1 flex flex-col">
          {/* Video Display */}
          <div className="flex-1 bg-black rounded-lg mb-4 flex items-center justify-center">
            <span className="text-gray-500">No media selected</span>
          </div>
          
          {/* Controls */}
          <div className="bg-gray-800 p-3 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-4">
                <PlayCircle className="w-8 h-8 hover:text-blue-400 cursor-pointer" />
                <Volume2 className="w-5 h-5" />
              </div>
              <Maximize2 className="w-5 h-5" />
            </div>
            
            {/* Progress Bar */}
            <div className="w-full bg-gray-700 h-1 rounded-full">
              <div className="bg-blue-500 w-1/3 h-full rounded-full" />
            </div>
            
            {/* Time */}
            <div className="flex justify-between text-sm mt-1 text-gray-400">
              <span>0:00</span>
              <span>-:--</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlexPlayerMockup;