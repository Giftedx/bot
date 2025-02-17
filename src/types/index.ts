export enum ActivityMode {
    OSRS = 'OSRS',
    MEDIA = 'MEDIA'
}

export enum PlaybackState {
    PLAYING = 'PLAYING',
    PAUSED = 'PAUSED',
    STOPPED = 'STOPPED'
}

export interface MediaMetadata {
    year?: number;
    summary?: string;
    rating?: number;
    studio?: string;
    director?: string;
    genre?: string;
}

export interface MediaInfo {
    id: string;
    title: string;
    duration: number;
    type: string;
    thumbnail?: string;
    metadata?: MediaMetadata;
}

export interface MediaState {
    currentMedia: MediaInfo | null;
    playbackState: PlaybackState;
    currentTime: number;
    duration: number;
    volume: number;
    participants: string[];
    leaderId: string;
    lastUpdate: number;
}

export interface OSRSState {
    // OSRS specific state will be defined here
}

export interface ActivityState {
    mode: ActivityMode;
    voiceChannelId: string;
    participants: string[];
    osrsState?: OSRSState;
    mediaState?: MediaState;
}

export interface WebSocketMessage {
    type: string;
    data: any;
}

export interface SyncRequest {
    targetTime?: number;
    playbackState?: PlaybackState;
}

export interface StateUpdate {
    type: 'STATE_UPDATE';
    data: ActivityState;
}

export type ClientMessage = {
    type: 'PLAY' | 'PAUSE' | 'SEEK' | 'STOP' | 'SET_VOLUME' | 'REQUEST_STATE';
    data?: {
        mediaId?: string;
        time?: number;
        volume?: number;
    };
}

export interface ActivityConfig {
    plexHostname: string;
    plexToken: string;
}

export interface ClientConnection {
    id: string;
    ws: WebSocket;
}

export interface MediaSource {
    type: 'plex';
    id: string;
    title: string;
    duration: number;
    thumbnail?: string;
}

export interface MediaPlayer {
    play(mediaId: string): Promise<void>;
    pause(): Promise<void>;
    resume(): Promise<void>;
    seek(time: number): Promise<void>;
    stop(): Promise<void>;
    setVolume(volume: number): Promise<void>;
}

export interface ActivityHandler {
    initialize(sessionId: string): Promise<void>;
    cleanup(): Promise<void>;
    addClient(clientId: string, ws: WebSocket): void;
    removeClient(clientId: string): void;
    handleMessage(clientId: string, message: ClientMessage): Promise<void>;
    syncState(request: SyncRequest): Promise<void>;
    getState(): MediaState | OSRSState;
}

export interface Position {
    x: number;
    y: number;
}

export interface Player {
    id: string;
    name: string;
    position: Position;
    isRunning: boolean;
    runEnergy: number;
    inventory: any[];
    skills: Record<string, number>;
}

export interface Item {
    id: string;
    name: string;
    stackable: boolean;
    quantity: number;
}

export interface Skills {
    attack: number;
    strength: number;
    defence: number;
    hitpoints: number;
    prayer: number;
    magic: number;
    ranged: number;
    mining: number;
    woodcutting: number;
    fishing: number;
}

export interface ChatMessage {
    playerName: string;
    content: string;
    timestamp: number;
}

export interface WorldObject {
    id: string;
    type: string;
    position: Position;
}

export interface GameState {
    tick: number;
    players: Map<string, Player>;
    chatMessages: ChatMessage[];
    worldObjects: Map<string, WorldObject>;
}

export type GameClientMessage = {
    playerId: string;
} & ({
    type: 'MOVE';
    position: Position;
} | {
    type: 'CHAT';
    content: string;
} | {
    type: 'INTERACT';
    targetId: string;
});

export type GameServerMessage = {
    type: 'INIT';
    playerId: string;
    gameState: GameState;
} | {
    type: 'STATE_UPDATE';
    gameState: GameState;
} | {
    type: 'PLAYER_JOINED';
    player: Player;
} | {
    type: 'PLAYER_LEFT';
    playerId: string;
} | {
    type: 'CHAT_MESSAGE';
    message: ChatMessage;
} | {
    type: 'ERROR';
    message: string;
};

export interface WorldTile {
    x: number;
    y: number;
    walkable: boolean;
    type: 'ground' | 'water' | 'wall' | 'object';
}

export interface Area {
    id: string;
    name: string;
    tiles: WorldTile[][];
    npcs: string[];
    objects: WorldObject[];
}

export interface GameConfig {
    tickRate: number;
    maxPlayers: number;
    startPosition: Position;
    defaultSkills: Record<string, number>;
} 