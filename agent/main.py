#!/usr/bin/env python3
"""
Main agent entry point for TestRail integration
Loads Karate results and syncs to TestRail
"""

import os
import sys
from dotenv import load_dotenv
from .state import AgentState, TestResult
from .karate_parser import KarateParser
from .testrail_client import TestRailClient, TestRailSettings
from .testrail_sync import TestRailSync
from .testrail_runner import TestRailRunner

# Load environment
load_dotenv()

def find_karate_results() -> str:
    """Find karate results file"""
    # Get the project root (parent of agent/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    paths = [
        os.path.join(project_root, "karate.json"),
        os.path.join(project_root, "target/karate-reports/karate-summary.json"),
        os.path.join(project_root, "target/karate-reports/karate.json"),
        os.path.join(project_root, "src/test/java/target/karate-reports/karate.json"),
    ]
    
    for path in paths:
        if os.path.exists(path):
            print(f"✓ Found Karate results: {path}")
            return path
    
    print(f"❌ No Karate results file found (searched in {project_root})")
    return None

def main():
    """Main agent flow"""
    print("\n" + "="*60)
    print("🧪 TestRail Integration Agent")
    print("="*60)
    
    # Find Karate results
    karate_json_path = find_karate_results()
    if not karate_json_path:
        print("⚠️ No Karate results to process")
        return
    
    # Parse results
    print("\n📋 Parsing Karate results...")
    parser = KarateParser()
    try:
        results = parser.parse_karate_json(karate_json_path)
        print(f"✓ Loaded {len(results)} test results")
    except Exception as e:
        print(f"❌ Parse error: {e}")
        return
    
    if not results:
        print("⚠️ No test results found")
        return
    
    # Print results summary
    passed = sum(1 for r in results if r.status == "passed")
    failed = sum(1 for r in results if r.status == "failed")
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    # Connect to TestRail
    print("\n🔌 Connecting to TestRail...")
    try:
        settings = TestRailSettings()
        client = TestRailClient(settings)
        if not client.check_connection():
            print("❌ Cannot connect to TestRail")
            return
        print("✓ Connected to TestRail")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Sync test cases
    print("\n📝 Syncing test cases...")
    print(f"   Using Project ID: {settings.testrail_project_id}")
    print(f"   Using Suite ID: {settings.testrail_suite_id}")
    try:
        sync = TestRailSync(
            client,
            settings.testrail_project_id,
            settings.testrail_suite_id
        )
        case_id_map = sync.sync_cases_from_karate(results)
        print(f"✓ Synced {len(case_id_map)} test cases")
    except Exception as e:
        import traceback
        print(f"❌ Sync error: {e}")
        print(f"   {traceback.format_exc()}")
        return
    
    # Create test run
    print("\n🚀 Creating test run...")
    try:
        build_data = {
            'build_number': os.getenv("BUILD_NUMBER", "unknown"),
            'branch': os.getenv("BRANCH_NAME", "unknown"),
            'commit_sha': os.getenv("COMMIT_SHA", ""),
            'commit_message': os.getenv("COMMIT_MESSAGE", ""),
            'jira_issue': os.getenv("JIRA_PARENT_ISSUE", None),
            'environment': 'dev'
        }
        
        runner = TestRailRunner(client)
        case_ids = list(case_id_map.values())
        run_id = runner.create_run_from_build(
            settings.testrail_project_id,
            settings.testrail_suite_id,
            build_data,
            case_ids
        )
        
        if not run_id:
            print("❌ Failed to create test run")
            return
        
        print(f"✓ Created run #{run_id}")
    except Exception as e:
        print(f"❌ Run creation error: {e}")
        return
    
    # Submit results
    print("\n📊 Submitting results...")
    try:
        success = runner.submit_results(run_id, results, case_id_map)
        if success:
            print("✓ Results submitted")
        else:
            print("⚠️ Some results failed to submit")
    except Exception as e:
        print(f"❌ Submit error: {e}")
        return
    
    # Attach artifact
    print("\n📎 Attaching artifact...")
    try:
        if os.path.exists(karate_json_path):
            runner.attach_artifact(run_id, karate_json_path)
            print("✓ Artifact attached")
    except Exception as e:
        print(f"⚠️ Attachment error: {e}")
    
    # Generate report
    print("\n📝 Generating report...")
    try:
        report_data = runner.generate_run_report(run_id)
        print(report_data['markdown'])
        
        # Save report data for GitHub Actions
        import json
        with open('testrail-run-data.json', 'w') as f:
            json.dump(report_data, f)
    except Exception as e:
        print(f"⚠️ Report error: {e}")
    
    print("\n" + "="*60)
    print(f"✅ Run #{run_id}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()