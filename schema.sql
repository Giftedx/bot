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

-- Battle System Tables

-- Battle History
CREATE TABLE IF NOT EXISTS battle_history (
    battle_id TEXT PRIMARY KEY,
    battle_type TEXT NOT NULL,
    challenger_id BIGINT NOT NULL,
    opponent_id BIGINT NOT NULL,
    winner_id BIGINT,
    start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    turns INTEGER NOT NULL DEFAULT 0,
    battle_data JSONB
);

-- Battle Statistics
CREATE TABLE IF NOT EXISTS battle_stats (
    player_id BIGINT NOT NULL,
    battle_type TEXT NOT NULL,
    total_battles INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    win_streak INTEGER DEFAULT 0,
    highest_streak INTEGER DEFAULT 0,
    total_damage_dealt BIGINT DEFAULT 0,
    total_damage_taken BIGINT DEFAULT 0,
    favorite_move TEXT,
    move_usage JSONB DEFAULT '{}',
    last_battle_time TIMESTAMP,
    PRIMARY KEY (player_id, battle_type)
);

-- Battle Rewards
CREATE TABLE IF NOT EXISTS battle_rewards (
    reward_id SERIAL PRIMARY KEY,
    battle_id TEXT NOT NULL REFERENCES battle_history(battle_id),
    player_id BIGINT NOT NULL,
    xp_gained INTEGER NOT NULL,
    coins_gained INTEGER NOT NULL,
    items_gained JSONB,
    special_rewards JSONB,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Battle Ratings
CREATE TABLE IF NOT EXISTS battle_ratings (
    player_id BIGINT NOT NULL,
    battle_type TEXT NOT NULL,
    rating INTEGER NOT NULL DEFAULT 1000,
    uncertainty FLOAT NOT NULL DEFAULT 350,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, battle_type)
);

-- Battle Achievements
CREATE TABLE IF NOT EXISTS battle_achievements (
    achievement_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    battle_type TEXT NOT NULL,
    requirement_type TEXT NOT NULL,
    requirement_value INTEGER NOT NULL,
    reward_type TEXT,
    reward_value JSONB
);

-- Player Battle Achievements
CREATE TABLE IF NOT EXISTS player_achievements (
    player_id BIGINT NOT NULL,
    achievement_id INTEGER NOT NULL REFERENCES battle_achievements(achievement_id),
    earned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, achievement_id)
);

-- Create indexes
CREATE INDEX idx_osrs_characters_user_id ON osrs_characters(user_id);
CREATE INDEX idx_osrs_stats_character_id ON osrs_stats(character_id);
CREATE INDEX idx_pokemon_user_id ON pokemon(user_id);
CREATE INDEX idx_active_spawns_channel ON active_spawns(channel_id) WHERE NOT caught;
CREATE INDEX idx_custom_commands_name ON custom_commands(name);
CREATE INDEX idx_pets_owner ON pets(owner_id);
CREATE INDEX idx_plex_sessions_channel ON plex_sessions(channel_id);
CREATE INDEX IF NOT EXISTS idx_battle_history_players ON battle_history(challenger_id, opponent_id);
CREATE INDEX IF NOT EXISTS idx_battle_history_type ON battle_history(battle_type);
CREATE INDEX IF NOT EXISTS idx_battle_stats_type ON battle_stats(battle_type);
CREATE INDEX IF NOT EXISTS idx_battle_rewards_player ON battle_rewards(player_id);
CREATE INDEX IF NOT EXISTS idx_battle_ratings_type ON battle_ratings(battle_type);

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

-- Insert default achievements
INSERT INTO battle_achievements (name, description, battle_type, requirement_type, requirement_value, reward_type, reward_value)
VALUES
    ('OSRS Warrior', 'Win 10 OSRS battles', 'osrs', 'wins', 10, 'coins', '{"amount": 1000}'),
    ('Pokemon Master', 'Win 10 Pokemon battles', 'pokemon', 'wins', 10, 'items', '{"rare_candy": 3}'),
    ('Pet Champion', 'Win 10 pet battles', 'pet', 'wins', 10, 'loyalty', '{"points": 100}')
ON CONFLICT DO NOTHING;
