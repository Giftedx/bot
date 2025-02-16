// Plex Activity client-side integration with Discord's Embedded App SDK
import { DiscordSDK } from '@discord/embedded-app-sdk';

class PlexActivityClient {
    constructor(clientId) {
        this.discordSdk = new DiscordSDK(clientId);
        this.auth = null;
        this.currentMedia = null;
        this.state = 'INITIALIZING';
    }

    async initialize() {
        try {
            // Wait for READY payload from Discord client
            await this.discordSdk.ready();
            console.log('Discord SDK is ready');

            // Request necessary permissions
            const { code } = await this.discordSdk.commands.authorize({
                client_id: this.discordSdk.clientId,
                response_type: 'code',
                state: '',
                prompt: 'none',
                scope: [
                    'identify',
                    'guilds',
                    'voice',
                    'activities.write',
                    'rpc',
                    'rpc.activities.write'
                ],
            });

            // Exchange code for access token via backend
            const response = await fetch('/.proxy/api/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ code }),
            });
            const { access_token } = await response.json();

            // Authenticate with Discord client
            this.auth = await this.discordSdk.commands.authenticate({
                access_token,
            });

            if (!this.auth) {
                throw new Error('Authentication failed');
            }

            this.state = 'READY';
            return true;

        } catch (error) {
            console.error('Failed to initialize Discord SDK:', error);
            this.state = 'ERROR';
            return false;
        }
    }

    async startActivity(channelId) {
        try {
            if (this.state !== 'READY') {
                throw new Error('SDK not ready');
            }

            // Get channel info
            const channel = await this.discordSdk.commands.getChannel({
                channel_id: channelId
            });

            // Start activity in channel
            await this.discordSdk.commands.setActivity({
                type: 'ACTIVITY',
                name: 'Plex Watch Together',
                details: 'Choosing media',
                state: 'INITIALIZED',
                party: {
                    id: channelId,
                    size: [1, channel.user_limit || 99]
                },
                instance: true
            });

            this.state = 'ACTIVE';
            return true;

        } catch (error) {
            console.error('Failed to start activity:', error);
            return false;
        }
    }

    async updateMediaState(mediaInfo) {
        try {
            if (this.state !== 'ACTIVE') {
                throw new Error('No active activity');
            }

            this.currentMedia = mediaInfo;

            // Update activity state with media info
            await this.discordSdk.commands.setActivity({
                type: 'ACTIVITY',
                name: 'Plex Watch Together',
                details: this._getMediaDetails(mediaInfo),
                state: 'PLAYING',
                timestamps: {
                    start: Date.now()
                },
                assets: {
                    large_image: mediaInfo.thumb || 'plex_logo',
                    large_text: mediaInfo.title,
                    small_image: 'plex_icon',
                    small_text: 'Plex'
                },
                instance: true
            });

            return true;

        } catch (error) {
            console.error('Failed to update media state:', error);
            return false;
        }
    }

    async pauseMedia() {
        if (!this.currentMedia) return false;

        try {
            await this.discordSdk.commands.setActivity({
                ...this._getBaseActivity(),
                state: 'PAUSED'
            });
            return true;
        } catch (error) {
            console.error('Failed to pause media:', error);
            return false;
        }
    }

    async resumeMedia() {
        if (!this.currentMedia) return false;

        try {
            await this.discordSdk.commands.setActivity({
                ...this._getBaseActivity(),
                state: 'PLAYING',
                timestamps: {
                    start: Date.now()
                }
            });
            return true;
        } catch (error) {
            console.error('Failed to resume media:', error);
            return false;
        }
    }

    async endActivity() {
        try {
            await this.discordSdk.commands.setActivity(null);
            this.state = 'READY';
            this.currentMedia = null;
            return true;
        } catch (error) {
            console.error('Failed to end activity:', error);
            return false;
        }
    }

    _getMediaDetails(mediaInfo) {
        if (mediaInfo.type === 'episode') {
            return `Watching ${mediaInfo.showTitle} - ${mediaInfo.title}`;
        } else if (mediaInfo.type === 'track') {
            return `Listening to ${mediaInfo.title} by ${mediaInfo.artist}`;
        }
        return `Watching ${mediaInfo.title}`;
    }

    _getBaseActivity() {
        if (!this.currentMedia) return null;

        return {
            type: 'ACTIVITY',
            name: 'Plex Watch Together',
            details: this._getMediaDetails(this.currentMedia),
            assets: {
                large_image: this.currentMedia.thumb || 'plex_logo',
                large_text: this.currentMedia.title,
                small_image: 'plex_icon',
                small_text: 'Plex'
            },
            instance: true
        };
    }

    // Event handlers
    onReady(callback) {
        this.discordSdk.subscribe('READY', callback);
    }

    onError(callback) {
        this.discordSdk.subscribe('ERROR', callback);
    }

    onClose(callback) {
        this.discordSdk.subscribe('CLOSE', callback);
    }
}

export default PlexActivityClient; 