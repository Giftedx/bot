import { WebSocket, WebSocketServer } from 'ws';
import { GameState, GameClientMessage, GameServerMessage, Player, Position } from '../types';
import { StateManager } from './StateManager';
import { InputHandler } from './InputHandler';
import { Logger } from '../utils/Logger';

export class GameServer {
    private wss: WebSocketServer;
    private stateManager: StateManager;
    private inputHandler: InputHandler;
    private clients: Map<string, WebSocket>;
    private logger: Logger;

    constructor(port: number) {
        this.wss = new WebSocketServer({ port });
        this.stateManager = new StateManager();
        this.inputHandler = new InputHandler(this.stateManager);
        this.clients = new Map();
        this.logger = new Logger('GameServer');

        this.setupWebSocket();
        this.startGameLoop();
    }

    private setupWebSocket(): void {
        this.wss.on('connection', (ws: WebSocket, req) => {
            const clientId = req.headers['client-id'] as string;
            if (!clientId) {
                ws.close(1002, 'Client ID required');
                return;
            }

            this.handleConnection(clientId, ws);

            ws.on('message', async (data: string) => {
                try {
                    const message = JSON.parse(data) as GameClientMessage;
                    await this.handleMessage(clientId, message);
                } catch (error) {
                    this.logger.error(`Error handling message from ${clientId}:`, error);
                    this.sendError(ws, 'Invalid message format');
                }
            });

            ws.on('close', () => {
                this.handleDisconnect(clientId);
            });

            ws.on('error', (error) => {
                this.logger.error(`WebSocket error for ${clientId}:`, error);
                this.handleDisconnect(clientId);
            });
        });
    }

    private handleConnection(clientId: string, ws: WebSocket): void {
        // Check if player limit reached
        if (this.clients.size >= this.stateManager.getConfig().maxPlayers) {
            ws.close(1008, 'Server full');
            return;
        }

        this.clients.set(clientId, ws);
        this.stateManager.addPlayer(clientId);
        this.logger.info(`Client connected: ${clientId}`);

        // Send initial state
        this.sendState(clientId);
    }

    private async handleMessage(clientId: string, message: GameClientMessage): Promise<void> {
        const client = this.clients.get(clientId);
        if (!client) return;

        try {
            await this.inputHandler.handleInput(clientId, message);
            this.broadcastState();
        } catch (error) {
            this.logger.error(`Error processing message from ${clientId}:`, error);
            this.sendError(client, error instanceof Error ? error.message : 'Unknown error');
        }
    }

    private handleDisconnect(clientId: string): void {
        this.clients.delete(clientId);
        this.stateManager.removePlayer(clientId);
        this.logger.info(`Client disconnected: ${clientId}`);
        this.broadcastState();
    }

    private startGameLoop(): void {
        this.stateManager.startGameLoop(() => {
            this.broadcastState();
        });
    }

    private broadcastState(): void {
        const state = this.stateManager.getState();
        const message: GameServerMessage = {
            type: 'STATE_UPDATE',
            gameState: state
        };

        const messageStr = JSON.stringify(message);
        for (const [clientId, client] of this.clients) {
            if (client.readyState === WebSocket.OPEN) {
                try {
                    client.send(messageStr);
                } catch (error) {
                    this.logger.error(`Error sending state to ${clientId}:`, error);
                    this.handleDisconnect(clientId);
                }
            }
        }
    }

    private sendState(clientId: string): void {
        const client = this.clients.get(clientId);
        if (!client || client.readyState !== WebSocket.OPEN) return;

        const state = this.stateManager.getState();
        const message: GameServerMessage = {
            type: 'STATE_UPDATE',
            gameState: state
        };

        try {
            client.send(JSON.stringify(message));
        } catch (error) {
            this.logger.error(`Error sending state to ${clientId}:`, error);
            this.handleDisconnect(clientId);
        }
    }

    private sendError(client: WebSocket, error: string): void {
        if (client.readyState !== WebSocket.OPEN) return;

        const message: GameServerMessage = {
            type: 'ERROR',
            message: error
        };

        try {
            client.send(JSON.stringify(message));
        } catch (error) {
            this.logger.error('Error sending error message:', error);
        }
    }

    public stop(): void {
        this.stateManager.stopGameLoop();
        this.wss.close();
        this.clients.clear();
        this.logger.info('Game server stopped');
    }
} 