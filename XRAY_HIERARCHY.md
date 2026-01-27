# X-Ray Test Hierarchy Structure

## Complete Flow

```
┌──────────────────────────────────────────────────────────────┐
│                  GitHub Branch Push                         │
│              (SCRUM-4-historia-3)                           │
└──────────────────────────────────┬──────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────┐
│         GitHub Actions Workflow karate-xray.yml             │
│         ✓ Extract JIRA_PARENT_ISSUE=SCRUM-4                │
│         ✓ Run Karate Tests                                  │
│         ✓ Generate karate.json                              │
│         ✓ Invoke Python Agent                               │
└──────────────────────────────────┬──────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────┐
│                  Python Agent Workflow                       │
│                 (agent/main.py)                              │
│                                                              │
│  1. Parse karate.json → TestResult objects                 │
│  2. Analyze results via LLM (with fallback)                │
│  3. Map to X-Ray hierarchy (NEW)                           │
│  4. Upload to Jira                                          │
└──────────────────────────────────┬──────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
    ┌──────────────────────────┐     ┌──────────────────────────┐
    │   STEP 1: Create         │     │   STEP 2: Create         │
    │   Test Plan              │     │   Test Execution         │
    │                          │     │                          │
    │  Issue Type: Epic/Plan   │     │  Issue Type: Task/Test   │
    │  SCRUM-30                │     │  SCRUM-31                │
    │  Labels: test-plan       │     │  Labels: test-execution  │
    │  Linked to: SCRUM-4      │     │  Linked to: SCRUM-4 & -30│
    └──────────────────────────┘     └──────────────────────────┘
                    │                             │
                    │         ┌─────────────────┬─┘
                    │         │                 │
                    ▼         ▼                 ▼
    ┌──────────────────────────────────────────────────────┐
    │    STEP 3: Create Individual Test Issues            │
    │    (for each feature scenario)                       │
    │                                                      │
    │    Issue Type: Test                                 │
    │    SCRUM-32: auth.feature - Valid credentials      │
    │    SCRUM-33: posts.feature - Create post success   │
    │    SCRUM-34: users.feature - Get all users         │
    │                                                      │
    │    Contains detailed ADF description with:          │
    │    - Step table (keyword, text, status, duration)   │
    │    - Request/Response payloads                      │
    │    - Error messages (if failed)                     │
    └──────────────────────────────────────────────────────┘
                    │
                    ▼
    ┌──────────────────────────────────────────────────────┐
    │    STEP 4: Link Tests to Test Execution             │
    │    (is_executed_by relationship)                    │
    │                                                      │
    │    SCRUM-32 ──is executed by─→ SCRUM-31            │
    │    SCRUM-33 ──is executed by─→ SCRUM-31            │
    │    SCRUM-34 ──is executed by─→ SCRUM-31            │
    └──────────────────────────────────────────────────────┘
                    │
                    ▼
    ┌──────────────────────────────────────────────────────┐
    │    STEP 5: Link Test Execution to Parent US         │
    │    (is_tested_by relationship)                      │
    │                                                      │
    │    SCRUM-4 ──is tested by─→ SCRUM-31              │
    │    (Parent receives the link via inwardIssue)       │
    └──────────────────────────────────────────────────────┘
                    │
                    ▼
    ┌──────────────────────────────────────────────────────┐
    │    STEP 6: Link Test Execution to Test Plan         │
    │    (contained_by or relates_to relationship)        │
    │                                                      │
    │    SCRUM-30 ──contains─→ SCRUM-31                  │
    │    (Test Plan receives the link via inwardIssue)    │
    └──────────────────────────────────────────────────────┘
                    │
                    ▼
    ┌──────────────────────────────────────────────────────┐
    │    STEP 7: Transition Parent US (if all pass)       │
    │                                                      │
    │    If all tests PASS:                               │
    │    SCRUM-4 → Status: Done / Finalizado / Tested    │
    │                                                      │
    │    If any test FAILS:                               │
    │    SCRUM-4 → Stays in current status                │
    └──────────────────────────────────────────────────────┘
                    │
                    ▼
        ✅ Workflow Complete
```

## Final Jira Hierarchy

```
┌─────────────────────────────────────────────┐
│ SCRUM-4 (Historia)                          │
│ "Implementar autenticación"                 │
│ Status: Done ✅ (auto-transitioned)        │
└─────────────────────────────────────────────┘
   │
   ├─ is tested by → SCRUM-30 (Test Plan)
   │                 "Test Plan - 2025-01-27 20:30"
   │                 │
   │                 └─ contains → SCRUM-31 (Test Execution)
   │                              "Test Execution - 2025-01-27 20:30"
   │                              │
   │                              ├─ is executed by ← SCRUM-32 (Test)
   │                              │                 "auth - Valid credentials"
   │                              │                 Status: PASS ✅
   │                              │
   │                              ├─ is executed by ← SCRUM-33 (Test)
   │                              │                 "posts - Create post success"
   │                              │                 Status: PASS ✅
   │                              │
   │                              └─ is executed by ← SCRUM-34 (Test)
   │                                              "users - Get all users"
   │                                              Status: PASS ✅
   │
   └─ is tested by → SCRUM-31 (direct link also)
```

## Link Direction Reference

### Correct Direction (Inward/Outward)

| Relationship | From Issue | To Issue | Method | Direction |
|---|---|---|---|---|
| **is tested by** | Parent US (SCRUM-4) | Test Execution (SCRUM-31) | POST to Parent | inwardIssue |
| **is executed by** | Test (SCRUM-32) | Test Execution (SCRUM-31) | POST to Test | outwardIssue |
| **contains** | Test Plan (SCRUM-30) | Test Execution (SCRUM-31) | POST to Plan | inwardIssue |

**Rule of Thumb:** 
- If Issue A "receives" the relationship → use `inwardIssue` when POSTing to Issue A
- If Issue A "points to" the relationship → use `outwardIssue` when POSTing to Issue A

## Implementation Details

### Tools Methods (agent/tools.py)

1. **`create_test_plan(summary)`**
   - Creates Epic or Test Plan type issue
   - Labels: test-plan, automated, karate
   - Returns: Test Plan key (e.g., SCRUM-30)

2. **`create_test_execution(parent_key, test_plan_key)`**
   - Creates Task or Test Execution type issue
   - Includes timestamp in summary
   - References both parent US and test plan in description
   - Returns: Test Execution key (e.g., SCRUM-31)

3. **`link_test_plan_to_parent(test_plan_key, parent_key)`**
   - Links: Parent "is tested by" Test Plan
   - Uses: inwardIssue on parent
   - Fallback: "relates to" if link type unavailable

4. **`link_execution_to_test_plan(execution_key, test_plan_key)`**
   - Links: Test Plan "contains" Test Execution
   - Uses: inwardIssue on test plan
   - Fallback: "relates to" if link type unavailable

5. **`link_test_to_execution(execution_key, test_key)`** (existing)
   - Links: Test "is executed by" Test Execution
   - Uses: outwardIssue from test

6. **`link_test_execution_to_parent(execution_key, parent_key)`** (existing)
   - Links: Parent "is tested by" Test Execution
   - Uses: inwardIssue on parent
   - Fallback: "relates to" if link type unavailable

### Workflow Steps (agent/nodes.py - map_to_xray_node)

```
STEP 1: Create Test Plan (if parent exists)
        └─ Link to parent US
STEP 2: Create individual Test issues (one per scenario)
STEP 3: Create Test Execution container
STEP 4: Link Tests → Test Execution (is_executed_by)
STEP 5: Link Test Execution → Parent US (is_tested_by)
STEP 6: Link Test Execution → Test Plan (contained_by)
STEP 7: Transition US if all tests pass
```

## Error Handling

- **404 on parent issue**: Gracefully skip - parent might not exist yet
- **Link type not found**: Fallback to "relates to" which always exists
- **Test creation fails**: Continue with other tests instead of stopping
- **LLM analysis timeout**: Fallback to simple pass/fail summary

## Configuration

### Environment Variables (GitHub Secrets)
```
JIRA_BASE_URL=https://ywindecker.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=SCRUM
JIRA_PARENT_ISSUE=extracted-from-branch-name
LLM_PROVIDER=glm
ZAI_API_KEY=your-api-key
```

### Branch Naming Convention
```
SCRUM-4-historia-3
└─ Regex: [A-Z]+-[0-9]+
   └─ Extracted as JIRA_PARENT_ISSUE=SCRUM-4
```

## What Changed

### Before
```
US (SCRUM-4)
└─ Test Execution (SCRUM-27)
   ├─ Test 1
   ├─ Test 2
```

### After (NEW)
```
US (SCRUM-4)
├─ Test Plan (SCRUM-30)
│  └─ Test Execution (SCRUM-31)
│     ├─ Test 1
│     ├─ Test 2
│
└─ Test Execution (SCRUM-31) [direct link]
```

This follows **X-Ray best practices** with proper hierarchy and multiple linking strategies for maximum compatibility.
