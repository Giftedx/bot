-- Initial schema migration

-- Player tables
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    discord_id BIGINT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Player stats (existing)
CREATE TABLE IF NOT EXISTS player_stats (
    player_id INTEGER PRIMARY KEY REFERENCES players(id),
    -- Combat stats
    attack_level INTEGER NOT NULL DEFAULT 1,
    strength_level INTEGER NOT NULL DEFAULT 1,
    defence_level INTEGER NOT NULL DEFAULT 1,
    ranged_level INTEGER NOT NULL DEFAULT 1,
    magic_level INTEGER NOT NULL DEFAULT 1,
    prayer_level INTEGER NOT NULL DEFAULT 1,
    hitpoints_level INTEGER NOT NULL DEFAULT 10,
    -- Non-combat stats
    mining_level INTEGER NOT NULL DEFAULT 1,
    smithing_level INTEGER NOT NULL DEFAULT 1,
    fishing_level INTEGER NOT NULL DEFAULT 1,
    cooking_level INTEGER NOT NULL DEFAULT 1,
    woodcutting_level INTEGER NOT NULL DEFAULT 1,
    firemaking_level INTEGER NOT NULL DEFAULT 1,
    crafting_level INTEGER NOT NULL DEFAULT 1,
    fletching_level INTEGER NOT NULL DEFAULT 1,
    herblore_level INTEGER NOT NULL DEFAULT 1,
    agility_level INTEGER NOT NULL DEFAULT 1,
    thieving_level INTEGER NOT NULL DEFAULT 1,
    slayer_level INTEGER NOT NULL DEFAULT 1,
    farming_level INTEGER NOT NULL DEFAULT 1,
    runecrafting_level INTEGER NOT NULL DEFAULT 1,
    construction_level INTEGER NOT NULL DEFAULT 1,
    hunter_level INTEGER NOT NULL DEFAULT 1,
    -- Experience values
    attack_xp REAL NOT NULL DEFAULT 0,
    strength_xp REAL NOT NULL DEFAULT 0,
    defence_xp REAL NOT NULL DEFAULT 0,
    ranged_xp REAL NOT NULL DEFAULT 0,
    magic_xp REAL NOT NULL DEFAULT 0,
    prayer_xp REAL NOT NULL DEFAULT 0,
    hitpoints_xp REAL NOT NULL DEFAULT 1154,
    mining_xp REAL NOT NULL DEFAULT 0,
    smithing_xp REAL NOT NULL DEFAULT 0,
    fishing_xp REAL NOT NULL DEFAULT 0,
    cooking_xp REAL NOT NULL DEFAULT 0,
    woodcutting_xp REAL NOT NULL DEFAULT 0,
    firemaking_xp REAL NOT NULL DEFAULT 0,
    crafting_xp REAL NOT NULL DEFAULT 0,
    fletching_xp REAL NOT NULL DEFAULT 0,
    herblore_xp REAL NOT NULL DEFAULT 0,
    agility_xp REAL NOT NULL DEFAULT 0,
    thieving_xp REAL NOT NULL DEFAULT 0,
    slayer_xp REAL NOT NULL DEFAULT 0,
    farming_xp REAL NOT NULL DEFAULT 0,
    runecrafting_xp REAL NOT NULL DEFAULT 0,
    construction_xp REAL NOT NULL DEFAULT 0,
    hunter_xp REAL NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Player equipment (existing)
CREATE TABLE IF NOT EXISTS player_equipment (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    slot TEXT NOT NULL,  -- head, body, legs, etc.
    item_id INTEGER NOT NULL,
    equipped_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, slot)
);

-- Player inventory (existing)
CREATE TABLE IF NOT EXISTS player_inventory (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    obtained_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, item_id)
);

-- Player bank (existing)
CREATE TABLE IF NOT EXISTS player_bank (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    tab INTEGER NOT NULL DEFAULT 0,
    UNIQUE(player_id, item_id)
);

-- Combat history (existing)
CREATE TABLE IF NOT EXISTS combat_history (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    opponent_type TEXT NOT NULL,  -- player or monster
    opponent_id INTEGER NOT NULL,  -- player_id or monster_id
    winner_id INTEGER NOT NULL,  -- player_id or monster_id
    start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    total_damage_dealt INTEGER NOT NULL DEFAULT 0,
    total_damage_taken INTEGER NOT NULL DEFAULT 0,
    experience_gained REAL NOT NULL DEFAULT 0,
    drops_json TEXT  -- JSON array of item IDs and quantities
);

-- Combat hits (existing)
CREATE TABLE IF NOT EXISTS combat_hits (
    id INTEGER PRIMARY KEY,
    combat_id INTEGER NOT NULL REFERENCES combat_history(id),
    attacker_id INTEGER NOT NULL,  -- player_id or monster_id
    defender_id INTEGER NOT NULL,  -- player_id or monster_id
    damage INTEGER NOT NULL,
    hit_type TEXT NOT NULL,  -- normal, special, magic, ranged
    accuracy REAL NOT NULL,
    max_hit INTEGER NOT NULL,
    hit_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Slayer tasks (existing)
CREATE TABLE IF NOT EXISTS slayer_tasks (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    monster_id INTEGER NOT NULL,
    amount_assigned INTEGER NOT NULL,
    amount_remaining INTEGER NOT NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    experience_gained REAL NOT NULL DEFAULT 0
);

-- NEW TABLES

-- Quest progress
CREATE TABLE IF NOT EXISTS quest_progress (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    quest_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'not_started',  -- not_started, in_progress, completed
    current_step INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    UNIQUE(player_id, quest_id)
);

-- Achievement progress
CREATE TABLE IF NOT EXISTS achievement_progress (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    achievement_id TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMP,
    UNIQUE(player_id, achievement_id)
);

-- Pet ownership
CREATE TABLE IF NOT EXISTS player_pets (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    pet_id TEXT NOT NULL,
    nickname TEXT,
    obtained_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    experience REAL NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    UNIQUE(player_id, pet_id)
);

-- Player skills (separate from stats for skill-specific data)
CREATE TABLE IF NOT EXISTS player_skills (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    skill_id TEXT NOT NULL,
    current_action TEXT,  -- current training activity
    action_start_time TIMESTAMP,
    action_end_time TIMESTAMP,
    bonus_xp_multiplier REAL NOT NULL DEFAULT 1.0,
    UNIQUE(player_id, skill_id)
);

-- Trading history
CREATE TABLE IF NOT EXISTS trade_history (
    id INTEGER PRIMARY KEY,
    player1_id INTEGER NOT NULL REFERENCES players(id),
    player2_id INTEGER NOT NULL REFERENCES players(id),
    items_offered_json TEXT NOT NULL,  -- JSON array of items offered by player1
    items_received_json TEXT NOT NULL,  -- JSON array of items offered by player2
    trade_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL  -- pending, completed, cancelled
);

-- Chat logs
CREATE TABLE IF NOT EXISTS chat_logs (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    channel_id TEXT NOT NULL,  -- public, private, clan, etc.
    message TEXT NOT NULL,
    sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Player relationships
CREATE TABLE IF NOT EXISTS player_relationships (
    id INTEGER PRIMARY KEY,
    player1_id INTEGER NOT NULL REFERENCES players(id),
    player2_id INTEGER NOT NULL REFERENCES players(id),
    relationship_type TEXT NOT NULL,  -- friend, clan_member, ignored
    established_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player1_id, player2_id)
);

-- World locations
CREATE TABLE IF NOT EXISTS player_location (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    location_id TEXT NOT NULL,
    entered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_players_discord_id ON players(discord_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_player_id ON player_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_equipment_player_id ON player_equipment(player_id);
CREATE INDEX IF NOT EXISTS idx_player_inventory_player_id ON player_inventory(player_id);
CREATE INDEX IF NOT EXISTS idx_player_bank_player_id ON player_bank(player_id);
CREATE INDEX IF NOT EXISTS idx_combat_history_player_id ON combat_history(player_id);
CREATE INDEX IF NOT EXISTS idx_combat_hits_combat_id ON combat_hits(combat_id);
CREATE INDEX IF NOT EXISTS idx_slayer_tasks_player_id ON slayer_tasks(player_id);

-- New indexes
CREATE INDEX IF NOT EXISTS idx_quest_progress_player_id ON quest_progress(player_id);
CREATE INDEX IF NOT EXISTS idx_achievement_progress_player_id ON achievement_progress(player_id);
CREATE INDEX IF NOT EXISTS idx_player_pets_player_id ON player_pets(player_id);
CREATE INDEX IF NOT EXISTS idx_player_skills_player_id ON player_skills(player_id);
CREATE INDEX IF NOT EXISTS idx_trade_history_player1_id ON trade_history(player1_id);
CREATE INDEX IF NOT EXISTS idx_trade_history_player2_id ON trade_history(player2_id);
CREATE INDEX IF NOT EXISTS idx_chat_logs_player_id ON chat_logs(player_id);
CREATE INDEX IF NOT EXISTS idx_player_relationships_player1_id ON player_relationships(player1_id);
CREATE INDEX IF NOT EXISTS idx_player_relationships_player2_id ON player_relationships(player2_id);
CREATE INDEX IF NOT EXISTS idx_player_location_player_id ON player_location(player_id); 