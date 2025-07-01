-- Initialize WatchKeeper Intelligence Database for PostgreSQL

-- Create sources table
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    source_type TEXT,
    reliability_score REAL,
    language TEXT,
    country TEXT,
    last_collected_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    collection_frequency INTEGER,
    rate_limit INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create threats table
CREATE TABLE IF NOT EXISTS threats (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    severity INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create intelligence_items table
CREATE TABLE IF NOT EXISTS intelligence_items (
    id SERIAL PRIMARY KEY,
    raw_content TEXT NOT NULL,
    processed_content TEXT,
    threat_id INTEGER,
    source_id INTEGER NOT NULL,
    ai_analysis_data JSONB,
    processing_status TEXT NOT NULL DEFAULT 'PENDING',
    error_message TEXT,
    processing_time FLOAT,
    confidence_score FLOAT,
    latitude FLOAT,
    longitude FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES sources(id),
    FOREIGN KEY (threat_id) REFERENCES threats(id)
);

-- Create tags table
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Create intelligence_tags junction table
CREATE TABLE IF NOT EXISTS intelligence_tags (
    intelligence_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (intelligence_id, tag_id),
    FOREIGN KEY (intelligence_id) REFERENCES intelligence_items(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Create verification_info table
CREATE TABLE IF NOT EXISTS verification_info (
    intelligence_id INTEGER PRIMARY KEY,
    source_verified BOOLEAN DEFAULT TRUE,
    url_verified BOOLEAN DEFAULT TRUE,
    timestamp TEXT NOT NULL,
    verification_method TEXT NOT NULL,
    verification_agent TEXT NOT NULL,
    FOREIGN KEY (intelligence_id) REFERENCES intelligence_items(id) ON DELETE CASCADE
);

-- Insert sample source data
INSERT INTO sources (id, name, url, source_type, reliability_score, language, country, is_active) VALUES
(1, 'News Agency', 'https://news-agency.com', 'NEWS', 0.8, 'en', 'US', TRUE),
(999, 'Integration Test Source', 'https://example.com/test', 'NEWS', 0.5, 'en', 'US', TRUE);

-- Insert sample threat data
INSERT INTO threats (id, name, description, severity) VALUES
(1, 'Civil Unrest', 'Civil unrest and protests that may affect missionary safety', 8),
(2, 'Natural Disaster', 'Natural disasters that may affect missionary operations', 9),
(999, 'Test Threat', 'Test threat for integration testing', 5);

-- Insert sample intelligence data with threat_id
INSERT INTO intelligence_items (
    raw_content, processed_content, threat_id, source_id, processing_status, 
    latitude, longitude, created_at, updated_at
) VALUES 
(
    'Raw content of the protests in Paris',
    'Processed content about protests in Paris',
    1,
    1,
    'COMPLETED',
    48.8566,
    2.3522,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Insert sample tags
INSERT INTO tags (name) VALUES 
('protest'),
('violence'),
('paris'),
('france'),
('missionary safety');

-- Link tags to intelligence items
INSERT INTO intelligence_tags (intelligence_id, tag_id) VALUES
(1, 1),
(1, 2),
(1, 3),
(1, 4),
(1, 5);

-- Insert verification info
INSERT INTO verification_info (intelligence_id, source_verified, url_verified, timestamp, verification_method, verification_agent) VALUES
(1, TRUE, TRUE, '2025-06-01T14:30:00', 'Manual verification', 'System Administrator');
