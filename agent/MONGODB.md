# 💾 MongoDB Integration - Historical Data & Analytics

## Overview

The MongoDB integration persists all test execution data, enabling:
- **Historical tracking** of test results over time
- **Flaky test detection** (tests that fail inconsistently)
- **Trend analysis** (pass rates, durations, patterns)
- **AI feedback storage** for future learning
- **Branch-level statistics** for quality metrics

## Setup

### Option 1: Local MongoDB (Development)

```bash
# Install MongoDB Community Edition
# macOS
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB
brew services start mongodb-community

# Verify connection
mongosh
```

### Option 2: MongoDB Atlas (Cloud - Recommended for CI/CD)

1. **Create free cluster:**
   - Go to https://www.mongodb.com/cloud/atlas
   - Sign up for free tier
   - Create a new project
   - Create a cluster
   - Add network access (whitelist your IP or 0.0.0.0 for GitHub Actions)
   - Create a database user (username/password)

2. **Get connection string:**
   - Click "Connect" → "Drivers" → Python
   - Copy the connection string
   - Format: `mongodb+srv://username:password@cluster.mongodb.net/agent-karate`

3. **Configure in your environment:**

   **Option A: Environment Variable**
   ```bash
   export MONGO_URI="mongodb+srv://username:password@cluster.mongodb.net/agent-karate"
   ```

   **Option B: testrail.config.json** (preferred for teams)
   ```json
   {
     "mongodb": {
       "uri": "mongodb+srv://username:password@cluster.mongodb.net/agent-karate",
       "enabled": true
     }
   }
   ```

   **Option C: GitHub Secrets** (for CI/CD)
   ```bash
   # Add to GitHub Secrets
   MONGO_URI = mongodb+srv://username:password@cluster.mongodb.net/agent-karate
   ```

### Install Dependencies

```bash
cd agent/
pip install -r requirements.txt
# Now includes: pymongo>=4.0.0
```

## Data Collections

### 1. `test_results` - Individual Test Executions
Stores every test run with full details:
```javascript
{
  test_id: "API de Posts.Obtener posts por ID",
  execution_id: "uuid-batch-001",
  run_date: ISODate("2026-01-30T15:30:00Z"),
  branch: "feature/posts-api",
  pr_number: 60,
  feature: "API de Posts",
  scenario: "Obtener posts por ID",
  tags: ["@smoke", "@critical"],
  status: "passed",
  duration_ms: 245.5,
  error_message: null,
  ai_risk_level: "LOW",
  ai_root_cause: null,
  testrail_case_id: 362
}
```

### 2. `execution_summaries` - Batch Results
Aggregates all test results from one PR/branch:
```javascript
{
  execution_batch_id: "batch-2026-01-30-60",
  run_date: ISODate("2026-01-30T15:45:00Z"),
  branch: "feature/posts-api",
  pr_number: 60,
  total_tests: 12,
  passed_tests: 11,
  failed_tests: 1,
  overall_pass_rate: 91.67,
  overall_risk_level: "MEDIUM",
  ai_pr_comment: "🟡 WARNING - REVIEW REQUIRED...",
  testrail_run_id: 42,
  test_result_ids: ["API.PostById", "API.ListPosts", ...]
}
```

### 3. `test_trends` - Historical Analysis
Tracks test health over time:
- Pass rate trends
- Flakiness scores (0 = always passes, 1 = always fails)
- Common errors
- Tag frequency

### 4. `ai_feedback` - Reusable Insights
Stores AI-generated insights for future reference:
- Root causes identified
- Affected systems
- User impact descriptions
- Recommended actions with owners

## Usage in Code

### Automatic (Built-in to Pipeline)

MongoDB sync happens automatically after TestRail sync:

```bash
python -m agent.main
```

Output includes:
```
💾 MONGODB SYNC - HISTÓRICO & ANALYTICS
================================================
✓ MongoDB connected: agent-karate
  💾 MongoDB: API Posts.Get by ID (inserted)
  💾 MongoDB: API Posts.List (inserted)
  💾 MongoDB: 12 test results saved
📊 Saving execution summary...
  📈 MongoDB: Execution summary batch-xxx saved

📈 Branch Stats (feature/posts-api):
   Pass Rate: 91.7%
   Total Tests: 12
   Avg Duration: 245ms

🔴 Flaky Tests Detected:
   API.Auth.Timeout: 40% failure rate
   API.Users.List: 35% failure rate
```

### Manual Queries

```python
from agent.mongo_sync import MongoSync

mongo = MongoSync()

# Get test history
history = mongo.get_test_history("API de Posts", "Obtener posts por ID", limit=10)

# Find flaky tests
flaky = mongo.get_flaky_tests(min_flakiness=0.3)
for test in flaky:
    print(f"{test['test_id']}: {test['flakiness']*100}% failure rate")

# Branch statistics
stats = mongo.get_branch_stats("feature/posts-api", days=7)
print(f"Pass Rate: {stats['pass_rate']}%")
```

## MongoDB Indexes (Recommended)

For optimal query performance, create these indexes:

```bash
mongosh

# Switch to database
use agent-karate

# Create indexes
db.test_results.createIndex({ execution_id: 1 })
db.test_results.createIndex({ branch: 1, run_date: -1 })
db.test_results.createIndex({ feature: 1, scenario: 1 })
db.test_results.createIndex({ status: 1 })

db.execution_summaries.createIndex({ pr_number: 1 })
db.execution_summaries.createIndex({ branch: 1, run_date: -1 })

db.test_trends.createIndex({ feature: 1, scenario: 1 })
db.test_trends.createIndex({ flakiness_score: 1 })
```

## Integration with CI/CD

### GitHub Actions

Add to `.github/workflows/karate-testrail.yml`:

```yaml
- name: Set MongoDB URI
  run: |
    echo "MONGO_URI=${{ secrets.MONGO_URI }}" >> $GITHUB_ENV

- name: Run Karate & Sync to TestRail & MongoDB
  run: |
    cd agent-karate
    python -m agent.main
```

Ensure `MONGO_URI` is added to GitHub Secrets.

## Schema Definition

See [mongo_schema.py](mongo_schema.py) for complete Pydantic models:
- `TestResultDocument`
- `ExecutionSummaryDocument`
- `TestTrendDocument`
- `AIFeedbackDocument`

## Future Enhancements

- [ ] Dashboard with historical trends and metrics
- [ ] Slack notifications with trends
- [ ] Automated flaky test report
- [ ] Predictive analysis (ML model for failure prediction)
- [ ] Integration with Jira for issue tracking
- [ ] Data retention policies and cleanup

## Troubleshooting

### MongoDB Connection Failed
```
⚠️ MongoDB connection failed: [Errno 111] Connection refused
```
- Verify MongoDB is running: `brew services list`
- Check connection string format
- Verify network access (especially for Atlas)

### pymongo not installed
```
⚠️ pymongo not installed. Install: pip install pymongo
```
```bash
pip install pymongo>=4.0.0
```

### No MongoDB URI provided
```
⚠️ MongoDB: No URI provided. Skipping MongoDB sync.
```
Set one of:
- Environment variable: `MONGO_URI`
- Config file: `testrail.config.json` → `mongodb.uri`

## Disabling MongoDB

If you don't want MongoDB:
1. Don't set `MONGO_URI`
2. Set `mongodb.enabled: false` in config
3. Leave MongoDB section empty in config

The pipeline will continue normally without MongoDB sync.
