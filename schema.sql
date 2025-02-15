-- Core Tables
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    settings JSONB DEFAULT '{}'
);

-- OSRS Character System
CREATE TABLE IF NOT EXISTS characters (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    combat_level INTEGER DEFAULT 3,
    total_level INTEGER DEFAULT 32,
    total_xp BIGINT DEFAULT 1154,
    quest_points INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, name)
);

-- Skills System
CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    skill_name VARCHAR(50) NOT NULL,
    level INTEGER DEFAULT 1,
    xp BIGINT DEFAULT 0,
    last_trained TIMESTAMP WITH TIME ZONE,
    UNIQUE(character_id, skill_name)
);

-- Bank & Items System
CREATE TABLE IF NOT EXISTS banks (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    tab INTEGER DEFAULT 0,
    items JSONB DEFAULT '{}',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    item_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    examine TEXT,
    tradeable BOOLEAN DEFAULT true,
    stackable BOOLEAN DEFAULT false,
    noted BOOLEAN DEFAULT false,
    noteable BOOLEAN DEFAULT false,
    linked_id INTEGER REFERENCES items(item_id),
    cost INTEGER DEFAULT 0,
    low_alchemy INTEGER,
    high_alchemy INTEGER,
    weight DECIMAL(10,3),
    buy_limit INTEGER,
    quest_item BOOLEAN DEFAULT false,
    release_date DATE,
    wiki_url TEXT,
    wiki_exchange TEXT
);

-- Grand Exchange System
CREATE TABLE IF NOT EXISTS ge_history (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES items(item_id),
    price INTEGER NOT NULL,
    volume INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ge_offers (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    item_id INTEGER REFERENCES items(item_id),
    quantity INTEGER NOT NULL,
    price_per_item INTEGER NOT NULL,
    is_buy BOOLEAN NOT NULL,
    completed BOOLEAN DEFAULT false,
    quantity_filled INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE
);

-- Quest System
CREATE TABLE IF NOT EXISTS quests (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    difficulty VARCHAR(50),
    quest_points INTEGER DEFAULT 1,
    requirements JSONB,
    rewards JSONB
);

CREATE TABLE IF NOT EXISTS character_quests (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    quest_id INTEGER REFERENCES quests(id),
    status VARCHAR(50) DEFAULT 'NOT_STARTED',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(character_id, quest_id)
);

-- Achievement System
CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    difficulty VARCHAR(50),
    requirements JSONB,
    rewards JSONB
);

CREATE TABLE IF NOT EXISTS character_achievements (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    achievement_id INTEGER REFERENCES achievements(id),
    completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(character_id, achievement_id)
);

-- Collection Log
CREATE TABLE IF NOT EXISTS collection_log (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    category VARCHAR(255) NOT NULL,
    item_id INTEGER REFERENCES items(item_id),
    obtained BOOLEAN DEFAULT false,
    obtained_at TIMESTAMP WITH TIME ZONE,
    quantity INTEGER DEFAULT 0,
    UNIQUE(character_id, category, item_id)
);

-- Combat System
CREATE TABLE IF NOT EXISTS combat_stats (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    attack_style VARCHAR(50),
    weapon_type VARCHAR(50),
    combat_stats JSONB DEFAULT '{}',
    prayer_points INTEGER DEFAULT 99,
    special_attack_energy INTEGER DEFAULT 100,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Equipment System
CREATE TABLE IF NOT EXISTS equipment (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    slot VARCHAR(50) NOT NULL,
    item_id INTEGER REFERENCES items(item_id),
    quantity INTEGER DEFAULT 1,
    UNIQUE(character_id, slot)
);

-- Users table
CREATE TABLE IF NOT EXISTS users_table (
    id BIGINT PRIMARY KEY,
    settings JSONB DEFAULT '{}',
    currency INTEGER DEFAULT 0,
    experience INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- OSRS characters table
CREATE TABLE IF NOT EXISTS osrs_characters (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users_table(id),
    name VARCHAR(255),
    stats JSONB DEFAULT '{}',
    inventory JSONB DEFAULT '{}',
    world INTEGER,
    last_trained TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- OSRS stats table
CREATE TABLE IF NOT EXISTS osrs_stats (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES osrs_characters(id),
    skill VARCHAR(50),
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    last_trained TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Pokemon table
CREATE TABLE IF NOT EXISTS pokemon (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users_table(id),
    pokemon_id INTEGER,
    name VARCHAR(255),
    level INTEGER DEFAULT 1,
    stats JSONB DEFAULT '{}',
    moves JSONB DEFAULT '[]',
    caught_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Active spawns table
CREATE TABLE IF NOT EXISTS active_spawns (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT,
    pokemon_id INTEGER,
    level INTEGER,
    caught BOOLEAN DEFAULT FALSE,
    caught_by BIGINT REFERENCES users_table(id),
    spawned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Guild settings
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id BIGINT PRIMARY KEY,
    prefix VARCHAR(5) DEFAULT '!',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Custom commands
CREATE TABLE IF NOT EXISTS custom_commands (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    name VARCHAR(50) NOT NULL,
    response TEXT NOT NULL,
    creator_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uses INTEGER DEFAULT 0,
    UNIQUE(guild_id, name)
);

-- Welcome settings
CREATE TABLE IF NOT EXISTS welcome_settings (
    guild_id BIGINT PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    message TEXT NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Autorole settings
CREATE TABLE IF NOT EXISTS autorole (
    guild_id BIGINT PRIMARY KEY,
    role_id BIGINT NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User settings
CREATE TABLE IF NOT EXISTS user_settings (
    user_id BIGINT PRIMARY KEY,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    last_message TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pet system
CREATE TABLE IF NOT EXISTS pets (
    id SERIAL PRIMARY KEY,
    owner_id BIGINT NOT NULL,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(50) NOT NULL,
    stats JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_trained TIMESTAMP,
    UNIQUE(owner_id, name)
);

-- Marriage system
CREATE TABLE IF NOT EXISTS marriages (
    id SERIAL PRIMARY KEY,
    user1_id BIGINT NOT NULL,
    user2_id BIGINT NOT NULL,
    married_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user1_id),
    UNIQUE(user2_id)
);

-- Playlists
CREATE TABLE IF NOT EXISTS playlists (
    id SERIAL PRIMARY KEY,
    owner_id BIGINT NOT NULL,
    name VARCHAR(50) NOT NULL,
    tracks JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner_id, name)
);

-- Plex sessions table
CREATE TABLE IF NOT EXISTS plex_sessions (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT,
    media_key VARCHAR(255),
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    user_id BIGINT REFERENCES users_table(id)
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

-- Elite Four progress tracking
CREATE TABLE IF NOT EXISTS elite_four_progress (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users_table(id),
    member_id VARCHAR(50) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, member_id)
);

-- Elite Four champions
CREATE TABLE IF NOT EXISTS elite_four_champions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users_table(id),
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Champion victories
CREATE TABLE IF NOT EXISTS champion_victories (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users_table(id),
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Gym rematches
CREATE TABLE IF NOT EXISTS gym_rematches (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users_table(id),
    gym_id VARCHAR(50) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, gym_id)
);

-- Elite Four rematches
CREATE TABLE IF NOT EXISTS elite_four_rematches (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users_table(id),
    member_id VARCHAR(50) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, member_id)
);

-- Pokemon tournaments
CREATE TABLE IF NOT EXISTS pokemon_tournaments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending',
    max_participants INTEGER,
    rules JSONB DEFAULT '{}',
    prizes JSONB DEFAULT '{}',
    winner_id BIGINT REFERENCES users_table(id)
);

-- Tournament participants
CREATE TABLE IF NOT EXISTS tournament_participants (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES pokemon_tournaments(id),
    user_id BIGINT REFERENCES users_table(id),
    team JSONB DEFAULT '[]',
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    eliminated BOOLEAN DEFAULT FALSE,
    UNIQUE(tournament_id, user_id)
);

-- Tournament matches
CREATE TABLE IF NOT EXISTS tournament_matches (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES pokemon_tournaments(id),
    round INTEGER NOT NULL,
    player1_id BIGINT REFERENCES users_table(id),
    player2_id BIGINT REFERENCES users_table(id),
    winner_id BIGINT REFERENCES users_table(id),
    battle_data JSONB DEFAULT '{}',
    scheduled_time TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending'
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_osrs_characters_user_id ON osrs_characters(user_id);
CREATE INDEX IF NOT EXISTS idx_osrs_stats_character_id ON osrs_stats(character_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_user_id ON pokemon(user_id);
CREATE INDEX IF NOT EXISTS idx_active_spawns_channel ON active_spawns(channel_id) WHERE NOT caught;
CREATE INDEX IF NOT EXISTS idx_custom_commands_guild_id ON custom_commands(guild_id);
CREATE INDEX IF NOT EXISTS idx_pets_owner_id ON pets(owner_id);
CREATE INDEX IF NOT EXISTS idx_marriages_users ON marriages(user1_id, user2_id);
CREATE INDEX IF NOT EXISTS idx_playlists_owner ON playlists(owner_id);
CREATE INDEX IF NOT EXISTS idx_plex_sessions_channel ON plex_sessions(channel_id);

-- Battle system indexes
CREATE INDEX IF NOT EXISTS idx_battle_history_players ON battle_history(challenger_id, opponent_id);
CREATE INDEX IF NOT EXISTS idx_battle_history_type ON battle_history(battle_type);
CREATE INDEX IF NOT EXISTS idx_battle_stats_type ON battle_stats(battle_type);
CREATE INDEX IF NOT EXISTS idx_battle_rewards_player ON battle_rewards(player_id);
CREATE INDEX IF NOT EXISTS idx_battle_ratings_type ON battle_ratings(battle_type);

-- Elite Four and tournament indexes
CREATE INDEX IF NOT EXISTS idx_elite_four_progress_user ON elite_four_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_elite_four_champions_user ON elite_four_champions(user_id);
CREATE INDEX IF NOT EXISTS idx_champion_victories_user ON champion_victories(user_id);
CREATE INDEX IF NOT EXISTS idx_gym_rematches_user ON gym_rematches(user_id);
CREATE INDEX IF NOT EXISTS idx_elite_four_rematches_user ON elite_four_rematches(user_id);
CREATE INDEX IF NOT EXISTS idx_tournament_participants_tournament ON tournament_participants(tournament_id);
CREATE INDEX IF NOT EXISTS idx_tournament_matches_tournament ON tournament_matches(tournament_id);

-- Functions and triggers
CREATE OR REPLACE FUNCTION update_osrs_level()
RETURNS TRIGGER AS $$
BEGIN
    NEW.level = FLOOR(POWER((NEW.xp / 4), (1.0/3)));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER trigger_update_osrs_level
    BEFORE INSERT OR UPDATE OF xp ON osrs_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_osrs_level();

CREATE TRIGGER update_guild_settings_updated_at
    BEFORE UPDATE ON guild_settings
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_welcome_settings_updated_at
    BEFORE UPDATE ON welcome_settings
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_autorole_updated_at
    BEFORE UPDATE ON autorole
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_playlists_updated_at
    BEFORE UPDATE ON playlists
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();

-- Include clan system schema
\i clan_schema.sql

-- Include reputation system schema
\i reputation_schema.sql

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_character_user_id ON characters(user_id);
CREATE INDEX IF NOT EXISTS idx_skills_character_id ON skills(character_id);
CREATE INDEX IF NOT EXISTS idx_banks_character_id ON banks(character_id);
CREATE INDEX IF NOT EXISTS idx_ge_history_item_id ON ge_history(item_id);
CREATE INDEX IF NOT EXISTS idx_ge_offers_character_id ON ge_offers(character_id);
CREATE INDEX IF NOT EXISTS idx_character_quests_character_id ON character_quests(character_id);
CREATE INDEX IF NOT EXISTS idx_character_achievements_character_id ON character_achievements(character_id);
CREATE INDEX IF NOT EXISTS idx_collection_log_character_id ON collection_log(character_id);
CREATE INDEX IF NOT EXISTS idx_equipment_character_id ON equipment(character_id);

-- Add foreign key constraints with cascade delete
ALTER TABLE skills
    DROP CONSTRAINT IF EXISTS skills_character_id_fkey,
    ADD CONSTRAINT skills_character_id_fkey
    FOREIGN KEY (character_id)
    REFERENCES characters(id)
    ON DELETE CASCADE;

ALTER TABLE banks
    DROP CONSTRAINT IF EXISTS banks_character_id_fkey,
    ADD CONSTRAINT banks_character_id_fkey
    FOREIGN KEY (character_id)
    REFERENCES characters(id)
    ON DELETE CASCADE;

ALTER TABLE character_quests
    DROP CONSTRAINT IF EXISTS character_quests_character_id_fkey,
    ADD CONSTRAINT character_quests_character_id_fkey
    FOREIGN KEY (character_id)
    REFERENCES characters(id)
    ON DELETE CASCADE;

ALTER TABLE character_achievements
    DROP CONSTRAINT IF EXISTS character_achievements_character_id_fkey,
    ADD CONSTRAINT character_achievements_character_id_fkey
    FOREIGN KEY (character_id)
    REFERENCES characters(id)
    ON DELETE CASCADE;

ALTER TABLE collection_log
    DROP CONSTRAINT IF EXISTS collection_log_character_id_fkey,
    ADD CONSTRAINT collection_log_character_id_fkey
    FOREIGN KEY (character_id)
    REFERENCES characters(id)
    ON DELETE CASCADE;

ALTER TABLE combat_stats
    DROP CONSTRAINT IF EXISTS combat_stats_character_id_fkey,
    ADD CONSTRAINT combat_stats_character_id_fkey
    FOREIGN KEY (character_id)
    REFERENCES characters(id)
    ON DELETE CASCADE;

ALTER TABLE equipment
    DROP CONSTRAINT IF EXISTS equipment_character_id_fkey,
    ADD CONSTRAINT equipment_character_id_fkey
    FOREIGN KEY (character_id)
    REFERENCES characters(id)
    ON DELETE CASCADE;
