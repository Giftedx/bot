declare module 'node-plex-api' {
    interface PlexAPIOptions {
        hostname: string;
        port?: number;
        token?: string;
        https?: boolean;
        options?: {
            identifier?: string;
            product?: string;
            version?: string;
            deviceName?: string;
        };
    }

    interface PlexMetadata {
        title: string;
        duration: number;
        type: string;
        thumb?: string;
        year?: number;
        summary?: string;
        rating?: number;
        studio?: string;
        Director?: Array<{ tag: string }>;
        Genre?: Array<{ tag: string }>;
    }

    interface PlexResponse {
        MediaContainer: {
            Metadata: PlexMetadata[];
        };
    }

    export class PlexAPI {
        constructor(options: PlexAPIOptions);
        query(path: string): Promise<PlexResponse>;
        _generateRelativeUrl(path: string): string;
    }
} 