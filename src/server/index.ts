import { GameServer } from './GameServer';

const PORT = 3000;
const server = new GameServer(PORT);

console.log(`Game server running on ws://localhost:${PORT}`);

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('Shutting down server...');
    server.stop();
    process.exit(0);
}); 