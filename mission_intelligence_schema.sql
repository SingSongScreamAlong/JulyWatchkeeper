-- Mission Intelligence Report Schema

-- Main mission intelligence report table
CREATE TABLE IF NOT EXISTS mission_intelligence_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    mission_id TEXT NOT NULL,
    region TEXT NOT NULL,
    country TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validity_period_start TIMESTAMP NOT NULL,
    validity_period_end TIMESTAMP NOT NULL,
    overall_threat_level INTEGER NOT NULL CHECK (overall_threat_level BETWEEN 1 AND 10),
    alert_status TEXT NOT NULL CHECK (alert_status IN ('Green', 'Yellow', 'Orange', 'Red', 'Black')),
    confidence_level TEXT NOT NULL CHECK (confidence_level IN ('High', 'Medium', 'Low')),
    go_no_go_recommendation BOOLEAN NOT NULL,
    go_no_go_rationale TEXT NOT NULL,
    success_probability REAL NOT NULL CHECK (success_probability BETWEEN 0 AND 1),
    recommended_team_size INTEGER NOT NULL,
    mission_type TEXT NOT NULL,
    mission_duration TEXT NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMP,
    verification_agent TEXT
);

-- Executive summary section
CREATE TABLE IF NOT EXISTS report_executive_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    key_decision_points TEXT NOT NULL,
    alternative_timing_recommendations TEXT,
    critical_briefing_highlights TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

-- Executive decision support section
CREATE TABLE IF NOT EXISTS report_decision_support (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    security_concerns TEXT NOT NULL,
    ministry_opportunities TEXT NOT NULL,
    critical_timing_considerations TEXT NOT NULL,
    resource_requirements TEXT NOT NULL,
    budget_impact TEXT NOT NULL,
    insurance_liability TEXT NOT NULL,
    recommended_team_composition TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

-- Security and threat assessment sections
CREATE TABLE IF NOT EXISTS report_security_assessment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    government_stability TEXT NOT NULL,
    political_changes TEXT NOT NULL,
    upcoming_elections TEXT,
    government_attitude TEXT NOT NULL,
    religious_freedom TEXT NOT NULL,
    policy_changes TEXT,
    visa_requirements TEXT NOT NULL,
    foreign_ministry_contacts TEXT,
    embassy_support TEXT NOT NULL,
    government_interference TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_threat_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    terrorism_threat TEXT NOT NULL,
    criminal_activity TEXT NOT NULL,
    areas_to_avoid TEXT NOT NULL,
    safe_zones TEXT NOT NULL,
    transportation_security TEXT NOT NULL,
    border_security TEXT,
    communication_security TEXT NOT NULL,
    cyber_security TEXT NOT NULL,
    targeting_patterns TEXT,
    recent_incidents TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_natural_disasters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    weather_patterns TEXT NOT NULL,
    disaster_probability TEXT NOT NULL,
    health_hazards TEXT NOT NULL,
    disease_outbreaks TEXT,
    air_water_quality TEXT,
    infrastructure_vulnerability TEXT NOT NULL,
    climate_impacts TEXT,
    emergency_response TEXT NOT NULL,
    evacuation_routes TEXT NOT NULL,
    insurance_coverage TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

-- Cultural and religious context sections
CREATE TABLE IF NOT EXISTS report_religious_landscape (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    dominant_religions TEXT NOT NULL,
    christian_presence TEXT NOT NULL,
    interfaith_relationships TEXT NOT NULL,
    religious_freedom TEXT NOT NULL,
    persecution_patterns TEXT NOT NULL,
    government_policies TEXT NOT NULL,
    religious_calendar TEXT,
    sacred_sites TEXT,
    missionary_history TEXT NOT NULL,
    local_church_contacts TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_cultural_dynamics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    cultural_values TEXT NOT NULL,
    communication_styles TEXT NOT NULL,
    gender_roles TEXT NOT NULL,
    family_structures TEXT NOT NULL,
    business_customs TEXT,
    hospitality_traditions TEXT,
    gift_protocols TEXT,
    dress_codes TEXT NOT NULL,
    language_requirements TEXT NOT NULL,
    historical_sensitivities TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_social_climate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    social_tensions TEXT NOT NULL,
    economic_conditions TEXT NOT NULL,
    youth_culture TEXT,
    education_system TEXT,
    media_landscape TEXT NOT NULL,
    social_media_usage TEXT,
    civil_society TEXT,
    corruption_levels TEXT NOT NULL,
    human_rights TEXT NOT NULL,
    womens_rights TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

-- Ministry opportunities sections
CREATE TABLE IF NOT EXISTS report_spiritual_receptivity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    spiritual_openness TEXT NOT NULL,
    responsive_demographics TEXT NOT NULL,
    effective_approaches TEXT NOT NULL,
    ministry_success TEXT,
    gospel_barriers TEXT NOT NULL,
    theological_understanding TEXT,
    syncretism_patterns TEXT,
    revival_history TEXT,
    prayer_networks TEXT,
    prophetic_significance TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_ministry_environment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    legal_framework TEXT NOT NULL,
    registration_requirements TEXT NOT NULL,
    evangelism_laws TEXT NOT NULL,
    educational_opportunities TEXT,
    medical_ministry TEXT,
    humanitarian_work TEXT,
    church_planting TEXT NOT NULL,
    literature_distribution TEXT,
    youth_ministry TEXT,
    technology_ministry TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_partnership_assessment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    missionary_presence TEXT NOT NULL,
    local_church_capacity TEXT NOT NULL,
    denominational_relationships TEXT,
    government_partnerships TEXT,
    ngo_network TEXT,
    academic_partnerships TEXT,
    business_community TEXT,
    media_relationships TEXT,
    financial_infrastructure TEXT NOT NULL,
    training_partnerships TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

-- Logistics sections
CREATE TABLE IF NOT EXISTS report_transportation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    airport_access TEXT NOT NULL,
    domestic_transportation TEXT NOT NULL,
    border_procedures TEXT,
    road_conditions TEXT NOT NULL,
    public_transportation TEXT,
    car_rental TEXT,
    fuel_availability TEXT,
    transportation_disruptions TEXT,
    evacuation_routes TEXT NOT NULL,
    cargo_regulations TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_accommodation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    accommodation_options TEXT NOT NULL,
    security_assessment TEXT NOT NULL,
    utilities_reliability TEXT NOT NULL,
    cost_of_living TEXT NOT NULL,
    food_safety TEXT NOT NULL,
    supply_availability TEXT,
    banking_services TEXT NOT NULL,
    postal_services TEXT,
    laundry_services TEXT,
    recreation_options TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_communication (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    mobile_coverage TEXT NOT NULL,
    internet_availability TEXT NOT NULL,
    wifi_security TEXT NOT NULL,
    international_calling TEXT,
    postal_reliability TEXT,
    satellite_options TEXT,
    social_media_restrictions TEXT NOT NULL,
    vpn_recommendations TEXT,
    emergency_protocols TEXT NOT NULL,
    technology_import TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

-- Health sections
CREATE TABLE IF NOT EXISTS report_healthcare (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    healthcare_quality TEXT NOT NULL,
    hospital_locations TEXT NOT NULL,
    english_speaking_medical TEXT,
    emergency_services TEXT NOT NULL,
    medical_insurance TEXT NOT NULL,
    medication_availability TEXT NOT NULL,
    medical_evacuation TEXT NOT NULL,
    dental_care TEXT,
    mental_health TEXT,
    traditional_medicine TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_health_risks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    endemic_diseases TEXT NOT NULL,
    current_outbreaks TEXT,
    food_water_safety TEXT NOT NULL,
    air_quality TEXT,
    altitude_climate TEXT,
    vector_diseases TEXT NOT NULL,
    travelers_diarrhea TEXT NOT NULL,
    std_prevalence TEXT,
    substance_abuse TEXT,
    environmental_hazards TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_medical_preparation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    required_vaccinations TEXT NOT NULL,
    preventive_medications TEXT,
    medical_kit TEXT NOT NULL,
    medication_import TEXT NOT NULL,
    medical_documentation TEXT,
    health_insurance TEXT NOT NULL,
    preexisting_conditions TEXT,
    dental_recommendations TEXT,
    eye_care TEXT,
    reproductive_health TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

-- Contacts sections
CREATE TABLE IF NOT EXISTS report_embassy_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    embassy_contact TEXT NOT NULL,
    consular_services TEXT NOT NULL,
    emergency_numbers TEXT NOT NULL,
    consular_agents TEXT,
    passport_services TEXT,
    legal_assistance TEXT,
    evacuation_assistance TEXT NOT NULL,
    registration_requirements TEXT,
    security_briefing TEXT,
    liaison_officer TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_emergency_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    police_numbers TEXT NOT NULL,
    medical_emergency TEXT NOT NULL,
    fire_department TEXT NOT NULL,
    tourist_police TEXT,
    coast_guard TEXT,
    mountain_rescue TEXT,
    poison_control TEXT,
    crisis_counseling TEXT,
    domestic_violence TEXT,
    legal_aid TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_ministry_networks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    local_church_contacts TEXT NOT NULL,
    missionary_families TEXT,
    ngo_coordination TEXT,
    government_liaisons TEXT,
    academic_contacts TEXT,
    business_network TEXT,
    media_contacts TEXT,
    medical_network TEXT,
    legal_contacts TEXT,
    translation_services TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

-- Intelligence sources sections
CREATE TABLE IF NOT EXISTS report_source_documentation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    intelligence_sources TEXT NOT NULL,
    reliability_ratings TEXT NOT NULL,
    collection_date TIMESTAMP NOT NULL,
    verification_methodology TEXT NOT NULL,
    confidence_levels TEXT NOT NULL,
    information_gaps TEXT,
    bias_considerations TEXT NOT NULL,
    update_frequency TEXT NOT NULL,
    human_intelligence TEXT,
    technical_collection TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_quality_assurance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    fact_checking TEXT NOT NULL,
    expert_review TEXT NOT NULL,
    cultural_sensitivity TEXT NOT NULL,
    security_clearance TEXT,
    peer_review TEXT,
    historical_accuracy TEXT,
    local_expert TEXT,
    academic_validation TEXT,
    government_confirmation TEXT,
    monitoring_protocols TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

-- Dynamic monitoring sections
CREATE TABLE IF NOT EXISTS report_intelligence_collection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    realtime_monitoring TEXT NOT NULL,
    early_warning TEXT NOT NULL,
    alert_systems TEXT NOT NULL,
    human_intelligence TEXT,
    social_media_monitoring TEXT NOT NULL,
    news_monitoring TEXT NOT NULL,
    government_tracking TEXT,
    economic_monitoring TEXT,
    weather_monitoring TEXT,
    infrastructure_monitoring TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_update_procedures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    update_frequency TEXT NOT NULL,
    emergency_alerts TEXT NOT NULL,
    communication_channels TEXT NOT NULL,
    escalation_procedures TEXT NOT NULL,
    version_control TEXT,
    stakeholder_notification TEXT NOT NULL,
    archive_maintenance TEXT,
    feedback_collection TEXT,
    lessons_learned TEXT,
    quality_control TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

-- Mission-specific customization sections
CREATE TABLE IF NOT EXISTS report_team_composition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    team_size TEXT NOT NULL,
    gender_composition TEXT NOT NULL,
    age_demographics TEXT,
    professional_skills TEXT NOT NULL,
    language_requirements TEXT NOT NULL,
    cultural_background TEXT,
    security_clearance TEXT,
    medical_conditions TEXT,
    family_considerations TEXT,
    leadership_structure TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_mission_optimization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    evangelism_planting TEXT,
    medical_healthcare TEXT,
    educational_training TEXT,
    humanitarian_relief TEXT,
    business_marketplace TEXT,
    research_academic TEXT,
    construction_development TEXT,
    media_communication TEXT,
    sports_recreation TEXT,
    arts_cultural TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_duration_intelligence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    short_term TEXT,
    medium_term TEXT,
    long_term TEXT,
    permanent_relocation TEXT,
    reconnaissance TEXT,
    emergency_response TEXT,
    conference_event TEXT,
    training_education TEXT,
    sabbatical_research TEXT,
    retirement_transition TEXT,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

-- Success metrics sections
CREATE TABLE IF NOT EXISTS report_effectiveness_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    opportunity_utilization TEXT NOT NULL,
    cultural_integration TEXT NOT NULL,
    relationship_building TEXT NOT NULL,
    language_acquisition TEXT,
    security_prevention TEXT NOT NULL,
    health_tracking TEXT,
    financial_efficiency TEXT NOT NULL,
    time_management TEXT,
    spiritual_growth TEXT,
    long_term_impact TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_risk_mitigation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    threat_detection TEXT NOT NULL,
    emergency_preparedness TEXT NOT NULL,
    communication_reliability TEXT NOT NULL,
    medical_preparation TEXT NOT NULL,
    cultural_sensitivity TEXT NOT NULL,
    legal_compliance TEXT NOT NULL,
    financial_security TEXT,
    technology_security TEXT NOT NULL,
    transportation_safety TEXT NOT NULL,
    disaster_preparedness TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE
);

-- Intelligence items used as sources for reports
CREATE TABLE IF NOT EXISTS report_intelligence_sources (
    report_id INTEGER NOT NULL,
    intelligence_id INTEGER NOT NULL,
    section TEXT NOT NULL,
    relevance_score REAL NOT NULL,
    PRIMARY KEY (report_id, intelligence_id, section),
    FOREIGN KEY (report_id) REFERENCES mission_intelligence_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (intelligence_id) REFERENCES intelligence_items(id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_reports_region ON mission_intelligence_reports(region);
CREATE INDEX IF NOT EXISTS idx_reports_country ON mission_intelligence_reports(country);
CREATE INDEX IF NOT EXISTS idx_reports_threat ON mission_intelligence_reports(overall_threat_level);
CREATE INDEX IF NOT EXISTS idx_reports_alert ON mission_intelligence_reports(alert_status);
CREATE INDEX IF NOT EXISTS idx_reports_mission_type ON mission_intelligence_reports(mission_type);
CREATE INDEX IF NOT EXISTS idx_intelligence_sources_report ON report_intelligence_sources(report_id);
CREATE INDEX IF NOT EXISTS idx_intelligence_sources_intel ON report_intelligence_sources(intelligence_id);
