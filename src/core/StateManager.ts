import { GameState, Player, Position, ChatMessage, GameConfig } from '../types';
import { Logger } from '../utils/Logger';

export class StateManager {
    private state: GameState;
    private config: GameConfig;
    private tickInterval: NodeJS.Timeout | null = null;
    private logger: Logger;

    constructor() {
        this.logger = new Logger('StateManager');
        this.config = {
            tickRate: 600, // OSRS uses 600ms ticks
            maxPlayers: 2000,
            startPosition: { x: 3222, y: 3218 }, // Lumbridge spawn
            defaultSkills: {
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

        this.state = {
            players: new Map(),
            chatMessages: [],
            tick: 0,
            worldObjects: new Map()
        };
    }

    public startGameLoop(onTick: () => void): void {
        if (this.tickInterval) return;

        this.tickInterval = setInterval(() => {
            this.processTick();
            onTick();
        }, this.config.tickRate);

        this.logger.info('Game loop started');
    }

    public stopGameLoop(): void {
        if (this.tickInterval) {
            clearInterval(this.tickInterval);
            this.tickInterval = null;
            this.logger.info('Game loop stopped');
        }
    }

    private processTick(): void {
        this.state.tick++;
        this.processMovement();
        this.processRunEnergy();
    }

    private processMovement(): void {
        // Basic movement processing - can be expanded later
        for (const player of this.state.players.values()) {
            if (player.isRunning) {
                player.runEnergy = Math.max(0, player.runEnergy - 0.67);
                if (player.runEnergy === 0) {
                    player.isRunning = false;
                }
            }
        }
    }

    private processRunEnergy(): void {
        for (const player of this.state.players.values()) {
            if (!player.isRunning && player.runEnergy < 100) {
                player.runEnergy = Math.min(100, player.runEnergy + 0.45);
            }
        }
    }

    public addPlayer(id: string): void {
        const newPlayer: Player = {
            id,
            name: `Player${id}`,
            position: this.config.startPosition,
            isRunning: false,
            runEnergy: 100,
            inventory: [],
            skills: { ...this.config.defaultSkills }
        };

        this.state.players.set(id, newPlayer);
        this.logger.info(`Player added: ${id}`);
    }

    public removePlayer(id: string): void {
        this.state.players.delete(id);
        this.logger.info(`Player removed: ${id}`);
    }

    public movePlayer(id: string, newPosition: Position): boolean {
        const player = this.state.players.get(id);
        if (!player) return false;

        if (this.isValidMove(player.position, newPosition)) {
            player.position = newPosition;
            return true;
        }
        return false;
    }

    private isValidMove(from: Position, to: Position): boolean {
        const dx = Math.abs(to.x - from.x);
        const dy = Math.abs(to.y - from.y);
        return dx <= 1 && dy <= 1 && (dx + dy > 0);
    }

    public addChatMessage(message: ChatMessage): void {
        this.state.chatMessages.push(message);
        if (this.state.chatMessages.length > 100) {
            this.state.chatMessages.shift();
        }
    }

    public getState(): GameState {
        return this.state;
    }

    public getConfig(): GameConfig {
        return this.config;
    }

    public getPlayer(id: string): Player | undefined {
        return this.state.players.get(id);
    }

    public setPlayerRunning(id: string, isRunning: boolean): void {
        const player = this.state.players.get(id);
        if (player && player.runEnergy > 0) {
            player.isRunning = isRunning;
        }
    }
} 