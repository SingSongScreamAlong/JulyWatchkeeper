#!/usr/bin/env python3
"""
Watchkeeper Dashboard Utilities
Helper functions for data processing and analysis
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys
from typing import Dict, List, Tuple, Any, Optional
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from europe_filter import filter_intelligence, EuropeFilter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('watchkeeper.dashboard')

def get_db_connection(db_path: str = None) -> sqlite3.Connection:
    """Create a database connection"""
    if db_path is None:
        db_path = os.getenv('WATCHKEEPER_DB', 'data/intelligence.db')
    
    if not os.path.exists(db_path):
        logger.error(f"Database not found at {db_path}")
        raise FileNotFoundError(f"Database not found at {db_path}")
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def load_intelligence_data(days: int = 30, limit: int = 1000, db_path: str = None) -> pd.DataFrame:
    """Load intelligence data from the database"""
    try:
        conn = get_db_connection(db_path)
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        query = """
        SELECT * FROM intelligence_items 
        WHERE timestamp >= ? 
        ORDER BY timestamp DESC
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=(cutoff_date, limit))
        conn.close()
        
        # Convert DataFrame to list of dictionaries for filtering
        records = df.to_dict('records')
        
        # Filter for European or missionary relevance
        filtered_records = filter_intelligence(records)
        
        # Convert filtered records back to DataFrame
        if filtered_records:
            df = pd.DataFrame(filtered_records)
            logger.info(f"Filtered intelligence data to {len(df)} Europe/missionary relevant items")
        else:
            # Create empty DataFrame with same columns if no records match
            df = pd.DataFrame(columns=df.columns)
            logger.info("No Europe/missionary relevant items found")
        
        # Convert timestamp columns to datetime
        for col in ['timestamp', 'publication_date', 'collection_date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
                
        return df
    except Exception as e:
        logger.error(f"Error loading intelligence data: {e}")
        return pd.DataFrame()

def get_threat_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate threat statistics from intelligence data"""
    if df.empty:
        return {
            "total_items": 0,
            "avg_threat": 0.0,
            "high_threat_count": 0,
            "medium_threat_count": 0,
            "low_threat_count": 0,
            "source_count": 0
        }
    
    stats = {
        "total_items": len(df),
        "avg_threat": round(df['threat_level'].mean(), 2),
        "high_threat_count": len(df[df['threat_level'] >= 7]),
        "medium_threat_count": len(df[(df['threat_level'] >= 4) & (df['threat_level'] < 7)]),
        "low_threat_count": len(df[df['threat_level'] < 4]),
        "source_count": df['source'].nunique()
    }
    
    return stats

def get_regional_breakdown(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Get regional breakdown of intelligence items"""
    if df.empty:
        return pd.DataFrame(columns=['region', 'count', 'avg_threat'])
        
    regional_data = df.groupby('region').agg({
        'id': 'count',
        'threat_level': 'mean'
    }).reset_index()
    
    regional_data.columns = ['region', 'count', 'avg_threat']
    regional_data['avg_threat'] = regional_data['avg_threat'].round(2)
    regional_data = regional_data.sort_values('count', ascending=False).head(top_n)
    
    return regional_data

def get_source_reliability(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate source reliability metrics"""
    if df.empty:
        return pd.DataFrame(columns=['source', 'count', 'avg_threat', 'avg_confidence'])
        
    source_data = df.groupby('source').agg({
        'id': 'count',
        'threat_level': 'mean',
        'confidence': 'mean'
    }).reset_index()
    
    source_data.columns = ['source', 'count', 'avg_threat', 'avg_confidence']
    source_data['avg_threat'] = source_data['avg_threat'].round(2)
    source_data['avg_confidence'] = source_data['avg_confidence'].round(2)
    source_data = source_data.sort_values('count', ascending=False)
    
    return source_data

def get_time_series_data(df: pd.DataFrame, date_column: str = 'timestamp') -> pd.DataFrame:
    """Get time series data for intelligence items"""
    if df.empty:
        return pd.DataFrame(columns=['date', 'count', 'avg_threat'])
        
    # Ensure the date column is datetime
    df['date'] = pd.to_datetime(df[date_column]).dt.date
    
    # Group by date and calculate metrics
    time_series = df.groupby('date').agg({
        'id': 'count',
        'threat_level': 'mean'
    }).reset_index()
    
    time_series.columns = ['date', 'count', 'avg_threat']
    time_series['date'] = pd.to_datetime(time_series['date'])
    time_series['avg_threat'] = time_series['avg_threat'].round(2)
    time_series = time_series.sort_values('date')
    
    return time_series

def get_geospatial_data(df: pd.DataFrame) -> pd.DataFrame:
    """Get geospatial data for mapping"""
    if df.empty:
        return pd.DataFrame(columns=['latitude', 'longitude', 'title', 'threat_level', 'source', 'timestamp'])
        
    # Filter for rows with valid coordinates
    geo_df = df.dropna(subset=['latitude', 'longitude']).copy()
    
    # Ensure coordinates are numeric
    geo_df['latitude'] = pd.to_numeric(geo_df['latitude'], errors='coerce')
    geo_df['longitude'] = pd.to_numeric(geo_df['longitude'], errors='coerce')
    
    # Filter out invalid coordinates
    geo_df = geo_df[(geo_df['latitude'] >= -90) & (geo_df['latitude'] <= 90) & 
                   (geo_df['longitude'] >= -180) & (geo_df['longitude'] <= 180)]
    
    # Select relevant columns
    map_df = geo_df[['latitude', 'longitude', 'title', 'threat_level', 'source', 'timestamp']]
    
    return map_df

def get_sentiment_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze sentiment distribution in intelligence data"""
    if df.empty or 'sentiment' not in df.columns:
        return {
            "sentiment_counts": {},
            "avg_sentiment": 0.0,
            "sentiment_by_region": {}
        }
    
    # Drop rows with missing sentiment
    sentiment_df = df.dropna(subset=['sentiment']).copy()
    
    if sentiment_df.empty:
        return {
            "sentiment_counts": {},
            "avg_sentiment": 0.0,
            "sentiment_by_region": {}
        }
    
    # Categorize sentiment
    sentiment_df['sentiment_category'] = pd.cut(
        sentiment_df['sentiment'],
        bins=[-1.0, -0.6, -0.2, 0.2, 0.6, 1.0],
        labels=['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']
    )
    
    # Count by category
    sentiment_counts = sentiment_df['sentiment_category'].value_counts().to_dict()
    
    # Average sentiment
    avg_sentiment = round(sentiment_df['sentiment'].mean(), 2)
    
    # Sentiment by region
    sentiment_by_region = sentiment_df.groupby('region')['sentiment'].mean().round(2).to_dict()
    
    return {
        "sentiment_counts": sentiment_counts,
        "avg_sentiment": avg_sentiment,
        "sentiment_by_region": sentiment_by_region
    }

def get_keyword_analysis(df: pd.DataFrame, top_n: int = 20) -> Dict[str, Any]:
    """Analyze keywords in intelligence data"""
    if df.empty or 'keywords' not in df.columns:
        return {
            "top_keywords": [],
            "keyword_threat_correlation": {}
        }
    
    # Extract all keywords
    all_keywords = []
    keyword_threat_map = {}
    
    for _, row in df.iterrows():
        if pd.notna(row['keywords']) and row['keywords']:
            keywords = [k.strip() for k in row['keywords'].split(',')]
            all_keywords.extend(keywords)
            
            for keyword in keywords:
                if keyword in keyword_threat_map:
                    keyword_threat_map[keyword].append(row['threat_level'])
                else:
                    keyword_threat_map[keyword] = [row['threat_level']]
    
    # Count keywords
    keyword_counts = pd.Series(all_keywords).value_counts().head(top_n).to_dict()
    
    # Calculate average threat level per keyword
    keyword_threat_correlation = {}
    for keyword, threats in keyword_threat_map.items():
        if len(threats) >= 3:  # Only include keywords that appear in at least 3 items
            keyword_threat_correlation[keyword] = round(sum(threats) / len(threats), 2)
    
    # Sort by correlation strength
    keyword_threat_correlation = dict(sorted(
        keyword_threat_correlation.items(), 
        key=lambda x: abs(x[1] - 5),  # Sort by distance from neutral (5)
        reverse=True
    )[:top_n])
    
    return {
        "top_keywords": keyword_counts,
        "keyword_threat_correlation": keyword_threat_correlation
    }

def filter_intelligence_data(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Filter intelligence data based on criteria"""
    filtered_df = df.copy()
    
    # Apply filters
    if 'threat_level' in filters and filters['threat_level']:
        min_threat = float(filters['threat_level'])
        filtered_df = filtered_df[filtered_df['threat_level'] >= min_threat]
        
    if 'missionary_relevance' in filters and filters['missionary_relevance']:
        min_relevance = float(filters['missionary_relevance'])
        filtered_df = filtered_df[filtered_df['missionary_relevance'] >= min_relevance]
        
    if 'region' in filters and filters['region']:
        filtered_df = filtered_df[filtered_df['region'] == filters['region']]
        
    if 'source' in filters and filters['source']:
        filtered_df = filtered_df[filtered_df['source'] == filters['source']]
        
    if 'start_date' in filters and filters['start_date']:
        start_date = pd.to_datetime(filters['start_date'])
        filtered_df = filtered_df[pd.to_datetime(filtered_df['timestamp']) >= start_date]
        
    if 'end_date' in filters and filters['end_date']:
        end_date = pd.to_datetime(filters['end_date'])
        filtered_df = filtered_df[pd.to_datetime(filtered_df['timestamp']) <= end_date]
        
    if 'keyword' in filters and filters['keyword']:
        keyword = filters['keyword'].lower()
        # Search in title, content, and keywords
        title_match = filtered_df['title'].str.lower().str.contains(keyword, na=False)
        content_match = filtered_df['content'].str.lower().str.contains(keyword, na=False)
        
        # Keywords are stored as JSON string
        keyword_match = filtered_df['keywords'].apply(
            lambda x: keyword in json.loads(x).lower() if isinstance(x, str) else False
        )
        
        filtered_df = filtered_df[title_match | content_match | keyword_match]
    
    # Always ensure European or missionary relevance
    if not filtered_df.empty:
        # Convert DataFrame to list of dictionaries for filtering
        records = filtered_df.to_dict('records')
        
        # Apply European filter
        filtered_records = filter_intelligence(records)
        
        # Convert filtered records back to DataFrame
        if filtered_records:
            filtered_df = pd.DataFrame(filtered_records)
        else:
            # Create empty DataFrame with same columns if no records match
            filtered_df = pd.DataFrame(columns=filtered_df.columns)
    
    return filtered_df

def apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Apply filters to the intelligence dataframe"""
    filtered_df = df.copy()
    
    # Filter by regions
    if filters.get('regions'):
        filtered_df = filtered_df[filtered_df['region'].isin(filters['regions'])]
    
    # Filter by threat level range
    if filters.get('threat_range'):
        min_threat, max_threat = filters['threat_range']
        filtered_df = filtered_df[
            (filtered_df['threat_level'] >= min_threat) & 
            (filtered_df['threat_level'] <= max_threat)
        ]
    
    # Filter by sources
    if filters.get('sources'):
        filtered_df = filtered_df[filtered_df['source'].isin(filters['sources'])]
    
    # Filter by date range
    if filters.get('date_range'):
        start_date, end_date = filters['date_range']
        filtered_df = filtered_df[
            (filtered_df['timestamp'] >= start_date) & 
            (filtered_df['timestamp'] <= end_date)
        ]
    
    # Filter by search query
    if filters.get('search_query'):
        query = filters['search_query'].lower()
        filtered_df = filtered_df[
            filtered_df['title'].str.lower().str.contains(query) | 
            filtered_df['content'].str.lower().str.contains(query)
        ]
    
    return filtered_df

def generate_export_data(df: pd.DataFrame, format_type: str = 'csv') -> str:
    """Generate export data in various formats"""
    if df.empty:
        return ""
    
    # Select relevant columns for export
    export_columns = [
        'id', 'title', 'source', 'url', 'timestamp', 'threat_level', 
        'region', 'country', 'location', 'keywords', 'sentiment'
    ]
    
    # Filter columns that exist in the dataframe
    export_df = df[[col for col in export_columns if col in df.columns]]
    
    if format_type == 'csv':
        return export_df.to_csv(index=False)
    elif format_type == 'json':
        return export_df.to_json(orient='records', date_format='iso')
    elif format_type == 'excel':
        # Return bytes for Excel download
        import io
        output = io.BytesIO()
        export_df.to_excel(output, index=False)
        output.seek(0)
        return output.getvalue()
    else:
        return export_df.to_csv(index=False)  # Default to CSV
