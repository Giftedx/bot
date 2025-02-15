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

-- Elite Four progress tracking
CREATE TABLE IF NOT EXISTS elite_four_progress (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    member_id VARCHAR(50) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, member_id)
);

-- Elite Four champions
CREATE TABLE IF NOT EXISTS elite_four_champions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Champion victories
CREATE TABLE IF NOT EXISTS champion_victories (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Gym rematches
CREATE TABLE IF NOT EXISTS gym_rematches (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    gym_id VARCHAR(50) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, gym_id)
);

-- Elite Four rematches
CREATE TABLE IF NOT EXISTS elite_four_rematches (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
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
    winner_id BIGINT REFERENCES users(id)
);

-- Tournament participants
CREATE TABLE IF NOT EXISTS tournament_participants (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES pokemon_tournaments(id),
    user_id BIGINT REFERENCES users(id),
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
    player1_id BIGINT REFERENCES users(id),
    player2_id BIGINT REFERENCES users(id),
    winner_id BIGINT REFERENCES users(id),
    battle_data JSONB DEFAULT '{}',
    scheduled_time TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending'
);

-- OSRS Tables
CREATE TABLE IF NOT EXISTS osrs_players (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    game_mode VARCHAR(50) DEFAULT 'normal',
    world INTEGER DEFAULT 301,
    combat_level INTEGER DEFAULT 3,
    total_level INTEGER DEFAULT 32,
    quest_points INTEGER DEFAULT 0,
    daily_streak INTEGER DEFAULT 0
);

-- Skills System
CREATE TABLE IF NOT EXISTS osrs_skills (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES osrs_players(user_id),
    skill_name VARCHAR(50) NOT NULL,
    level INTEGER DEFAULT 1,
    xp BIGINT DEFAULT 0,
    current_level INTEGER, -- For boosted/reduced stats
    last_trained TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, skill_name)
);

-- Items & Equipment
CREATE TABLE IF NOT EXISTS osrs_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tradeable BOOLEAN DEFAULT true,
    stackable BOOLEAN DEFAULT false,
    equipable BOOLEAN DEFAULT false,
    slot VARCHAR(50),
    value INTEGER DEFAULT 0,
    high_alch INTEGER,
    low_alch INTEGER,
    weight DECIMAL(10,2),
    bonuses JSONB DEFAULT '{}'::jsonb,
    requirements JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS osrs_inventory (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES osrs_players(user_id),
    item_id INTEGER REFERENCES osrs_items(id),
    quantity INTEGER DEFAULT 1,
    slot INTEGER,
    noted BOOLEAN DEFAULT false,
    UNIQUE(user_id, slot)
);

CREATE TABLE IF NOT EXISTS osrs_equipment (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES osrs_players(user_id),
    slot_name VARCHAR(50) NOT NULL,
    item_id INTEGER REFERENCES osrs_items(id),
    UNIQUE(user_id, slot_name)
);

CREATE TABLE IF NOT EXISTS osrs_bank (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES osrs_players(user_id),
    item_id INTEGER REFERENCES osrs_items(id),
    quantity INTEGER DEFAULT 1,
    tab INTEGER DEFAULT 0,
    UNIQUE(user_id, item_id)
);

-- Quest System
CREATE TABLE IF NOT EXISTS osrs_quests (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    difficulty VARCHAR(50),
    quest_points INTEGER DEFAULT 1,
    requirements JSONB DEFAULT '{}'::jsonb,
    rewards JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS osrs_player_quests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES osrs_players(user_id),
    quest_id INTEGER REFERENCES osrs_quests(id),
    status VARCHAR(50) DEFAULT 'not_started',
    progress INTEGER DEFAULT 0,
    completed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, quest_id)
);

-- Achievement System
CREATE TABLE IF NOT EXISTS osrs_achievements (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    difficulty VARCHAR(50),
    points INTEGER DEFAULT 0,
    requirements JSONB DEFAULT '{}'::jsonb,
    rewards JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS osrs_player_achievements (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES osrs_players(user_id),
    achievement_id INTEGER REFERENCES osrs_achievements(id),
    progress INTEGER DEFAULT 0,
    completed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, achievement_id)
);

-- Collection Log System
CREATE TABLE IF NOT EXISTS osrs_collection_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS osrs_collection_items (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES osrs_collection_categories(id),
    item_id INTEGER REFERENCES osrs_items(id),
    rarity VARCHAR(50),
    UNIQUE(category_id, item_id)
);

CREATE TABLE IF NOT EXISTS osrs_player_collection (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES osrs_players(user_id),
    item_id INTEGER REFERENCES osrs_items(id),
    obtained_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, item_id)
);

-- Minigame System
CREATE TABLE IF NOT EXISTS osrs_minigames (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    min_combat_level INTEGER DEFAULT 0,
    requirements JSONB DEFAULT '{}'::jsonb,
    rewards JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS osrs_player_minigames (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES osrs_players(user_id),
    minigame_id INTEGER REFERENCES osrs_minigames(id),
    points INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    high_score INTEGER DEFAULT 0,
    last_played TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, minigame_id)
);

-- Grand Exchange System
CREATE TABLE IF NOT EXISTS osrs_ge_items (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES osrs_items(id),
    current_price INTEGER NOT NULL,
    daily_volume INTEGER DEFAULT 0,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    price_trend VARCHAR(50) DEFAULT 'stable',
    UNIQUE(item_id)
);

CREATE TABLE IF NOT EXISTS osrs_ge_orders (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES osrs_players(user_id),
    item_id INTEGER REFERENCES osrs_items(id),
    type VARCHAR(50) NOT NULL, -- 'buy' or 'sell'
    quantity INTEGER NOT NULL,
    price_each INTEGER NOT NULL,
    quantity_filled INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS osrs_ge_history (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES osrs_items(id),
    price INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    buyer_id BIGINT REFERENCES osrs_players(user_id),
    seller_id BIGINT REFERENCES osrs_players(user_id)
);

-- World System
CREATE TABLE IF NOT EXISTS osrs_worlds (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) DEFAULT 'normal',
    region VARCHAR(50) NOT NULL,
    player_count INTEGER DEFAULT 0,
    max_players INTEGER DEFAULT 2000,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Daily Tasks System
CREATE TABLE IF NOT EXISTS osrs_daily_tasks (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES osrs_players(user_id),
    task_type VARCHAR(50) NOT NULL,
    requirement TEXT NOT NULL,
    reward_type VARCHAR(50) NOT NULL,
    reward_amount INTEGER NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, created_at::date)
);

-- Create indexes for better query performance
CREATE INDEX idx_osrs_characters_user_id ON osrs_characters(user_id);
CREATE INDEX idx_osrs_stats_character_id ON osrs_stats(character_id);
CREATE INDEX idx_pokemon_user_id ON pokemon(user_id);
CREATE INDEX idx_active_spawns_channel ON active_spawns(channel_id) WHERE NOT caught;
CREATE INDEX idx_custom_commands_guild_id ON custom_commands(guild_id);
CREATE INDEX idx_pets_owner_id ON pets(owner_id);
CREATE INDEX idx_marriages_users ON marriages(user1_id, user2_id);
CREATE INDEX idx_playlists_owner ON playlists(owner_id);
CREATE INDEX idx_plex_sessions_channel ON plex_sessions(channel_id);

-- Battle system indexes
CREATE INDEX IF NOT EXISTS idx_battle_history_players ON battle_history(challenger_id, opponent_id);
CREATE INDEX IF NOT EXISTS idx_battle_history_type ON battle_history(battle_type);
CREATE INDEX IF NOT EXISTS idx_battle_stats_type ON battle_stats(battle_type);
CREATE INDEX IF NOT EXISTS idx_battle_rewards_player ON battle_rewards(player_id);
CREATE INDEX IF NOT EXISTS idx_battle_ratings_type ON battle_ratings(battle_type);

-- Elite Four and tournament indexes
CREATE INDEX idx_elite_four_progress_user ON elite_four_progress(user_id);
CREATE INDEX idx_elite_four_champions_user ON elite_four_champions(user_id);
CREATE INDEX idx_champion_victories_user ON champion_victories(user_id);
CREATE INDEX idx_gym_rematches_user ON gym_rematches(user_id);
CREATE INDEX idx_elite_four_rematches_user ON elite_four_rematches(user_id);
CREATE INDEX idx_tournament_participants_tournament ON tournament_participants(tournament_id);
CREATE INDEX idx_tournament_matches_tournament ON tournament_matches(tournament_id);

-- Indexes
CREATE INDEX idx_osrs_skills_user ON osrs_skills(user_id);
CREATE INDEX idx_osrs_inventory_user ON osrs_inventory(user_id);
CREATE INDEX idx_osrs_bank_user ON osrs_bank(user_id);
CREATE INDEX idx_osrs_equipment_user ON osrs_equipment(user_id);
CREATE INDEX idx_osrs_player_quests_user ON osrs_player_quests(user_id);
CREATE INDEX idx_osrs_player_achievements_user ON osrs_player_achievements(user_id);
CREATE INDEX idx_osrs_player_collection_user ON osrs_player_collection(user_id);
CREATE INDEX idx_osrs_player_minigames_user ON osrs_player_minigames(user_id);
CREATE INDEX idx_osrs_ge_orders_user ON osrs_ge_orders(user_id);
CREATE INDEX idx_osrs_ge_orders_status ON osrs_ge_orders(status) WHERE status = 'active';
CREATE INDEX idx_osrs_ge_history_item ON osrs_ge_history(item_id, timestamp DESC);
CREATE INDEX idx_osrs_daily_tasks_user ON osrs_daily_tasks(user_id, created_at);

-- Triggers
CREATE OR REPLACE FUNCTION update_combat_level() RETURNS TRIGGER AS $$
BEGIN
    -- Update combat level when combat skills change
    IF NEW.skill_name IN ('attack', 'strength', 'defence', 'hitpoints', 'prayer', 'ranged', 'magic') THEN
        UPDATE osrs_players
        SET combat_level = (
            SELECT FLOOR(
                (defence_level + hitpoints_level + FLOOR(prayer_level/2))/4 +
                (
                    GREATEST(
                        (attack_level + strength_level) * 0.325,
                        magic_level * 0.325,
                        ranged_level * 0.325
                    )
                )
            )
            FROM (
                SELECT 
                    MAX(CASE WHEN skill_name = 'defence' THEN level ELSE 0 END) as defence_level,
                    MAX(CASE WHEN skill_name = 'hitpoints' THEN level ELSE 0 END) as hitpoints_level,
                    MAX(CASE WHEN skill_name = 'prayer' THEN level ELSE 0 END) as prayer_level,
                    MAX(CASE WHEN skill_name = 'attack' THEN level ELSE 0 END) as attack_level,
                    MAX(CASE WHEN skill_name = 'strength' THEN level ELSE 0 END) as strength_level,
                    MAX(CASE WHEN skill_name = 'magic' THEN level ELSE 0 END) as magic_level,
                    MAX(CASE WHEN skill_name = 'ranged' THEN level ELSE 0 END) as ranged_level
                FROM osrs_skills
                WHERE user_id = NEW.user_id
            ) s
        )
        WHERE user_id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_combat_level_trigger
    AFTER INSERT OR UPDATE OF level ON osrs_skills
    FOR EACH ROW
    EXECUTE FUNCTION update_combat_level();

CREATE OR REPLACE FUNCTION update_total_level() RETURNS TRIGGER AS $$
BEGIN
    UPDATE osrs_players
    SET total_level = (
        SELECT SUM(level)
        FROM osrs_skills
        WHERE user_id = NEW.user_id
    )
    WHERE user_id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_total_level_trigger
    AFTER INSERT OR UPDATE OF level ON osrs_skills
    FOR EACH ROW
    EXECUTE FUNCTION update_total_level();
