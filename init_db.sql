-- Initialize WatchKeeper Intelligence Database

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
),
(
    'Travel Advisory Issued for Eastern Germany',
    'The Foreign Ministry has issued a travel advisory for eastern regions of Germany due to increasing civil unrest. Several religious institutions have reported vandalism in the past week. Missionaries in the area are advised to exercise extreme caution and maintain low profiles.',
    'Travel advisory for missionaries in eastern Germany',
    'Deutsche Welle',
    2,
    'Raw content of travel advisory for eastern Germany',
    'https://www.dw.com/en/travel-advisory-eastern-germany/a-65432198',
    '2025-06-21T14:15:00Z',
    '2025-06-21T10:30:00Z',
    7.2,
    8.5,
    'Europe',
    'Germany',
    'Eastern Germany',
    -0.7,
    0.85
),
(
    'Cyber Attack Targets Religious Organizations in Spain',
    'A sophisticated cyber attack has targeted multiple religious organizations across Spain. The attack appears to be focused on extracting contact information and communication records. Security experts recommend immediate password changes and enhanced digital security measures for all religious personnel.',
    'Cyber attack on religious organizations in Spain',
    'El País',
    3,
    'Raw content of cyber attack on religious organizations in Spain',
    'https://elpais.com/technology/2025-06-20/cyber-attack-religious-organizations.html',
    '2025-06-20T09:45:00Z',
    '2025-06-20T08:15:00Z',
    7.8,
    8.0,
    'Europe',
    'Spain',
    'Madrid',
    -0.4,
    0.75
),
(
    'Severe Weather Warning for Southern Italy',
    'Meteorological services have issued severe weather warnings for southern Italy, including Sicily and Calabria. Flash floods and landslides are possible in the next 72 hours. Several missionary groups are known to be operating in these regions. Emergency services recommend postponing all non-essential travel.',
    'Severe weather warning affecting missionary areas in southern Italy',
    'ANSA',
    4,
    'Raw content of severe weather warning for southern Italy',
    'https://www.ansa.it/english/news/2025-06-19/weather-warning-southern-italy.html',
    '2025-06-19T16:20:00Z',
    '2025-06-19T15:45:00Z',
    6.5,
    7.0,
    'Europe',
    'Italy',
    'Sicily and Calabria',
    -0.6,
    0.8
),
(
    'Public Transportation Strike in London Affects Mission Activities',
    'A major public transportation strike in London has severely disrupted travel across the city. Mission activities scheduled for the weekend may be affected. Alternative transportation arrangements are recommended, and safety concerns are heightened due to overcrowding at available services.',
    'London transport strike disrupts mission activities',
    'BBC News',
    5,
    'Raw content of London transport strike',
    'https://www.bbc.co.uk/news/uk-england-london-65432987',
    '2025-06-18T11:10:00Z',
    '2025-06-18T09:30:00Z',
    5.5,
    7.0,
    'Europe',
    'United Kingdom',
    'London',
    -0.3,
    0.85
);

-- Insert tags
INSERT INTO tags (name) VALUES 
('protest'), ('violence'), ('cyber security'), ('weather'), ('transportation'),
('evacuation'), ('public safety'), ('political unrest'), ('natural disaster'), ('infrastructure');

-- Link tags to intelligence items
-- Paris protests
INSERT INTO intelligence_tags (intelligence_id, tag_id) VALUES 
(1, 1), (1, 2), (1, 7), (1, 8);

-- Germany travel advisory
INSERT INTO intelligence_tags (intelligence_id, tag_id) VALUES 
(2, 7), (2, 8);

-- Spain cyber attack
INSERT INTO intelligence_tags (intelligence_id, tag_id) VALUES 
(3, 3);

-- Italy weather warning
INSERT INTO intelligence_tags (intelligence_id, tag_id) VALUES 
(4, 4), (4, 5), (4, 7), (4, 9);

-- London transportation strike
INSERT INTO intelligence_tags (intelligence_id, tag_id) VALUES 
(5, 5), (5, 7), (5, 10);

-- Add verification info
INSERT INTO verification_info (intelligence_id, source_verified, url_verified, timestamp, verification_method, verification_agent) VALUES
(1, TRUE, TRUE, '2025-06-22T19:00:00Z', 'manual review', 'system operator'),
(2, TRUE, TRUE, '2025-06-21T15:30:00Z', 'automated check', 'verification service'),
(3, TRUE, TRUE, '2025-06-20T10:15:00Z', 'manual review', 'system operator'),
(4, TRUE, TRUE, '2025-06-19T17:00:00Z', 'automated check', 'verification service'),
(5, TRUE, TRUE, '2025-06-18T12:00:00Z', 'manual review', 'system operator');
