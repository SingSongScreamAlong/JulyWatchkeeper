-- Initialize PostGIS extensions for WATCHKEEPER database
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;

-- Create schema for WATCHKEEPER
CREATE SCHEMA IF NOT EXISTS watchkeeper;

-- Set search path
SET search_path TO watchkeeper, public;

-- Create custom types if needed
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'threat_status') THEN
        CREATE TYPE threat_status AS ENUM ('pending', 'active', 'resolved', 'false_alarm');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'threat_category') THEN
        CREATE TYPE threat_category AS ENUM ('security', 'political', 'economic', 'environmental', 'social', 'technological', 'other');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'source_type') THEN
        CREATE TYPE source_type AS ENUM ('news', 'social_media', 'government', 'ngo', 'academic', 'intelligence', 'other');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'processing_status') THEN
        CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');
    END IF;
END$$;

-- Create spatial indexes function
CREATE OR REPLACE FUNCTION create_spatial_indexes() RETURNS void AS $$
BEGIN
    -- This function will be called after tables are created by SQLAlchemy/Alembic
    -- It ensures proper spatial indexing for PostGIS columns
    RAISE NOTICE 'Spatial indexes will be created by Alembic migrations';
END;
$$ LANGUAGE plpgsql;

-- Create function to calculate distance between points
CREATE OR REPLACE FUNCTION calculate_distance(
    lat1 float, 
    lon1 float, 
    lat2 float, 
    lon2 float
) RETURNS float AS $$
DECLARE
    point1 geometry;
    point2 geometry;
BEGIN
    -- Convert lat/lon to PostGIS points
    point1 := ST_SetSRID(ST_MakePoint(lon1, lat1), 4326);
    point2 := ST_SetSRID(ST_MakePoint(lon2, lat2), 4326);
    
    -- Return distance in meters
    RETURN ST_Distance(
        point1::geography,
        point2::geography
    );
END;
$$ LANGUAGE plpgsql;
