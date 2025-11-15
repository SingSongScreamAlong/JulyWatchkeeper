#!/usr/bin/env python3
"""Quick database initialization for testing"""
import sqlite3
import os
from datetime import datetime

# Create data directory
os.makedirs('data', exist_ok=True)

# Connect to database
conn = sqlite3.connect('data/intelligence.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS intelligence_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS intelligence_tags (
    intelligence_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (intelligence_id, tag_id),
    FOREIGN KEY (intelligence_id) REFERENCES intelligence_items(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
)
''')

# Insert sample data for Nov 15, 2025
now = datetime.utcnow().isoformat() + 'Z'

samples = [
    (
        'Religious Freedom Concerns in Middle East Region',
        'Reports indicate increasing restrictions on religious activities in several Middle Eastern countries. Christian communities report heightened surveillance and administrative barriers to worship gatherings. Missionaries are advised to maintain low profiles and follow local guidance.',
        'Heightened restrictions on religious activities in Middle East',
        'International Religious Freedom Report',
        1,
        'Raw content about religious freedom concerns',
        'https://www.state.gov/religiousfreedomreport/',
        now,
        now,
        7.5,
        8.5,
        'Middle East',
        'Regional',
        'Middle East Region',
        30.0,
        45.0,
        'religious freedom, restrictions, surveillance',
        -0.6,
        0.85,
        now
    ),
    (
        'Security Alert: European Border Tensions',
        'Increased military activity near Eastern European borders raises security concerns for missionary personnel in the region. Local authorities recommend avoiding border areas and monitoring official travel advisories.',
        'Military tensions in Eastern Europe affect missionary safety',
        'Reuters Security Brief',
        2,
        'Raw content about border tensions',
        'https://www.reuters.com/world/europe/',
        now,
        now,
        8.0,
        7.5,
        'Europe',
        'Eastern Europe',
        'Eastern European Border Region',
        50.0,
        25.0,
        'security, military, borders, tensions',
        -0.7,
        0.80,
        now
    ),
    (
        'Natural Disaster: Earthquake Aftershocks in Southeast Asia',
        'Multiple aftershocks continue following major earthquake in Southeast Asia. Several mission stations report minor damage. No missionary casualties reported, but evacuation routes should be reviewed.',
        'Earthquake aftershocks affecting mission stations in SE Asia',
        'USGS Earthquake Hazards',
        3,
        'Raw content about earthquake',
        'https://earthquake.usgs.gov/',
        now,
        now,
        6.5,
        7.0,
        'Southeast Asia',
        'Regional',
        'Southeast Asia',
        10.0,
        105.0,
        'earthquake, natural disaster, aftershocks',
        -0.5,
        0.90,
        now
    ),
    (
        'Health Alert: Disease Outbreak in Sub-Saharan Africa',
        'WHO reports outbreak of infectious disease in three Sub-Saharan African countries. Medical teams and missionaries in affected areas should ensure vaccinations are current and follow WHO health protocols.',
        'Disease outbreak affects missionary health safety in Africa',
        'WHO Disease Outbreak News',
        4,
        'Raw content about disease outbreak',
        'https://www.who.int/emergencies/disease-outbreak-news',
        now,
        now,
        7.0,
        8.0,
        'Africa',
        'Sub-Saharan Africa',
        'West Africa',
        10.0,
        0.0,
        'health, disease, outbreak, WHO',
        -0.6,
        0.85,
        now
    ),
    (
        'Political Unrest: Protests in South American Capital',
        'Large-scale protests in major South American capital city. Several Christian organizations report disruptions to outreach activities. Transportation networks affected. Missionaries advised to postpone non-essential travel.',
        'Protests disrupt missionary activities in South America',
        'BBC World News',
        5,
        'Raw content about protests',
        'https://www.bbc.com/news/world/latin_america',
        now,
        now,
        6.0,
        6.5,
        'South America',
        'Regional',
        'South America',
        -15.0,
        -60.0,
        'protests, political unrest, transportation',
        -0.4,
        0.75,
        now
    ),
]

for sample in samples:
    # Remove timestamp from the tuple since it's not in the table
    sample_data = sample[:-1]  # Exclude last element (timestamp)
    cursor.execute('''
        INSERT INTO intelligence_items (
            title, content, summary, source, source_id, raw_content, url,
            collection_date, publication_date, threat_level, missionary_relevance,
            region, country, location, latitude, longitude, keywords, sentiment,
            confidence
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_data)

conn.commit()
print(f"✓ Database initialized successfully")
print(f"✓ Created {len(samples)} sample intelligence items for {now[:10]}")
print(f"✓ Database location: data/intelligence.db")

# Show stats
cursor.execute("SELECT COUNT(*) FROM intelligence_items")
count = cursor.fetchone()[0]
print(f"✓ Total intelligence items: {count}")

cursor.execute("SELECT AVG(threat_level) FROM intelligence_items")
avg_threat = cursor.fetchone()[0]
print(f"✓ Average threat level: {avg_threat:.2f}/10")

conn.close()
