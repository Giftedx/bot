import { GameClientMessage, Position } from '../types';
import { StateManager } from './StateManager';
import { Logger } from '../utils/Logger';

export class InputHandler {
    private logger: Logger;

    constructor(private stateManager: StateManager) {
        this.logger = new Logger('InputHandler');
    }

    public async handleInput(clientId: string, message: GameClientMessage): Promise<void> {
        const player = this.stateManager.getPlayer(clientId);
        if (!player) {
            throw new Error('Player not found');
        }

        switch (message.type) {
            case 'MOVE':
                this.handleMove(clientId, message.position);
                break;
            case 'CHAT':
                this.handleChat(clientId, message.content);
                break;
            case 'INTERACT':
                this.handleInteraction(clientId, message.targetId);
                break;
            default:
                throw new Error('Unknown message type');
        }
    }

    private handleMove(clientId: string, position: Position): void {
        if (this.stateManager.movePlayer(clientId, position)) {
            this.logger.debug(`Player ${clientId} moved to (${position.x}, ${position.y})`);
        } else {
            throw new Error('Invalid move');
        }
    }

    private handleChat(clientId: string, content: string): void {
        const player = this.stateManager.getPlayer(clientId);
        if (!player) return;

        // Basic chat filtering
        const filteredContent = this.filterChatMessage(content);
        
        this.stateManager.addChatMessage({
            playerName: player.name,
            content: filteredContent,
            timestamp: Date.now()
        });

        this.logger.debug(`Player ${clientId} sent message: ${filteredContent}`);
    }

    private handleInteraction(clientId: string, targetId: string): void {
        // Basic interaction handling - can be expanded later
        this.logger.debug(`Player ${clientId} interacting with ${targetId}`);
    }

    private filterChatMessage(content: string): string {
        // Basic chat filtering - can be expanded with more sophisticated filtering
        return content
            .trim()
            .slice(0, 100) // Max length
            .replace(/[^\w\s!?.,]/g, ''); // Basic sanitization
    }
} 