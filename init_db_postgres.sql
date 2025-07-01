-- Initialize WatchKeeper Intelligence Database for PostgreSQL

-- Create intelligence_items table
CREATE TABLE IF NOT EXISTS intelligence_items (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    source TEXT NOT NULL,
    source_id INTEGER NOT NULL,
    raw_content TEXT NOT NULL,
    url TEXT NOT NULL,
    collection_date TEXT NOT NULL,
    publication_date TEXT,
    threat_level REAL NOT NULL,
    missionary_relevance REAL NOT NULL,
    region TEXT,
    country TEXT,
    location TEXT,
    latitude REAL,
    longitude REAL,
    keywords TEXT,
    sentiment REAL,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

-- Insert sample intelligence data
-- First, insert the intelligence items
INSERT INTO intelligence_items (
    title, content, summary, source, source_id, raw_content, url, collection_date, publication_date, 
    threat_level, missionary_relevance, region, country, location, sentiment, confidence
) VALUES 
(
    'Protests Erupt in Paris Near Missionary Housing',
    'Violent protests have erupted in central Paris following controversial legislation. The demonstrations are taking place within 500 meters of known missionary housing. Local authorities have advised residents to stay indoors and avoid the area. Several injuries have been reported, though no missionaries are known to be affected at this time.',
    'Violent protests near missionary housing in Paris',
    'News Agency',
    1,
    'Raw content of the protests in Paris',
    'https://www.france24.com/en/europe/20250622-paris-protests',
    '2025-06-22T18:30:00Z',
    '2025-06-22T16:45:00Z',
    8.5,
    9.0,
    'Europe',
    'France',
    'Paris, 5th Arrondissement',
    -0.5,
    0.9
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
(1, 1);

INSERT INTO intelligence_tags (intelligence_id, tag_id) VALUES
(1, 2);

INSERT INTO intelligence_tags (intelligence_id, tag_id) VALUES
(1, 3);

INSERT INTO intelligence_tags (intelligence_id, tag_id) VALUES
(1, 4);

INSERT INTO intelligence_tags (intelligence_id, tag_id) VALUES
(1, 5);

-- Insert verification info
INSERT INTO verification_info (intelligence_id, source_verified, url_verified, timestamp, verification_method, verification_agent) VALUES
(1, TRUE, TRUE, '2025-06-01T14:30:00', 'Manual verification', 'System Administrator');
