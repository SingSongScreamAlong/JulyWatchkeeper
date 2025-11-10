# WATCHKEEPER Enhanced Features Documentation

## Overview

This document describes all enhanced features added to WATCHKEEPER v2.0, transforming it from a monitoring system into a comprehensive missionary safety and intelligence platform.

---

## 🚨 1. Alert & Notification System

### Features
- **Multi-Channel Notifications**: Email, SMS (Twilio), and Push (Firebase)
- **Configurable Alert Rules**: Set thresholds for threat level, missionary relevance, regions, and keywords
- **Intelligent Escalation**: Automatic escalation for unacknowledged high-priority alerts
- **Alert Prioritization**: 10-point priority system based on threat level and missionary relevance
- **Notification Preferences**: Per-recipient notification preferences and regional filters

### API Endpoints
```
POST   /api/v1/alerts/rules          - Create alert rule
GET    /api/v1/alerts/rules          - Get alert rules
PUT    /api/v1/alerts/rules/{id}     - Update alert rule
DELETE /api/v1/alerts/rules/{id}     - Delete alert rule
GET    /api/v1/alerts/               - Get alerts
POST   /api/v1/alerts/{id}/acknowledge - Acknowledge alert
POST   /api/v1/alerts/recipients     - Create notification recipient
GET    /api/v1/alerts/recipients     - Get recipients
POST   /api/v1/alerts/test           - Send test alert
```

### Configuration
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@domain.com
SMTP_PASSWORD=your_password
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
```

---

## 📝 2. Field Incident Reporting

### Features
- **Real-Time Incident Submission**: Field personnel can report incidents immediately
- **Incident Types**: Threat, safety, medical, security incidents
- **Severity Scoring**: 1-10 severity scale with automatic alerts for high-severity
- **Verification System**: Two-step verification process for incident validation
- **Intelligence Correlation**: Automatic correlation with existing intelligence data
- **Attachments Support**: Photos, documents, and witness information
- **Follow-Up Tracking**: Track actions taken and follow-up requirements

### API Endpoints
```
POST   /api/v1/incidents/            - Create incident
GET    /api/v1/incidents/            - Get incidents (with filters)
GET    /api/v1/incidents/high-severity - Get high-severity incidents
GET    /api/v1/incidents/{id}        - Get specific incident
PUT    /api/v1/incidents/{id}        - Update incident
POST   /api/v1/incidents/{id}/verify - Verify incident
GET    /api/v1/incidents/region/{region} - Get incidents by region
```

### Incident Data Structure
```json
{
  "incident_type": "threat",
  "severity": 8,
  "title": "Incident title",
  "description": "Detailed description",
  "location": "City, Country",
  "latitude": 12.345,
  "longitude": 67.890,
  "country": "Country Name",
  "region": "Region Name",
  "reporter_name": "John Doe",
  "reporter_contact": "john@example.com",
  "incident_date": "2025-11-10T14:30:00Z",
  "witnesses": {},
  "attachments": {}
}
```

---

## 📍 3. Personnel Tracking & Geofencing

### Features
- **Real-Time Location Tracking**: GPS tracking with opt-in consent
- **Geofencing**: Create safe zones and danger zones with automatic alerts
- **Check-In System**: Configurable check-in frequency with missed check-in alerts
- **Location History**: Complete history of personnel movements
- **Emergency Contacts**: Store and access emergency contact information
- **Medical Information**: Critical medical information for emergencies
- **Danger Zone Detection**: Automatic alerts when personnel enter danger zones
- **Distance Calculations**: Haversine formula for accurate distance measurement

### API Endpoints
```
POST   /api/v1/personnel/            - Create personnel record
GET    /api/v1/personnel/            - Get personnel
GET    /api/v1/personnel/{id}        - Get personnel details
POST   /api/v1/personnel/{id}/location - Update location
GET    /api/v1/personnel/{id}/location-history - Get location history
GET    /api/v1/personnel/check-ins/missed - Check missed check-ins
GET    /api/v1/personnel/danger-zones/current - Get personnel in danger zones
POST   /api/v1/personnel/geofences   - Create geofence
GET    /api/v1/personnel/geofences   - Get geofences
```

### Geofence Types
- **safe_zone**: Areas where personnel are safe
- **danger_zone**: High-risk areas requiring caution
- **restricted**: Areas where entry is restricted

---

## 🆘 4. Safe Contact Network

### Features
- **Contact Database**: Comprehensive database of safe contacts worldwide
- **Contact Types**: Safe houses, legal aid, medical facilities, transportation, embassies
- **Trust Levels**: 1-10 trust rating for each contact
- **Services Tracking**: Track services offered by each contact
- **Proximity Search**: Find nearby safe contacts based on GPS location
- **Access Codes**: Secure access codes for identifying missionaries
- **Verification System**: Track last verification date and verifier
- **24/7 Availability**: Flag contacts available round-the-clock

### API Endpoints
```
POST   /api/v1/personnel/safe-contacts  - Create safe contact
GET    /api/v1/personnel/safe-contacts  - Get safe contacts
GET    /api/v1/personnel/safe-contacts/nearby - Get nearby contacts
```

### Contact Types
- `safe_house`: Safe accommodation for missionaries
- `legal_aid`: Legal assistance and advocacy
- `medical`: Medical facilities and doctors
- `transportation`: Trusted transportation providers
- `embassy`: Embassy and consulate contacts
- `local_support`: Local sympathetic individuals/organizations

---

## 📊 5. Enhanced Intelligence Sources (58 Sources)

### Source Categories

#### Government Sources (8)
- US State Department Travel Advisories
- UN Security Council Press
- UK Foreign Office Travel Advice
- Canadian Travel Advisories
- Australian DFAT Travel Advice
- US Commission on International Religious Freedom
- European Asylum Support Office
- Cybersecurity & Infrastructure Security Agency

#### Health & Disaster (6)
- WHO Emergency News
- CDC Travel Health Notices
- European Centre for Disease Prevention
- ProMED Disease Alerts
- Global Disaster Alert System (GDACS)
- USGS Earthquake Alerts
- National Hurricane Center

#### Human Rights & Religious Freedom (11)
- Human Rights Watch
- Amnesty International
- Freedom House
- Open Doors USA Persecution News
- International Christian Concern
- Morning Star News
- Voice of the Martyrs
- World Evangelical Alliance
- Aid to the Church in Need
- Christian Solidarity Worldwide
- Barnabas Fund
- Release International

#### Humanitarian Organizations (6)
- ICRC (Red Cross)
- ReliefWeb - OCHA
- Doctors Without Borders
- UNHCR Refugee News
- World Food Programme

#### News Sources (15)
- BBC World News
- Al Jazeera English
- Reuters World News
- AP News
- France24 Africa
- Deutsche Welle
- Africa News
- Middle East Eye
- Asia Times
- Latin America News Dispatch
- Reporters Without Borders

#### Conflict & Security (8)
- ACLED Crisis Data
- International Crisis Group
- Institute for War & Peace Reporting
- Global Terrorism Database
- International SOS Risk Map
- Atlantic Council
- Center for Strategic & International Studies

#### Social Media & OSINT (3)
- Twitter API (optional, requires API key)
- Telegram OSINT Channels
- Reddit WorldNews

---

## 🗄️ 6. Database Enhancements

### New Tables

1. **alert_rules**: Configurable alert rules
2. **alerts**: Alert instances and acknowledgments
3. **notification_recipients**: Alert recipients and preferences
4. **field_incidents**: Field incident reports
5. **personnel**: Personnel records
6. **location_history**: GPS tracking history
7. **geofences**: Geographic boundaries
8. **geofence_events**: Geofence crossing events
9. **safe_contacts**: Safe contact network
10. **travel_routes**: Travel route safety analysis
11. **organizations**: Partner organizations for collaboration
12. **shared_intelligence**: Intelligence sharing tracking
13. **response_playbooks**: Automated response procedures
14. **playbook_executions**: Playbook execution history
15. **audit_logs**: Comprehensive audit logging
16. **threat_predictions**: ML-based threat predictions
17. **intelligence_briefings**: Generated intelligence summaries
18. **mobile_sync_queue**: Mobile offline sync queue

---

## 🔐 7. Security Features

### Implemented
- JWT authentication for all API endpoints
- Role-based access control (admin, field_staff, analyst)
- Encrypted storage for sensitive contact information
- Audit logging for all data access
- Secure API key management

### Future Enhancements (Scaffolded)
- End-to-end encryption for high-sensitivity reports
- TOR/VPN integration for restricted regions
- Self-destructing messages
- Alternative access methods (SMS, satellite)

---

## 📱 8. Mobile Support (Scaffolded)

### Features (Ready for Implementation)
- Offline-capable intelligence access
- Mobile sync queue for low-connectivity
- Push notifications via Firebase
- Location tracking background service
- Emergency button functionality
- Encrypted local storage

### Database Support
- `mobile_sync_queue` table for offline sync
- Priority-based sync ordering
- Conflict resolution support

---

## 🤖 9. Machine Learning (Scaffolded)

### Prepared Features
- Threat prediction and forecasting
- Pattern recognition across historical data
- Anomaly detection
- Clustering similar threats across regions
- Multi-language NLP support
- Sentiment analysis enhancements

### Dependencies Added
- TensorFlow, PyTorch
- scikit-learn
- Transformers (Hugging Face)
- Language detection and translation

---

## 📈 10. Analytics & Reporting (Scaffolded)

### Intelligence Briefings
- Daily/weekly automated briefings
- Executive summaries for leadership
- Regional focus reports
- Incident-specific reports
- Voice-enabled briefings (accessibility)

### Historical Analysis
- Trend analysis over time
- Seasonal pattern recognition
- Regional risk evolution
- Safe window identification

---

## 🔄 11. Collaboration Platform (Scaffolded)

### Organizations Table
- Partner missionary organizations
- NGOs and humanitarian groups
- Trust-level based sharing
- API key authentication
- Regional interest filtering

### Intelligence Sharing
- Controlled intelligence distribution
- Share levels: summary_only, full, classified
- Time-limited access
- Access tracking and auditing
- Revocation support

---

## 🎯 12. Response Playbooks (Scaffolded)

### Automated Response
- Trigger conditions based on intelligence
- Configurable action sequences
- Notification templates
- Escalation chains
- Auto-execute or manual approval
- Execution tracking and logging

### Example Playbooks
- High-threat evacuation protocol
- Medical emergency response
- Cyber attack response
- Natural disaster protocol
- Missed check-in escalation

---

## 🚀 Getting Started

### Installation

1. **Install Dependencies**
```bash
pip install -r requirements.txt
playwright install chromium
python -c "import nltk; nltk.download('vader_lexicon')"
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Initialize Database**
```bash
# Run migrations
alembic upgrade head

# Or use initialization script
python init_database.py --force
```

4. **Start Services**
```bash
# Start API server
python run.py

# Start Guardian intelligence collector
python guardian.py --monitor

# Use Docker (recommended)
docker-compose up -d
```

### Quick Test

```bash
# Test alert system
curl -X POST http://localhost:8000/api/v1/alerts/test \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"recipient_email": "test@example.com"}'
```

---

## 📚 Additional Documentation

- **API Reference**: `/api/v1/docs` (Swagger UI)
- **Database Schema**: `migrations/versions/002_enhanced_features.py`
- **Intelligence Sources**: `config/comprehensive_sources.json`
- **Original README**: `README.md`
- **Sentinel Integration**: `SENTINEL_INTEGRATION.md`
- **API Guide**: `README-API.md`

---

## 🔮 Future Roadmap

### Phase 1 (Completed)
- ✅ Alert and notification system
- ✅ Incident reporting
- ✅ Personnel tracking
- ✅ Geofencing
- ✅ Safe contact network
- ✅ 58 intelligence sources
- ✅ Database enhancements
- ✅ API endpoints

### Phase 2 (Scaffolded - Ready for Implementation)
- ⏳ ML threat prediction
- ⏳ Multi-language NLP
- ⏳ Response playbooks
- ⏳ Intelligence briefings
- ⏳ Collaboration platform
- ⏳ Travel route analysis
- ⏳ Mobile application

### Phase 3 (Planned)
- 🔜 Advanced encryption
- 🔜 Satellite communication
- 🔜 AI-powered recommendations
- 🔜 Voice interface
- 🔜 Biometric authentication
- 🔜 Blockchain for audit trail
- 🔜 Integration with more global systems

---

## 💡 Key Improvements Summary

| Feature | Before | After |
|---------|--------|-------|
| Intelligence Sources | ~10 | 58+ |
| Database Tables | 5 | 23 |
| API Endpoints | ~10 | 50+ |
| Notification Channels | 0 | 3 (Email, SMS, Push) |
| Real-Time Tracking | No | Yes |
| Incident Reporting | No | Yes |
| Geofencing | No | Yes |
| Safe Contacts | No | Yes |
| Alert System | Basic | Advanced with escalation |
| ML/AI Support | No | Scaffolded |
| Mobile Support | No | Scaffolded |
| Collaboration | No | Scaffolded |

---

## 🤝 Contributing

Contributions welcome! Key areas:
1. ML model training for threat prediction
2. Mobile app development (React Native / Flutter)
3. Additional intelligence source integrations
4. Multi-language support
5. Testing and documentation

---

## 📞 Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/yourusername/watchkeeper/issues
- Documentation: `/docs`
- API Docs: `/api/v1/docs`

---

**WATCHKEEPER v2.0** - Protecting missionaries through advanced intelligence and technology.
