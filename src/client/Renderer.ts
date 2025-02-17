import { GameState, Position, Player } from '../types';

export class Renderer {
    private canvas: HTMLCanvasElement;
    private ctx: CanvasRenderingContext2D;
    private tileSize: number = 32;
    private colors = {
        background: '#000000',
        grid: '#333333',
        player: '#ffffff',
        water: '#0000ff',
        wall: '#666666',
        text: '#ffffff'
    };

    constructor(canvas: HTMLCanvasElement) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d')!;
        this.setupCanvas();
    }

    private setupCanvas(): void {
        // Set up for HiDPI displays
        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();

        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.ctx.scale(dpr, dpr);

        // Set canvas style size
        this.canvas.style.width = `${rect.width}px`;
        this.canvas.style.height = `${rect.height}px`;
    }

    public render(state: GameState): void {
        this.clear();
        this.drawGrid();
        this.drawPlayers(state.players);
        this.drawChat(state.chatMessages);
        this.drawUI(state);
    }

    private clear(): void {
        this.ctx.fillStyle = this.colors.background;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    private drawGrid(): void {
        this.ctx.strokeStyle = this.colors.grid;
        this.ctx.lineWidth = 1;

        for (let x = 0; x < this.canvas.width; x += this.tileSize) {
            for (let y = 0; y < this.canvas.height; y += this.tileSize) {
                this.ctx.strokeRect(x, y, this.tileSize, this.tileSize);
            }
        }
    }

    private drawPlayers(players: Map<string, Player>): void {
        for (const player of players.values()) {
            this.drawPlayer(player);
        }
    }

    private drawPlayer(player: Player): void {
        const screenPos = this.worldToScreen(player.position);
        
        // Draw player body
        this.ctx.fillStyle = this.colors.player;
        this.ctx.fillRect(
            screenPos.x,
            screenPos.y,
            this.tileSize,
            this.tileSize
        );

        // Draw player name
        this.ctx.fillStyle = this.colors.text;
        this.ctx.font = '12px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(
            player.name,
            screenPos.x + this.tileSize / 2,
            screenPos.y - 5
        );
    }

    private drawChat(messages: { playerName: string; content: string; timestamp: number }[]): void {
        const lastMessages = messages.slice(-5);
        this.ctx.fillStyle = this.colors.text;
        this.ctx.font = '14px Arial';
        this.ctx.textAlign = 'left';

        lastMessages.forEach((msg, i) => {
            const text = `${msg.playerName}: ${msg.content}`;
            this.ctx.fillText(
                text,
                10,
                this.canvas.height - 60 + (i * 20)
            );
        });
    }

    private drawUI(state: GameState): void {
        // Draw game tick
        this.ctx.fillStyle = this.colors.text;
        this.ctx.font = '12px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(`Tick: ${state.tick}`, 10, 20);

        // Draw player count
        this.ctx.fillText(`Players: ${state.players.size}`, 10, 40);
    }

    private worldToScreen(position: Position): Position {
        return {
            x: position.x * this.tileSize,
            y: position.y * this.tileSize
        };
    }

    private screenToWorld(position: Position): Position {
        return {
            x: Math.floor(position.x / this.tileSize),
            y: Math.floor(position.y / this.tileSize)
        };
    }

    public handleClick(event: MouseEvent): Position {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        return this.screenToWorld({ x, y });
    }

    public setTileSize(size: number): void {
        this.tileSize = size;
    }

    public resize(): void {
        this.setupCanvas();
    }
} 