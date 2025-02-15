-- OSRS Character Table
CREATE TABLE IF NOT EXISTS osrs_characters (
    user_id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    stats JSONB NOT NULL DEFAULT '{}',
    inventory JSONB NOT NULL DEFAULT '[]',
    equipment JSONB NOT NULL DEFAULT '{}',
    bank JSONB NOT NULL DEFAULT '{}',
    quest_progress JSONB NOT NULL DEFAULT '{}',
    achievement_diaries JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_trained TIMESTAMP WITH TIME ZONE,
    total_xp BIGINT NOT NULL DEFAULT 0,
    combat_level INTEGER NOT NULL DEFAULT 3
);

-- OSRS Item Transactions
CREATE TABLE IF NOT EXISTS osrs_transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES osrs_characters(user_id),
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price_per_item INTEGER,
    total_price INTEGER,
    transaction_type VARCHAR(50) NOT NULL, -- 'buy', 'sell', 'trade', 'drop', 'pickup'
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_quantity CHECK (quantity != 0)
);

-- OSRS Training Sessions
CREATE TABLE IF NOT EXISTS osrs_training_sessions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES osrs_characters(user_id),
    skill VARCHAR(50) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    start_level INTEGER NOT NULL,
    end_level INTEGER,
    xp_gained INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- OSRS Quest Progress
CREATE TABLE IF NOT EXISTS osrs_quest_completions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES osrs_characters(user_id),
    quest_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'not_started', -- 'not_started', 'in_progress', 'completed'
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, quest_name)
);

-- OSRS Achievement Diary Progress
CREATE TABLE IF NOT EXISTS osrs_achievement_diary_tasks (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES osrs_characters(user_id),
    diary_name VARCHAR(255) NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    difficulty VARCHAR(50) NOT NULL, -- 'easy', 'medium', 'hard', 'elite'
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, diary_name, task_name)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_osrs_characters_total_xp ON osrs_characters(total_xp DESC);
CREATE INDEX IF NOT EXISTS idx_osrs_transactions_user_id ON osrs_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_osrs_transactions_created_at ON osrs_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_osrs_training_sessions_user_id ON osrs_training_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_osrs_quest_completions_user_id ON osrs_quest_completions(user_id);
CREATE INDEX IF NOT EXISTS idx_osrs_achievement_diary_tasks_user_id ON osrs_achievement_diary_tasks(user_id);

-- Functions
CREATE OR REPLACE FUNCTION update_combat_level()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate combat level based on stats
    -- This follows the OSRS combat level formula
    NEW.combat_level := (
        SELECT FLOOR(
            (
                -- Base combat
                0.25 * (
                    CAST((NEW.stats->>'defence')::text AS INTEGER) +
                    CAST((NEW.stats->>'hitpoints')::text AS INTEGER) +
                    FLOOR(CAST((NEW.stats->>'prayer')::text AS INTEGER) / 2)
                ) +
                -- Highest combat style
                GREATEST(
                    -- Melee
                    0.325 * (
                        CAST((NEW.stats->>'attack')::text AS INTEGER) +
                        CAST((NEW.stats->>'strength')::text AS INTEGER)
                    ),
                    -- Ranged
                    0.325 * (
                        FLOOR(1.5 * CAST((NEW.stats->>'ranged')::text AS INTEGER))
                    ),
                    -- Magic
                    0.325 * (
                        FLOOR(1.5 * CAST((NEW.stats->>'magic')::text AS INTEGER))
                    )
                )
            )::numeric
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update combat level when stats change
CREATE TRIGGER update_combat_level_trigger
    BEFORE INSERT OR UPDATE OF stats
    ON osrs_characters
    FOR EACH ROW
    EXECUTE FUNCTION update_combat_level();

-- Function to calculate total XP
CREATE OR REPLACE FUNCTION calculate_total_xp(stats JSONB)
RETURNS BIGINT AS $$
DECLARE
    total BIGINT := 0;
    skill_name TEXT;
    skill_level INTEGER;
BEGIN
    FOR skill_name, skill_level IN 
        SELECT * FROM jsonb_each_text(stats)
    LOOP
        -- Add XP for each level
        -- This is a simplified version, you might want to use the actual OSRS XP formula
        total := total + (skill_level * skill_level * 100);
    END LOOP;
    RETURN total;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update total XP when stats change
CREATE TRIGGER update_total_xp_trigger
    BEFORE INSERT OR UPDATE OF stats
    ON osrs_characters
    FOR EACH ROW
    EXECUTE FUNCTION calculate_total_xp(NEW.stats); 