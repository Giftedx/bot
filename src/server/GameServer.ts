import { WebSocket, WebSocketServer } from 'ws';
import { GameState, Player, GameClientMessage, GameServerMessage, Position } from '../types';
import { randomUUID } from 'crypto';

/**
 * Represents the main game server handling WebSocket connections and game state.
 */
export class GameServer {
    private wss: WebSocketServer;
    private gameState: GameState;
    private clientMap: Map<WebSocket, string> = new Map();
    private tickInterval: NodeJS.Timeout | null = null;
    private readonly TICK_RATE = 600; // ms

    /**
     * Initializes the GameServer instance.
     * @param port - The port number to listen on.
     */
    constructor(port: number) {
        this.wss = new WebSocketServer({ port });
        this.gameState = {
            tick: 0,
            players: new Map(),
            chatMessages: [],
            worldObjects: new Map()
        };

        this.setupWebSocketServer();
        this.startGameLoop();
    }

    /**
     * Sets up the WebSocket server event listeners.
     */
    private setupWebSocketServer(): void {
        this.wss.on('connection', (ws: WebSocket) => {
            const playerId = randomUUID();
            const player: Player = {
                id: playerId,
                name: `Player${this.gameState.players.size + 1}`,
                position: { x: 0, y: 0 },
                isRunning: false,
                runEnergy: 100,
                inventory: [],
                skills: {
                    attack: 1,
                    strength: 1,
                    defence: 1,
                    hitpoints: 10,
                    prayer: 1,
                    magic: 1,
                    ranged: 1,
                    mining: 1,
                    woodcutting: 1,
                    fishing: 1
                }
            };

            // Add player to game state
            this.gameState.players.set(playerId, player);
            this.clientMap.set(ws, playerId);

            // Send initial game state
            this.sendMessage(ws, {
                type: 'INIT',
                playerId,
                gameState: this.gameState
            });

            // Broadcast new player to other clients
            this.broadcast({
                type: 'PLAYER_JOINED',
                player
            }, ws);

            ws.on('message', (data: string) => {
                try {
                    const message: GameClientMessage = JSON.parse(data.toString());
                    this.handleClientMessage(ws, message);
                } catch (error) {
                    console.error('Error parsing message:', error);
                    this.sendMessage(ws, {
                        type: 'ERROR',
                        message: 'Invalid message format'
                    });
                }
            });

            ws.on('close', () => {
                const playerId = this.clientMap.get(ws);
                if (playerId) {
                    this.gameState.players.delete(playerId);
                    this.clientMap.delete(ws);
                    this.broadcast({
                        type: 'PLAYER_LEFT',
                        playerId
                    });
                }
            });
        });
    }

    /**
     * Handles incoming messages from clients.
     * @param ws - The WebSocket connection.
     * @param message - The parsed message object.
     */
    private handleClientMessage(ws: WebSocket, message: GameClientMessage): void {
        const playerId = this.clientMap.get(ws);
        if (!playerId || message.playerId !== playerId) {
            this.sendMessage(ws, {
                type: 'ERROR',
                message: 'Invalid player ID'
            });
            return;
        }

        const player = this.gameState.players.get(playerId);
        if (!player) {
            this.sendMessage(ws, {
                type: 'ERROR',
                message: 'Player not found'
            });
            return;
        }

        switch (message.type) {
            case 'MOVE':
                this.handlePlayerMove(player, message.position);
                break;
            case 'CHAT':
                this.handleChatMessage(player, message.content);
                break;
            case 'INTERACT':
                this.handleInteraction(player, message.targetId);
                break;
        }
    }

    /**
     * Updates a player's position.
     * @param player - The player object.
     * @param newPosition - The new coordinates.
     */
    private handlePlayerMove(player: Player, newPosition: Position): void {
        // Simple collision detection (you can expand this)
        if (this.isValidPosition(newPosition)) {
            player.position = newPosition;
            this.broadcastGameState();
        }
    }

    /**
     * Processes a chat message from a player.
     * @param player - The player sending the message.
     * @param content - The message content.
     */
    private handleChatMessage(player: Player, content: string): void {
        const message = {
            playerName: player.name,
            content: content.slice(0, 100), // Limit message length
            timestamp: Date.now()
        };

        this.gameState.chatMessages.push(message);
        if (this.gameState.chatMessages.length > 100) {
            this.gameState.chatMessages.shift();
        }

        this.broadcast({
            type: 'CHAT_MESSAGE',
            message
        });
    }

    /**
     * Handles player interactions with the world.
     * @param player - The player initiating interaction.
     * @param targetId - The ID of the target object/entity.
     */
    private handleInteraction(player: Player, targetId: string): void {
        // Handle player interactions with objects or other players
        // This is a placeholder for future implementation
    }

    /**
     * Validates if a position is within the world bounds.
     * @param position - The position to check.
     * @returns True if valid, false otherwise.
     */
    private isValidPosition(position: Position): boolean {
        // Simple boundary check (you can expand this)
        return position.x >= 0 && position.x < 100 && 
               position.y >= 0 && position.y < 100;
    }

    /**
     * Starts the main game loop.
     */
    private startGameLoop(): void {
        this.tickInterval = setInterval(() => {
            this.gameState.tick++;
            // Update game state here (e.g., NPCs, combat, etc.)
            this.broadcastGameState();
        }, this.TICK_RATE);
    }

    /**
     * Broadcasts the full game state to all connected clients.
     */
    private broadcastGameState(): void {
        this.broadcast({
            type: 'STATE_UPDATE',
            gameState: this.gameState
        });
    }

    /**
     * Sends a message to a specific client.
     * @param client - The WebSocket client.
     * @param message - The message to send.
     */
    private sendMessage(client: WebSocket, message: GameServerMessage): void {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify(message));
        }
    }

    /**
     * Broadcasts a message to all clients, optionally excluding one.
     * @param message - The message to broadcast.
     * @param exclude - (Optional) A client to exclude from the broadcast.
     */
    private broadcast(message: GameServerMessage, exclude?: WebSocket): void {
        this.wss.clients.forEach(client => {
            if (client !== exclude && client.readyState === WebSocket.OPEN) {
                client.send(JSON.stringify(message));
            }
        });
    }

    /**
     * Stops the server and closes all connections.
     */
    public stop(): void {
        if (this.tickInterval) {
            clearInterval(this.tickInterval);
        }
        this.wss.close();
    }
}
