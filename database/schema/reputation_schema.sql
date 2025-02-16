-- Reputation system tables

-- Table: reputation
CREATE TABLE IF NOT EXISTS reputation (
    user_id BIGINT PRIMARY KEY,
    points INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: reputation_history
CREATE TABLE IF NOT EXISTS reputation_history (
    id SERIAL PRIMARY KEY,
    giver_id BIGINT NOT NULL,
    receiver_id BIGINT NOT NULL,
    given_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (giver_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id)
);

-- Index on reputation points for faster leaderboard queries
CREATE INDEX IF NOT EXISTS idx_reputation_points ON reputation(points DESC);

-- Index on reputation history for faster lookup
CREATE INDEX IF NOT EXISTS idx_reputation_history_users ON reputation_history(giver_id, receiver_id);
CREATE INDEX IF NOT EXISTS idx_reputation_history_date ON reputation_history(given_at DESC);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_reputation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update the updated_at timestamp
CREATE TRIGGER update_reputation_timestamp
    BEFORE UPDATE ON reputation
    FOR EACH ROW
    EXECUTE FUNCTION update_reputation_timestamp();

-- View to get reputation statistics
CREATE OR REPLACE VIEW reputation_stats AS
SELECT 
    r.user_id,
    r.points,
    COUNT(DISTINCT rh.giver_id) as unique_givers,
    COUNT(DISTINCT rh.receiver_id) as unique_receivers,
    MAX(rh.given_at) as last_reputation_received
FROM reputation r
LEFT JOIN reputation_history rh ON r.user_id = rh.receiver_id
GROUP BY r.user_id, r.points; 