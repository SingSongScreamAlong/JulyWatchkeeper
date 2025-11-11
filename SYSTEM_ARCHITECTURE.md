# WATCHKEEPER System Architecture - Complete Walkthrough

## 🔍 How WATCHKEEPER Works: End-to-End Flow

This document explains exactly how WATCHKEEPER collects raw data, processes it, filters noise, assesses threats, and generates the operational picture.

---

## 📡 Phase 1: Data Collection (Intelligence Gathering)

### Collection Sources

WATCHKEEPER pulls from **three types of sources**:

#### 1. **News Sources** (`src/collectors/news_collector.py`)
- **BBC News Europe** (reliability: 0.85)
- **Reuters Europe** (reliability: 0.90)
- **Deutsche Welle** (reliability: 0.80)

**How it works:**
```
1. Fetches HTML from news source homepage
2. Uses BeautifulSoup to parse article links
3. Visits each article page (rate-limited: 5 articles/cycle)
4. Extracts: title, content, URL, publication date
5. Stores raw content in database with PENDING status
```

#### 2. **Social Media Sources** (`src/collectors/social_media_collector.py`)
- Twitter/X feeds
- Facebook public pages
- Telegram channels

#### 3. **Government Sources** (`src/collectors/government_collector.py`)
- OSAC (Overseas Security Advisory Council)
- ACLED (Armed Conflict Location & Event Data)
- Official travel advisories

### Collection Frequency

**Automated Schedule (Celery Beat):**
```
Every hour:     Run full collection cycle
Every 15 min:   Process pending items
Continuous:     Active collectors monitor RSS feeds
```

### Collection Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. Collector Manager starts all collectors            │
│                                                         │
│  2. Each collector continuously polls its sources      │
│     - News Collector: Checks RSS feeds hourly          │
│     - Social Media: Monitors hashtags/keywords         │
│     - Government: Polls APIs for new advisories        │
│                                                         │
│  3. Raw content extracted:                             │
│     ├── Title                                          │
│     ├── Content (full text)                            │
│     ├── Source URL                                     │
│     ├── Publication date                               │
│     └── Source metadata                                │
│                                                         │
│  4. Stored in database:                                │
│     - Table: intelligence_items                        │
│     - Status: PENDING                                  │
│     - Assigned source_id (tracks source reliability)   │
│                                                         │
│  5. Automatically queued for processing:               │
│     - Celery task: process_intelligence_item()         │
│     - Added to Redis queue                             │
└─────────────────────────────────────────────────────────┘
```

**Code: How items enter the pipeline**
```python
# From base_collector.py line 135-194
async def _send_to_pipeline(self, item: Dict[str, Any]):
    # Create Intelligence record
    intelligence = Intelligence(
        raw_content=item.get("content", ""),
        source_id=source.id,
        processing_status=ProcessingStatus.PENDING
    )
    session.add(intelligence)
    await session.commit()

    # Queue for processing
    process_intelligence_item.delay(intelligence.id)
```

---

## ⚙️ Phase 2: Processing Pipeline (Intelligence Analysis)

Once collected, each item goes through a **5-stage processing pipeline**:

### Pipeline Architecture

```
Raw Intelligence (PENDING)
        ↓
┌───────────────────────────────────────────┐
│  Stage 1: Language Processing            │
│  - Detect language (English/French/German)│
│  - Translate to English if needed         │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│  Stage 2: AI Analysis (Ollama)           │
│  - Summarization (2-3 sentences)          │
│  - Key theme extraction                   │
│  - Threat classification (None/Low/Med/   │
│    High/Critical)                         │
│  - Geographic entity extraction           │
│  - Missionary impact assessment           │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│  Stage 3: Geographic Processing          │
│  - Extract location mentions              │
│  - Geocode to lat/long coordinates        │
│  - Identify regions (Europe focus)        │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│  Stage 4: Severity Scoring                │
│  - Keyword-based scoring (0-10)           │
│  - Weighted by keyword severity           │
│  - Integrated with AI threat level        │
│  - Final score: 60% keywords + 40% AI     │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│  Stage 5: Relevance Assessment            │
│  - Missionary keyword matching            │
│  - Mission location proximity             │
│  - Impact score from AI                   │
│  - Final: 40% keywords + 40% location +   │
│           20% AI impact                   │
└───────────────────────────────────────────┘
        ↓
Intelligence (COMPLETED)
```

### Stage 2 Deep Dive: AI Analysis with Ollama

**What the AI does** (`src/processors/ai_processor.py`):

The AI analyzes intelligence using **5 parallel tasks**:

#### 1. **Summarization**
```
Prompt: "Provide a concise summary in 2-3 sentences"
Output: "Violence erupted in Paris as protesters clashed with police..."
```

#### 2. **Theme Extraction**
```
Prompt: "Extract 3-5 key themes"
Output: ["civil unrest", "security concerns", "travel disruption"]
```

#### 3. **Threat Classification**
```
Prompt: "Classify threat level and explain reasoning"
Output: {
  "level": "High",
  "confidence": 0.85,
  "reasoning": "Armed violence, evacuation orders, targeted attacks"
}
```

#### 4. **Location Extraction**
```
Prompt: "Extract all geographic locations mentioned"
Output: ["Paris", "Île-de-France", "France", "European Union"]
```

#### 5. **Missionary Impact**
```
Prompt: "Assess impact on missionary operations"
Output: {
  "impact_level": "High",
  "affected_activities": ["travel", "public gatherings", "outreach"],
  "recommendations": "Avoid affected areas, monitor situation"
}
```

---

## 🎯 Phase 3: Threat Assessment (Deciding What's a Threat)

### How Threats Are Identified

WATCHKEEPER uses a **multi-layered approach** combining **keyword analysis**, **AI classification**, and **severity scoring**:

### 1. Keyword-Based Severity Scoring

**Severity Processor** (`src/processors/severity_processor.py`):

```python
# Keyword categories with severity weights (0.0 - 1.0)
keywords = {
    "violence": {
        "bomb": 0.9,        # Very high severity
        "terrorist": 0.9,
        "hostage": 0.9,
        "killed": 0.7,
        "riot": 0.7
    },
    "disaster": {
        "tsunami": 0.9,
        "earthquake": 0.8,
        "evacuation": 0.6
    },
    "religious": {
        "persecution": 0.9,
        "extremist": 0.8,
        "banned": 0.8,
        "arrested": 0.7
    },
    "political": {
        "coup": 0.8,
        "martial law": 0.8,
        "unrest": 0.6
    }
}
```

**Scoring Algorithm:**
```
1. Scan text for keywords (case-insensitive, whole words)
2. Count occurrences (max 3 per keyword for diminishing returns)
3. Calculate: score = weight × min(count, 3) × (1/3)
4. Aggregate across all categories
5. Normalize to 0-10 scale
6. Apply sigmoid scaling for emphasis
```

**Example:**
```
Text: "Armed terrorists attacked a church, killing 5 and taking hostages"

Matched keywords:
- "terrorist" (weight: 0.9) → score contribution: 0.9
- "attack" (weight: 0.8) → score contribution: 0.8
- "killed" (weight: 0.7) → score contribution: 0.7
- "hostage" (weight: 0.9) → score contribution: 0.9

Keyword score: 8.5/10
```

### 2. AI Threat Classification

The AI assesses threat level based on **contextual understanding**:

```
Low (2/10):      "New policy requires religious registration"
Medium (5/10):   "Protests near embassy, some violence reported"
High (8/10):     "Armed group targets western missionaries"
Critical (10/10): "Active shooter at missionary compound, evacuation in progress"
```

### 3. Final Severity Score

```python
# Weighted combination
final_score = (keyword_score × 0.6) + (ai_threat_score × 0.4)

# Clamped to 0-10 range
final_score = max(0, min(10, round(final_score)))
```

**Severity Labels:**
```
0-2:  Minimal
3-4:  Low
5-6:  Moderate
7-8:  High
9-10: Critical
```

---

## 🗑️ Phase 4: Noise Filtering (How It Filters Out Irrelevant Information)

### Multi-Stage Filtering System

#### 1. **Source Reliability Filter**

Each source has a **reliability score** (0.0 - 1.0):

```
BBC:       0.85 (High reliability)
Reuters:   0.90 (Very high reliability)
DW:        0.80 (High reliability)
Twitter:   0.50 (Medium reliability)
Blog:      0.30 (Low reliability)
```

**How it's calculated:**
```python
# From verification_service.py
reliability = (avg_confidence × 0.6) + (high_confidence_ratio × 0.4)

# Based on historical performance:
# - Average confidence score of past items
# - Proportion of high-confidence items (≥0.7)
```

Low-reliability items are **deprioritized** but not discarded.

#### 2. **Missionary Relevance Filter**

**Relevance Processor** (`src/processors/relevance_processor.py`) scores each item:

```python
# Keyword categories with relevance weights
missionary_keywords = {
    "missionary": 1.0,     # Direct relevance
    "mission": 0.9,
    "church": 0.8,
    "christian": 0.8,
    "persecution": 1.0,
    "visa": 0.8,
    "humanitarian": 0.8
}
```

**Scoring:**
```
Relevance Score = 40% keyword match + 40% location proximity + 20% AI impact

Labels:
0-2:  Not Relevant        → Archived
3-4:  Low Relevance       → Low priority queue
5-6:  Moderately Relevant → Standard processing
7-8:  Highly Relevant     → Priority queue
9-10: Critical Relevance  → Immediate alert
```

**Example Filtering:**
```
✅ KEPT: "Missionaries detained at Turkish border"
   - Relevance: 9/10 (missionary keyword + security)

❌ FILTERED: "New restaurant opens in Paris"
   - Relevance: 0/10 (no missionary connection)

✅ KEPT: "Visa policy changes for religious workers"
   - Relevance: 7/10 (visa + religious keywords)

❌ FILTERED: "Football match results from Madrid"
   - Relevance: 0/10 (no connection)
```

#### 3. **Geographic Filter**

**Europe Focus** (`europe_filter.py`):

```python
european_countries = [
    "france", "germany", "italy", "spain", "uk",
    "poland", "romania", "greece", "portugal", ...
]

european_regions = [
    "europe", "european union", "schengen",
    "balkans", "scandinavia", "mediterranean", ...
]
```

Items are **scored** by European relevance:
- Direct country mention: +2 points
- European region: +1 point
- Non-European: 0 points

#### 4. **Time-Based Filter**

```python
# Items older than 30 days are deprioritized
# Items older than 90 days are archived
# Duplicate content (same URL) is discarded
```

#### 5. **Duplicate Detection**

```python
# From verification_service.py
def find_consensus(item):
    # Find similar items within 24 hours
    # Calculate text similarity (Jaccard index)
    # If similarity ≥ 0.7:
    #   - Mark as duplicate
    #   - Link to original
    #   - Increase confidence of original
```

---

## 📊 Phase 5: Operational Picture Generation

### Dashboard Components

The operational picture is generated from processed intelligence through several views:

#### 1. **Threat Map** (Geographic Visualization)

```python
# Data points plotted on map:
for item in intelligence_items:
    if item.latitude and item.longitude:
        marker = {
            "lat": item.latitude,
            "lng": item.longitude,
            "severity": item.severity_score,
            "color": severity_color(item.severity_score),
            "popup": {
                "title": item.title,
                "summary": item.ai_analysis.summary,
                "threat_level": item.severity_label
            }
        }
```

**Color Coding:**
```
Green:   Minimal (0-2)
Yellow:  Low-Moderate (3-6)
Orange:  High (7-8)
Red:     Critical (9-10)
```

#### 2. **Mission Intelligence Report**

Generated from `guardian.py` and report generators:

```
=== MISSION INTELLIGENCE REPORT ===
Generated: 2025-01-15 14:30 UTC
Valid Until: 2025-01-22 14:30 UTC

EXECUTIVE SUMMARY
-----------------
[AI-generated summary of top threats]

HIGH-PRIORITY THREATS (7)
-----------------
1. [CRITICAL] Missionary detention in Turkey
   Location: Istanbul
   Severity: 9/10
   Impact: High - Affects all missionaries in region
   Status: Ongoing
   Recommendation: Avoid travel, contact embassy

2. [HIGH] New visa restrictions for religious workers
   Location: Hungary
   Severity: 7/10
   Impact: Medium - Affects new entries only
   Status: In effect from Feb 1
   Recommendation: Accelerate pending applications

REGIONAL OVERVIEW
-----------------
Europe:
  - Total Threats: 23
  - Critical: 2
  - High: 7
  - Medium: 14
  - Low: 0

  Trending: ↑ Visa restrictions
           ↑ Security concerns
           ↓ Health risks

MISSION FIELD IMPACT
-------------------
Turkey:   [⚠️ HIGH RISK]  - Active persecution
Germany:  [✓ SAFE]        - Stable operations
France:   [⚠️ MODERATE]   - Civil unrest in cities
Poland:   [✓ SAFE]        - No current threats
...
```

#### 3. **Analytics Dashboard**

Real-time metrics from `analytics_tasks.py`:

```
Dashboard displays:

┌─────────────────────────────────────┐
│  SYSTEM OVERVIEW                    │
│  Total Intelligence: 1,234          │
│  Total Threats: 56                  │
│  Active Alerts: 8                   │
│  Processing Rate: 15.5 items/hour   │
│  System Health: ✓ Healthy           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  THREAT BREAKDOWN                   │
│  Critical: █████ 5 (8.9%)           │
│  High:     ███████████ 12 (21.4%)   │
│  Medium:   ████████████████ 28      │
│  Low:      ███████ 11 (19.6%)       │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  REGIONAL HOTSPOTS                  │
│  🔴 Turkey        (9 threats)        │
│  🟠 Russia        (7 threats)        │
│  🟠 Hungary       (5 threats)        │
│  🟡 France        (4 threats)        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  TRENDING TOPICS (Last 7 days)      │
│  ↑ Visa restrictions (+45%)         │
│  ↑ Security incidents (+23%)        │
│  ↓ Health concerns (-12%)           │
│  → Travel advisories (stable)       │
└─────────────────────────────────────┘
```

#### 4. **Alert System**

**Automatic alerts triggered** when:

```python
# From alert_tasks.py
if threat_level >= 9.0:
    # CRITICAL: Email + SMS
    send_email(to=alert_recipients)
    send_sms(to=emergency_contacts)

elif threat_level >= 8.0:
    # HIGH: Email only
    send_email(to=alert_recipients)

elif threat_level >= 6.0:
    # MEDIUM: Email digest
    add_to_daily_digest()
```

**Alert Content:**
```
Subject: [WATCHKEEPER CRITICAL] Missionary Detention - Turkey

IMMEDIATE ACTION REQUIRED

Title: European missionaries detained at Istanbul airport
Threat Level: 9/10 (Critical)
Location: Istanbul, Turkey
Confidence: 0.88

Summary:
Three European missionaries were detained by Turkish authorities
at Atatürk Airport while attempting to enter the country...

Recommended Actions:
1. Do not travel to Turkey until situation resolves
2. Contact local embassy for updates
3. Review security protocols
4. Monitor situation hourly

Intelligence ID: 12345
Source: Reuters (reliability: 0.90)
Verified: Yes (3 sources confirm)
```

---

## 🔄 Complete System Flow (Putting It All Together)

```
┌──────────────────────────────────────────────────────────────┐
│ STEP 1: COLLECTION                                           │
├──────────────────────────────────────────────────────────────┤
│ BBC News scraper runs → finds article about protest in Paris│
│ Extracts: title, content, URL, date                         │
│ Stores in database with status=PENDING                      │
│ Automatically queues for processing (Celery)                │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 2: LANGUAGE PROCESSING                                  │
├──────────────────────────────────────────────────────────────┤
│ Detect language → English ✓                                 │
│ No translation needed                                        │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 3: AI ANALYSIS (Ollama)                                │
├──────────────────────────────────────────────────────────────┤
│ Summary: "Violent protest in Paris, 50+ arrested"           │
│ Themes: ["civil unrest", "security", "travel disruption"]   │
│ Threat Level: Medium (confidence: 0.75)                     │
│ Locations: ["Paris", "France"]                              │
│ Impact: Medium - affects travel in city center              │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 4: GEOGRAPHIC PROCESSING                                │
├──────────────────────────────────────────────────────────────┤
│ Extract: "Paris" → Geocode to 48.8566, 2.3522              │
│ Region: Europe (✓ relevant)                                 │
│ Mission field proximity: 15km from active mission           │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 5: SEVERITY SCORING                                     │
├──────────────────────────────────────────────────────────────┤
│ Keywords matched: "protest"(0.5), "arrested"(0.6)           │
│ Keyword score: 5.5/10                                        │
│ AI threat: Medium → 5/10                                     │
│ Final: (5.5×0.6) + (5×0.4) = 5.3 → 5/10 (Moderate)         │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 6: RELEVANCE ASSESSMENT                                 │
├──────────────────────────────────────────────────────────────┤
│ Keywords: "christian"(0.8) "church"(0.8) not found → 0/10   │
│ Location: 15km from mission → 6/10                          │
│ AI impact: Medium → 5/10                                     │
│ Final: (0×0.4) + (6×0.4) + (5×0.2) = 3.4 → 3/10 (Low)      │
│                                                              │
│ Decision: LOW RELEVANCE - Archive for reference only        │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 7: STORAGE & INDEXING                                   │
├──────────────────────────────────────────────────────────────┤
│ Status: COMPLETED                                            │
│ Stored with:                                                 │
│   - Severity: 5/10 (Moderate)                               │
│   - Relevance: 3/10 (Low)                                   │
│   - Location: Paris (48.8566, 2.3522)                       │
│   - All AI analysis data                                     │
│   - Processing time: 3.2 seconds                            │
│                                                              │
│ Alert Check: Severity < 8.0 → No alert                      │
│ Dashboard: Added to map (yellow marker)                     │
│ Search: Indexed for full-text search                        │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎯 Example: High-Threat Item Processing

Let's trace a **critical threat** through the system:

```
Raw Article: "Armed extremists attack missionary compound in Turkey,
             several staff members taken hostage. Government has
             issued evacuation orders for all foreign workers."
```

### Processing Steps:

**1. Collection**
```
Source: Reuters (reliability: 0.90)
Timestamp: 2025-01-15 09:30 UTC
Status: PENDING → Queued immediately
```

**2. AI Analysis**
```
Summary: "Armed attack on missionary facility in Turkey with hostages,
         evacuation orders issued"
Themes: ["terrorism", "hostage situation", "missionary safety", "evacuation"]
Threat: CRITICAL (confidence: 0.95)
Locations: ["Turkey", "Ankara region"]
Impact: CRITICAL - Direct threat to missionaries
```

**3. Severity Scoring**
```
Keywords detected:
- "extremist" (0.8)
- "attack" (0.8)
- "missionary" (0.6)
- "hostage" (0.9)
- "evacuate" (0.8)

Keyword score: 9.2/10
AI threat: Critical → 10/10
Final: (9.2×0.6) + (10×0.4) = 9.5 → 10/10 ✓ CRITICAL
```

**4. Relevance Assessment**
```
Keywords:
- "missionary" (1.0) ✓✓
- "extremist" (0.8) ✓
- "evacuate" (0.7) ✓

Keyword score: 9/10
Location: Turkey (active mission field) → 10/10
AI impact: Critical → 10/10
Final: (9×0.4) + (10×0.4) + (10×0.2) = 9.6 → 10/10 ✓ CRITICAL
```

**5. Automatic Actions Triggered**
```
✓ Status: COMPLETED
✓ Severity: 10/10 (CRITICAL)
✓ Relevance: 10/10 (CRITICAL)

Alerts triggered:
✓ Email sent to: ["admin@mission.org", "security@mission.org"]
✓ SMS sent to: [emergency contacts]
✓ Webhook: Security dashboard notified
✓ Dashboard: RED marker on Turkey
✓ Report: Added to IMMEDIATE ACTION section
✓ Notification: All users alerted in-app
```

**6. Operational Picture Impact**
```
Dashboard updated:
- Active Alerts: 7 → 8
- Critical Threats: 4 → 5
- Turkey status: SAFE → HIGH RISK
- Travel advisory: Updated to "DO NOT TRAVEL"

Map updated:
- Red marker added to Turkey
- Radius: 100km danger zone highlighted
- All mission fields in region flagged

Report generated:
=== IMMEDIATE ACTION REQUIRED ===
CRITICAL THREAT: Hostage situation in Turkey
All missionaries must evacuate immediately
Contact embassy: +90 312 XXX XXXX
Evacuation route: [map link]
```

---

## 🔍 How the System Filters Noise

**Example: Sports Article Filtered**

```
Input: "Paris Saint-Germain defeats Marseille 3-1 in heated match"

Processing:
├─ Language: English ✓
├─ AI Analysis:
│  └─ Summary: "Football match result"
│  └─ Threat: None (0/10)
│  └─ Impact: None
├─ Severity: 0/10 (no threat keywords)
├─ Relevance: 0/10 (no missionary keywords)
│
Decision: FILTERED OUT
Action: Not stored in active intelligence
Result: System never sees this data
```

**Example: Borderline Article Kept**

```
Input: "New French law requires registration for religious organizations"

Processing:
├─ AI Analysis:
│  └─ Threat: Low (2/10)
│  └─ Impact: Medium (affects churches)
├─ Severity: 3/10 (policy change, minor keywords)
├─ Relevance: 7/10
│  └─ "religious"(0.7) + "registration"(0.7) + location
│
Decision: KEPT (low severity but high relevance)
Action: Stored, no alert, added to weekly digest
Result: Tracked for trend analysis
```

---

## 📈 Analytics: How Trends Are Identified

```python
# From analytics_tasks.py
def generate_daily_metrics():
    # Count threats by severity over time
    # Track keyword frequency trends
    # Monitor geographic hotspots
    # Calculate processing performance

    trends = {
        "visa_restrictions": {
            "week_ago": 12,
            "today": 18,
            "trend": "↑ +50%",
            "status": "INCREASING"
        },
        "security_incidents": {
            "week_ago": 8,
            "today": 10,
            "trend": "↑ +25%",
            "status": "INCREASING"
        }
    }

    # Alert if trend exceeds threshold
    if trends["visa_restrictions"]["change"] > 40%:
        create_trend_alert("Significant increase in visa restrictions")
```

---

## 🎓 Key Takeaways

### What Makes WATCHKEEPER Effective:

1. **Multi-Source Collection**: Aggregates from news, social media, government
2. **AI + Keyword Hybrid**: Combines machine learning with rule-based scoring
3. **Contextual Understanding**: AI understands nuance ("arrested" at protest vs. arrested missionary)
4. **Multi-Layer Filtering**: Reliability × Relevance × Severity × Recency
5. **Automated Prioritization**: Critical items → immediate alerts, low items → archived
6. **Continuous Learning**: Source reliability updates based on historical accuracy
7. **Geographic Focus**: Prioritizes European missionary-relevant regions
8. **Real-Time Processing**: Sub-5-second processing per item
9. **Consensus Verification**: Cross-references similar reports from multiple sources

### The Result:

From **thousands of daily news articles** → **~50-100 relevant intelligence items** → **5-10 actionable threats** → **1-3 critical alerts**

This creates a **clear operational picture** without overwhelming users with noise.
