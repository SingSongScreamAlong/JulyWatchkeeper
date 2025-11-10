"""Enhanced features: alerts, incidents, tracking, collaboration

Revision ID: 002_enhanced_features
Revises: 001_initial_schema
Create Date: 2025-11-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_enhanced_features'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # ============ ALERTS & NOTIFICATIONS ============
    op.create_table(
        'alert_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('threat_level_threshold', sa.Float(), default=7.0),
        sa.Column('missionary_relevance_threshold', sa.Float(), default=7.0),
        sa.Column('region_filter', postgresql.ARRAY(sa.String())),
        sa.Column('country_filter', postgresql.ARRAY(sa.String())),
        sa.Column('keyword_filter', postgresql.ARRAY(sa.String())),
        sa.Column('notification_channels', postgresql.JSONB()),  # email, sms, push
        sa.Column('escalation_rules', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_rule_id', sa.Integer(), sa.ForeignKey('alert_rules.id')),
        sa.Column('intelligence_id', sa.Integer(), sa.ForeignKey('intelligence_items.id')),
        sa.Column('alert_type', sa.String(50)),  # high_threat, critical, evacuation
        sa.Column('priority', sa.Integer(), default=5),  # 1-10
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), default='pending'),  # pending, sent, failed, acknowledged
        sa.Column('sent_at', sa.DateTime()),
        sa.Column('acknowledged_at', sa.DateTime()),
        sa.Column('acknowledged_by', sa.Integer()),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_alerts_status', 'status'),
        sa.Index('idx_alerts_priority', 'priority')
    )

    op.create_table(
        'notification_recipients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('push_token', sa.Text()),
        sa.Column('roles', postgresql.ARRAY(sa.String())),  # admin, field_staff, analyst
        sa.Column('regions', postgresql.ARRAY(sa.String())),
        sa.Column('notification_preferences', postgresql.JSONB()),
        sa.Column('active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_recipients_active', 'active')
    )

    # ============ INCIDENT REPORTING ============
    op.create_table(
        'field_incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_type', sa.String(100), nullable=False),  # threat, safety, medical, security
        sa.Column('severity', sa.Integer(), nullable=False),  # 1-10
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('location', sa.String(500)),
        sa.Column('latitude', sa.Float()),
        sa.Column('longitude', sa.Float()),
        sa.Column('country', sa.String(100)),
        sa.Column('region', sa.String(100)),
        sa.Column('reported_by', sa.Integer()),  # user_id
        sa.Column('reporter_name', sa.String(255)),
        sa.Column('reporter_contact', sa.String(255)),
        sa.Column('incident_date', sa.DateTime(), nullable=False),
        sa.Column('reported_date', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('status', sa.String(50), default='new'),  # new, investigating, resolved, false_report
        sa.Column('verified', sa.Boolean(), default=False),
        sa.Column('verified_by', sa.Integer()),
        sa.Column('verification_notes', sa.Text()),
        sa.Column('related_intelligence_id', sa.Integer(), sa.ForeignKey('intelligence_items.id')),
        sa.Column('attachments', postgresql.JSONB()),  # photos, documents
        sa.Column('witnesses', postgresql.JSONB()),
        sa.Column('actions_taken', sa.Text()),
        sa.Column('follow_up_required', sa.Boolean(), default=False),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_incidents_status', 'status'),
        sa.Index('idx_incidents_severity', 'severity'),
        sa.Index('idx_incidents_date', 'incident_date')
    )

    # ============ PERSONNEL & TEAM TRACKING ============
    op.create_table(
        'personnel',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('role', sa.String(100)),  # missionary, staff, volunteer
        sa.Column('organization', sa.String(255)),
        sa.Column('current_location', sa.String(500)),
        sa.Column('current_latitude', sa.Float()),
        sa.Column('current_longitude', sa.Float()),
        sa.Column('current_country', sa.String(100)),
        sa.Column('home_base', sa.String(255)),
        sa.Column('emergency_contact_name', sa.String(255)),
        sa.Column('emergency_contact_phone', sa.String(50)),
        sa.Column('medical_info', postgresql.JSONB()),
        sa.Column('status', sa.String(50), default='active'),  # active, on_leave, inactive
        sa.Column('tracking_enabled', sa.Boolean(), default=False),
        sa.Column('last_check_in', sa.DateTime()),
        sa.Column('check_in_frequency_hours', sa.Integer(), default=24),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_personnel_status', 'status'),
        sa.Index('idx_personnel_check_in', 'last_check_in')
    )

    op.create_table(
        'location_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('personnel_id', sa.Integer(), sa.ForeignKey('personnel.id'), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('accuracy', sa.Float()),  # GPS accuracy in meters
        sa.Column('location_name', sa.String(500)),
        sa.Column('country', sa.String(100)),
        sa.Column('activity_type', sa.String(50)),  # check_in, auto_update, manual
        sa.Column('notes', sa.Text()),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_location_personnel', 'personnel_id'),
        sa.Index('idx_location_timestamp', 'timestamp')
    )

    op.create_table(
        'geofences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('fence_type', sa.String(50)),  # safe_zone, danger_zone, restricted
        sa.Column('center_latitude', sa.Float(), nullable=False),
        sa.Column('center_longitude', sa.Float(), nullable=False),
        sa.Column('radius_meters', sa.Float(), nullable=False),
        sa.Column('polygon', postgresql.JSONB()),  # GeoJSON for complex shapes
        sa.Column('threat_level', sa.Float()),
        sa.Column('alert_on_enter', sa.Boolean(), default=True),
        sa.Column('alert_on_exit', sa.Boolean(), default=False),
        sa.Column('active', sa.Boolean(), default=True),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_geofences_active', 'active')
    )

    op.create_table(
        'geofence_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('geofence_id', sa.Integer(), sa.ForeignKey('geofences.id')),
        sa.Column('personnel_id', sa.Integer(), sa.ForeignKey('personnel.id')),
        sa.Column('event_type', sa.String(50)),  # entered, exited
        sa.Column('location_history_id', sa.Integer(), sa.ForeignKey('location_history.id')),
        sa.Column('alert_triggered', sa.Boolean(), default=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_geofence_events_timestamp', 'timestamp')
    )

    # ============ SAFE CONTACTS & RESOURCES ============
    op.create_table(
        'safe_contacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contact_type', sa.String(100)),  # safe_house, legal_aid, medical, transportation, embassy
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('organization', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('alternate_phone', sa.String(50)),
        sa.Column('email', sa.String(255)),
        sa.Column('address', sa.Text()),
        sa.Column('latitude', sa.Float()),
        sa.Column('longitude', sa.Float()),
        sa.Column('country', sa.String(100)),
        sa.Column('city', sa.String(100)),
        sa.Column('region', sa.String(100)),
        sa.Column('services_offered', postgresql.ARRAY(sa.String())),
        sa.Column('availability_24_7', sa.Boolean(), default=False),
        sa.Column('requires_appointment', sa.Boolean(), default=False),
        sa.Column('trust_level', sa.Integer(), default=5),  # 1-10
        sa.Column('last_verified', sa.DateTime()),
        sa.Column('verified_by', sa.Integer()),
        sa.Column('notes', sa.Text()),
        sa.Column('encrypted_details', sa.Text()),  # for sensitive contact info
        sa.Column('access_code', sa.String(100)),  # password/code to identify missionaries
        sa.Column('active', sa.Boolean(), default=True),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_safe_contacts_country', 'country'),
        sa.Index('idx_safe_contacts_active', 'active')
    )

    # ============ TRAVEL ROUTES & SAFETY ============
    op.create_table(
        'travel_routes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('start_location', sa.String(255), nullable=False),
        sa.Column('end_location', sa.String(255), nullable=False),
        sa.Column('start_latitude', sa.Float()),
        sa.Column('start_longitude', sa.Float()),
        sa.Column('end_latitude', sa.Float()),
        sa.Column('end_longitude', sa.Float()),
        sa.Column('route_waypoints', postgresql.JSONB()),  # array of {lat, lng, name}
        sa.Column('distance_km', sa.Float()),
        sa.Column('estimated_duration_hours', sa.Float()),
        sa.Column('transportation_modes', postgresql.ARRAY(sa.String())),  # car, bus, train, plane, boat
        sa.Column('current_risk_score', sa.Float(), default=0.0),
        sa.Column('risk_factors', postgresql.JSONB()),
        sa.Column('safe_alternative_routes', postgresql.JSONB()),
        sa.Column('checkpoints', postgresql.JSONB()),
        sa.Column('recommended', sa.Boolean(), default=True),
        sa.Column('last_assessment', sa.DateTime()),
        sa.Column('notes', sa.Text()),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_routes_risk', 'current_risk_score')
    )

    # ============ COLLABORATION & INTEL SHARING ============
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('organization_type', sa.String(100)),  # missionary, ngo, government
        sa.Column('trust_level', sa.Integer(), default=5),  # 1-10
        sa.Column('api_key', sa.String(255), unique=True),
        sa.Column('can_receive_intel', sa.Boolean(), default=False),
        sa.Column('can_submit_intel', sa.Boolean(), default=False),
        sa.Column('regions_of_interest', postgresql.ARRAY(sa.String())),
        sa.Column('contact_name', sa.String(255)),
        sa.Column('contact_email', sa.String(255)),
        sa.Column('contact_phone', sa.String(50)),
        sa.Column('active', sa.Boolean(), default=True),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_orgs_active', 'active')
    )

    op.create_table(
        'shared_intelligence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('intelligence_id', sa.Integer(), sa.ForeignKey('intelligence_items.id')),
        sa.Column('shared_with_org_id', sa.Integer(), sa.ForeignKey('organizations.id')),
        sa.Column('shared_by_user_id', sa.Integer()),
        sa.Column('share_level', sa.String(50)),  # summary_only, full, classified
        sa.Column('expiry_date', sa.DateTime()),
        sa.Column('accessed', sa.Boolean(), default=False),
        sa.Column('access_count', sa.Integer(), default=0),
        sa.Column('last_accessed', sa.DateTime()),
        sa.Column('revoked', sa.Boolean(), default=False),
        sa.Column('revoked_at', sa.DateTime()),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_shared_intel_org', 'shared_with_org_id'),
        sa.Index('idx_shared_intel_expiry', 'expiry_date')
    )

    # ============ AUTOMATED RESPONSE PLAYBOOKS ============
    op.create_table(
        'response_playbooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('trigger_conditions', postgresql.JSONB(), nullable=False),  # rules for activation
        sa.Column('priority', sa.Integer(), default=5),
        sa.Column('actions', postgresql.JSONB(), nullable=False),  # sequence of actions
        sa.Column('notification_template', postgresql.JSONB()),
        sa.Column('escalation_chain', postgresql.JSONB()),
        sa.Column('required_approvals', postgresql.ARRAY(sa.String())),
        sa.Column('auto_execute', sa.Boolean(), default=False),
        sa.Column('active', sa.Boolean(), default=True),
        sa.Column('execution_count', sa.Integer(), default=0),
        sa.Column('last_executed', sa.DateTime()),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_playbooks_active', 'active')
    )

    op.create_table(
        'playbook_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('playbook_id', sa.Integer(), sa.ForeignKey('response_playbooks.id')),
        sa.Column('intelligence_id', sa.Integer(), sa.ForeignKey('intelligence_items.id')),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('field_incidents.id')),
        sa.Column('triggered_by', sa.String(100)),  # auto, manual, alert_rule
        sa.Column('trigger_user_id', sa.Integer()),
        sa.Column('status', sa.String(50), default='pending'),  # pending, in_progress, completed, failed
        sa.Column('actions_completed', postgresql.JSONB()),
        sa.Column('actions_failed', postgresql.JSONB()),
        sa.Column('error_log', sa.Text()),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('metadata', postgresql.JSONB()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_executions_status', 'status'),
        sa.Index('idx_executions_playbook', 'playbook_id')
    )

    # ============ AUDIT LOGGING ============
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer()),
        sa.Column('username', sa.String(255)),
        sa.Column('action', sa.String(255), nullable=False),  # view, create, update, delete, export
        sa.Column('resource_type', sa.String(100)),  # intelligence, incident, personnel
        sa.Column('resource_id', sa.Integer()),
        sa.Column('ip_address', sa.String(50)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('request_method', sa.String(10)),
        sa.Column('request_path', sa.String(500)),
        sa.Column('status_code', sa.Integer()),
        sa.Column('changes', postgresql.JSONB()),  # before/after for updates
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_audit_user', 'user_id'),
        sa.Index('idx_audit_action', 'action'),
        sa.Index('idx_audit_timestamp', 'timestamp'),
        sa.Index('idx_audit_resource', 'resource_type', 'resource_id')
    )

    # ============ ML PREDICTIONS & ANALYTICS ============
    op.create_table(
        'threat_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prediction_type', sa.String(100)),  # threat_escalation, pattern_match, anomaly
        sa.Column('region', sa.String(100)),
        sa.Column('country', sa.String(100)),
        sa.Column('predicted_threat_level', sa.Float()),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('prediction_timeframe', sa.String(50)),  # 24h, 7d, 30d
        sa.Column('valid_from', sa.DateTime(), nullable=False),
        sa.Column('valid_until', sa.DateTime(), nullable=False),
        sa.Column('factors', postgresql.JSONB()),  # contributing factors
        sa.Column('related_intelligence_ids', postgresql.ARRAY(sa.Integer())),
        sa.Column('model_version', sa.String(50)),
        sa.Column('accuracy_actual', sa.Float()),  # filled in after validation
        sa.Column('validated', sa.Boolean(), default=False),
        sa.Column('notes', sa.Text()),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_predictions_region', 'region'),
        sa.Index('idx_predictions_validity', 'valid_from', 'valid_until')
    )

    # ============ INTELLIGENCE BRIEFINGS ============
    op.create_table(
        'intelligence_briefings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('briefing_type', sa.String(50)),  # daily, weekly, incident, executive
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('summary', sa.Text()),
        sa.Column('full_content', sa.Text(), nullable=False),
        sa.Column('format', sa.String(50)),  # text, html, pdf, voice
        sa.Column('priority', sa.Integer(), default=5),
        sa.Column('region_focus', sa.String(100)),
        sa.Column('time_period_start', sa.DateTime()),
        sa.Column('time_period_end', sa.DateTime()),
        sa.Column('intelligence_items_included', postgresql.ARRAY(sa.Integer())),
        sa.Column('incidents_included', postgresql.ARRAY(sa.Integer())),
        sa.Column('key_threats', postgresql.JSONB()),
        sa.Column('recommendations', sa.Text()),
        sa.Column('generated_by', sa.String(100)),  # auto, analyst_name
        sa.Column('reviewed_by', sa.Integer()),
        sa.Column('published', sa.Boolean(), default=False),
        sa.Column('publish_date', sa.DateTime()),
        sa.Column('recipients', postgresql.ARRAY(sa.Integer())),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_briefings_type', 'briefing_type'),
        sa.Index('idx_briefings_published', 'published')
    )

    # ============ MOBILE SYNC ============
    op.create_table(
        'mobile_sync_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(255)),
        sa.Column('sync_type', sa.String(50)),  # full, incremental, push
        sa.Column('data_type', sa.String(100)),  # intelligence, incidents, alerts, contacts
        sa.Column('entity_id', sa.Integer()),
        sa.Column('action', sa.String(50)),  # create, update, delete
        sa.Column('payload', postgresql.JSONB()),
        sa.Column('priority', sa.Integer(), default=5),
        sa.Column('status', sa.String(50), default='pending'),  # pending, synced, failed
        sa.Column('attempts', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text()),
        sa.Column('synced_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_sync_user_status', 'user_id', 'status'),
        sa.Index('idx_sync_device', 'device_id')
    )


def downgrade():
    op.drop_table('mobile_sync_queue')
    op.drop_table('intelligence_briefings')
    op.drop_table('threat_predictions')
    op.drop_table('audit_logs')
    op.drop_table('playbook_executions')
    op.drop_table('response_playbooks')
    op.drop_table('shared_intelligence')
    op.drop_table('organizations')
    op.drop_table('travel_routes')
    op.drop_table('safe_contacts')
    op.drop_table('geofence_events')
    op.drop_table('geofences')
    op.drop_table('location_history')
    op.drop_table('personnel')
    op.drop_table('field_incidents')
    op.drop_table('notification_recipients')
    op.drop_table('alerts')
    op.drop_table('alert_rules')
