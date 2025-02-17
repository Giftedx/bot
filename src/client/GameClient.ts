import { GameState, GameClientMessage, GameServerMessage, Position } from '../types';
import { Renderer } from './Renderer';

export class GameClient {
    private ws: WebSocket;
    private renderer: Renderer;
    private gameState: GameState;
    private playerId: string | null = null;

    constructor(serverUrl: string, canvas: HTMLCanvasElement) {
        this.ws = new WebSocket(serverUrl);
        this.renderer = new Renderer(canvas);
        this.gameState = {
            tick: 0,
            players: new Map(),
            chatMessages: [],
            worldObjects: new Map()
        };

        this.setupWebSocket();
        this.setupEventListeners(canvas);
        this.startRenderLoop();
    }

    private setupWebSocket(): void {
        this.ws.onopen = () => {
            console.log('Connected to game server');
        };

        this.ws.onmessage = (event) => {
            const message: GameServerMessage = JSON.parse(event.data);
            this.handleServerMessage(message);
        };

        this.ws.onclose = () => {
            console.log('Disconnected from game server');
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    private setupEventListeners(canvas: HTMLCanvasElement): void {
        // Handle mouse clicks for movement
        canvas.addEventListener('click', (event) => {
            const worldPos = this.renderer.handleClick(event);
            this.sendMoveMessage(worldPos);
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            this.renderer.resize();
        });

        // Handle chat input
        const chatInput = document.getElementById('chatInput') as HTMLInputElement;
        if (chatInput) {
            chatInput.addEventListener('keypress', (event) => {
                if (event.key === 'Enter' && chatInput.value.trim()) {
                    this.sendChatMessage(chatInput.value.trim());
                    chatInput.value = '';
                }
            });
        }
    }

    private handleServerMessage(message: GameServerMessage): void {
        switch (message.type) {
            case 'INIT':
                this.playerId = message.playerId;
                this.gameState = message.gameState;
                break;
            case 'STATE_UPDATE':
                this.gameState = message.gameState;
                break;
            case 'PLAYER_JOINED':
                this.gameState.players.set(message.player.id, message.player);
                break;
            case 'PLAYER_LEFT':
                this.gameState.players.delete(message.playerId);
                break;
            case 'CHAT_MESSAGE':
                this.gameState.chatMessages.push(message.message);
                if (this.gameState.chatMessages.length > 100) {
                    this.gameState.chatMessages.shift();
                }
                break;
        }
    }

    private sendMoveMessage(position: Position): void {
        if (this.ws.readyState === WebSocket.OPEN && this.playerId) {
            const message: GameClientMessage = {
                type: 'MOVE',
                position,
                playerId: this.playerId
            };
            this.ws.send(JSON.stringify(message));
        }
    }

    private sendChatMessage(content: string): void {
        if (this.ws.readyState === WebSocket.OPEN && this.playerId) {
            const message: GameClientMessage = {
                type: 'CHAT',
                content,
                playerId: this.playerId
            };
            this.ws.send(JSON.stringify(message));
        }
    }

    private startRenderLoop(): void {
        const render = () => {
            this.renderer.render(this.gameState);
            requestAnimationFrame(render);
        };
        requestAnimationFrame(render);
    }

    public disconnect(): void {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.close();
        }
    }
} 