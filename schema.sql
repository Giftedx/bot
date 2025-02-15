-- Users table
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    settings JSONB DEFAULT '{}',
    currency INTEGER DEFAULT 0,
    experience INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- OSRS characters table
CREATE TABLE osrs_characters (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    name VARCHAR(255),
    stats JSONB DEFAULT '{}',
    inventory JSONB DEFAULT '{}',
    world INTEGER,
    last_trained TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- OSRS stats table
CREATE TABLE osrs_stats (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES osrs_characters(id),
    skill VARCHAR(50),
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    last_trained TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Pokemon table
CREATE TABLE pokemon (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    pokemon_id INTEGER,
    name VARCHAR(255),
    level INTEGER DEFAULT 1,
    stats JSONB DEFAULT '{}',
    moves JSONB DEFAULT '[]',
    caught_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Active spawns table
CREATE TABLE active_spawns (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT,
    pokemon_id INTEGER,
    level INTEGER,
    caught BOOLEAN DEFAULT FALSE,
    caught_by BIGINT REFERENCES users(id),
    spawned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Custom commands table
CREATE TABLE custom_commands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    response TEXT,
    creator_id BIGINT REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Pet system table
CREATE TABLE pets (
    id SERIAL PRIMARY KEY,
    owner_id BIGINT REFERENCES users(id),
    name VARCHAR(255),
    type VARCHAR(50),
    stats JSONB DEFAULT '{}',
    training_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Plex sessions table
CREATE TABLE plex_sessions (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT,
    media_key VARCHAR(255),
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    user_id BIGINT REFERENCES users(id)
);

-- Create indexes
CREATE INDEX idx_osrs_characters_user_id ON osrs_characters(user_id);
CREATE INDEX idx_osrs_stats_character_id ON osrs_stats(character_id);
CREATE INDEX idx_pokemon_user_id ON pokemon(user_id);
CREATE INDEX idx_active_spawns_channel ON active_spawns(channel_id) WHERE NOT caught;
CREATE INDEX idx_custom_commands_name ON custom_commands(name);
CREATE INDEX idx_pets_owner ON pets(owner_id);
CREATE INDEX idx_plex_sessions_channel ON plex_sessions(channel_id);

-- Create functions
CREATE OR REPLACE FUNCTION update_osrs_level()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate new level based on XP
    -- This is a simplified version of OSRS level calculation
    NEW.level = FLOOR(POWER(NEW.xp / 4, 1/3));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER trigger_update_osrs_level
    BEFORE INSERT OR UPDATE OF xp ON osrs_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_osrs_level(); 