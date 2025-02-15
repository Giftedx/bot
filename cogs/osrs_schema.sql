-- OSRS Database Schema

-- OSRS Characters
CREATE TABLE IF NOT EXISTS osrs_characters (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    current_world INTEGER DEFAULT 301
);

-- OSRS Skills
CREATE TABLE IF NOT EXISTS osrs_skills (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES osrs_characters(id),
    skill_type VARCHAR(50) NOT NULL,
    level INTEGER DEFAULT 1,
    xp BIGINT DEFAULT 0,
    last_trained TIMESTAMP WITH TIME ZONE,
    UNIQUE(character_id, skill_type)
);

-- OSRS Inventory
CREATE TABLE IF NOT EXISTS osrs_inventory (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES osrs_characters(id),
    item_id INTEGER NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    quantity INTEGER DEFAULT 1,
    slot INTEGER,
    noted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- OSRS Equipment
CREATE TABLE IF NOT EXISTS osrs_equipment (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES osrs_characters(id),
    slot VARCHAR(50) NOT NULL,
    item_id INTEGER NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, slot)
);

-- OSRS Resource Nodes
CREATE TABLE IF NOT EXISTS osrs_resources (
    id SERIAL PRIMARY KEY,
    world_id INTEGER NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_name VARCHAR(255) NOT NULL,
    depleted BOOLEAN DEFAULT FALSE,
    respawn_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- OSRS Training History
CREATE TABLE IF NOT EXISTS osrs_training_history (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES osrs_characters(id),
    skill_type VARCHAR(50) NOT NULL,
    xp_gained INTEGER NOT NULL,
    duration INTEGER NOT NULL, -- in seconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_osrs_characters_user ON osrs_characters(user_id);
CREATE INDEX IF NOT EXISTS idx_osrs_skills_char ON osrs_skills(character_id);
CREATE INDEX IF NOT EXISTS idx_osrs_inventory_char ON osrs_inventory(character_id);
CREATE INDEX IF NOT EXISTS idx_osrs_equipment_char ON osrs_equipment(character_id);
CREATE INDEX IF NOT EXISTS idx_osrs_resources_world ON osrs_resources(world_id);
CREATE INDEX IF NOT EXISTS idx_osrs_training_char ON osrs_training_history(character_id);

-- Add triggers for automatic level calculation
CREATE OR REPLACE FUNCTION update_osrs_level()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate new level based on XP using OSRS formula
    WITH level_calc AS (
        SELECT level
        FROM generate_series(1, 99) level
        WHERE NEW.xp < (
            SELECT floor(sum(
                floor(l + 300 * pow(2, l/7.0))/4
            ))::bigint
            FROM generate_series(1, level) l
        )
        LIMIT 1
    )
    SELECT level - 1 INTO NEW.level
    FROM level_calc;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_osrs_level
    BEFORE INSERT OR UPDATE OF xp ON osrs_skills
    FOR EACH ROW
    EXECUTE FUNCTION update_osrs_level();
