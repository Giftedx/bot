-- Clan system tables

-- Table: clans
CREATE TABLE IF NOT EXISTS clans (
    name VARCHAR(100) PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index on clan name for faster lookups
CREATE INDEX IF NOT EXISTS idx_clans_name ON clans(name);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_clan_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update the updated_at timestamp
CREATE TRIGGER update_clan_timestamp
    BEFORE UPDATE ON clans
    FOR EACH ROW
    EXECUTE FUNCTION update_clan_timestamp();

-- View to get clan member counts
CREATE OR REPLACE VIEW clan_member_counts AS
SELECT 
    name,
    (data->>'members')::jsonb as members,
    jsonb_object_keys((data->>'members')::jsonb) as member_count
FROM clans;

-- Function to get clan statistics
CREATE OR REPLACE FUNCTION get_clan_stats(clan_name VARCHAR)
RETURNS TABLE (
    total_members INTEGER,
    total_xp BIGINT,
    average_level INTEGER,
    member_ranks JSON
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM jsonb_object_keys((c.data->>'members')::jsonb)),
        (c.data->>'xp')::BIGINT,
        (c.data->>'level')::INTEGER,
        (
            SELECT json_object_agg(rank, count)
            FROM (
                SELECT 
                    value->>'rank' as rank,
                    COUNT(*) as count
                FROM clans,
                jsonb_each((data->>'members')::jsonb)
                WHERE name = clan_name
                GROUP BY value->>'rank'
            ) ranks
        )::JSON
    FROM clans c
    WHERE c.name = clan_name;
END;
$$ LANGUAGE plpgsql; 