"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-06-18

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2 as ga
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE threat_status AS ENUM ('pending', 'active', 'resolved', 'false_alarm')")
    op.execute("CREATE TYPE threat_category AS ENUM ('security', 'political', 'economic', 'environmental', 'social', 'technological', 'other')")
    op.execute("CREATE TYPE source_type AS ENUM ('news', 'social_media', 'government', 'ngo', 'academic', 'intelligence', 'other')")
    op.execute("CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed')")
    
    # Create PostGIS extension if not exists
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis_topology')
    
    # Create sources table
    op.create_table('sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('source_type', sa.Enum('news', 'social_media', 'government', 'ngo', 'academic', 'intelligence', 'other', name='source_type'), nullable=False),
        sa.Column('reliability_score', sa.Float(), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('country', sa.String(length=2), nullable=True),
        sa.Column('last_collected_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('collection_frequency', sa.Integer(), nullable=False),
        sa.Column('rate_limit', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sources_id'), 'sources', ['id'], unique=False)
    op.create_index(op.f('ix_sources_name'), 'sources', ['name'], unique=False)
    
    # Create threats table
    op.create_table('threats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('location', ga.Geography(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('severity', sa.Integer(), nullable=False),
        sa.Column('category', sa.Enum('security', 'political', 'economic', 'environmental', 'social', 'technological', 'other', name='threat_category'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'active', 'resolved', 'false_alarm', name='threat_status'), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('missionary_relevance', sa.Float(), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('source_name', sa.String(length=255), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_threats_id'), 'threats', ['id'], unique=False)
    op.create_index(op.f('ix_threats_title'), 'threats', ['title'], unique=False)
    
    # Create intelligence table
    op.create_table('intelligence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_content', sa.Text(), nullable=False),
        sa.Column('processed_content', sa.Text(), nullable=True),
        sa.Column('threat_id', sa.Integer(), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('ai_analysis_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('processing_status', sa.Enum('pending', 'processing', 'completed', 'failed', name='processing_status'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.ForeignKeyConstraint(['threat_id'], ['threats.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_intelligence_id'), 'intelligence', ['id'], unique=False)
    
    # Create spatial indexes
    op.execute('CREATE INDEX idx_threats_location ON threats USING GIST (location);')


def downgrade() -> None:
    # Drop tables
    op.drop_table('intelligence')
    op.drop_table('threats')
    op.drop_table('sources')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS processing_status')
    op.execute('DROP TYPE IF EXISTS source_type')
    op.execute('DROP TYPE IF EXISTS threat_category')
    op.execute('DROP TYPE IF EXISTS threat_status')
