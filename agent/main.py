#!/usr/bin/env python3
"""
Main agent entry point for TestRail integration
Loads Karate results and syncs to TestRail with AI feedback
"""

import os
import sys
import json
import subprocess
from uuid import uuid4
from dotenv import load_dotenv
from .state import AgentState, TestResult
from .karate_parser import KarateParser
from .testrail_client import TestRailClient, TestRailSettings
from .testrail_sync import TestRailSync
from .testrail_runner import TestRailRunner
from .mongo_sync import MongoSync
from .slack_notifier import SlackNotifier
from .ai_feedback import generate_pipeline_feedback
from .html_reporter import generate_html_report

# Load .env from project root (works whether called as: python -m agent.main or python agent/main.py)
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path, verbose=False)
load_dotenv()

# Load testrail.config.json and set env vars for TestRailSettings
def _load_config():
    """Load testrail.config.json and set environment variables"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, 'testrail.config.json')
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
            # Set env vars from config if not already set
            if 'testrail' in config:
                tr_config = config['testrail']
                if tr_config.get('project_id'):
                    os.environ.setdefault('TESTRAIL_PROJECT_ID', str(tr_config['project_id']))
                if tr_config.get('suite_id'):
                    os.environ.setdefault('TESTRAIL_SUITE_ID', str(tr_config['suite_id']))

_load_config()

def _get_git_commit() -> str:
    """Get current git commit SHA or fallback to local"""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ).decode().strip()
        return commit[:7]
    except:
        return "local"

def find_karate_results() -> str:
    """Find karate results file"""
    # Get the project root (parent of agent/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Primero buscar archivos detallados .karate-json.txt
    print(f"📍 Searching in: {project_root}")
    print("   Looking for detailed scenario files (.karate-json.txt):")
    
    import glob
    detailed_patterns = [
        os.path.join(project_root, "target/karate-reports/*.karate-json.txt"),
        os.path.join(project_root, "src/test/java/target/karate-reports/*.karate-json.txt"),
    ]
    
    for pattern in detailed_patterns:
        matches = glob.glob(pattern)
        for match in matches:
            print(f"   ✓ {match}")
            if os.path.exists(match):
                print(f"✓ Found detailed Karate results: {match}")
                return match
    
    # Fallback a archivos summary
    print("   Falling back to summary files:")
    paths = [
        os.path.join(project_root, "karate.json"),
        os.path.join(project_root, "target/karate-reports/karate.json"),
        os.path.join(project_root, "target/karate-reports/karate-summary.json"),
        os.path.join(project_root, "target/karate-reports/karate-summary-json.txt"),
        os.path.join(project_root, "src/test/java/target/karate-reports/karate.json"),
    ]
    
    for i, path in enumerate(paths, 1):
        exists = "✓" if os.path.exists(path) else "✗"
        print(f"   {i}. {exists} {path}")
        if os.path.exists(path):
            print(f"✓ Found Karate results: {path}")
            return path
    
    print(f"❌ No Karate results file found")
    return None

def main():
    """Main agent flow"""
    print("\n" + "="*60)
    print("🧪 TestRail Integration Agent with AI Feedback")
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
    
    # Generate HTML report
    print("\n📄 Generating HTML report...")
    try:
        html_report = generate_html_report(results, run_id, os.getenv("BUILD_NUMBER", "unknown"))
        html_path = "test-report.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        print(f"✓ HTML report saved: {html_path}")
    except Exception as e:
        print(f"⚠️ HTML report generation failed: {e}")
    
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
    
    # Generate AI Feedback
    print("\n" + "="*60)
    print("🤖 AI FEEDBACK & INSIGHTS")
    print("="*60)
    ai_feedback = ""
    try:
        llm_provider = os.getenv("LLM_PROVIDER", "glm")
        ai_feedback = generate_pipeline_feedback(results, llm_provider)
        print(ai_feedback)
        
        # Append AI feedback to report
        with open('testrail-run-data.json', 'r') as f:
            report_data = json.load(f)
        
        report_data['ai_feedback'] = ai_feedback
        
        with open('testrail-run-data.json', 'w') as f:
            json.dump(report_data, f, indent=2)
    except Exception as e:
        print(f"⚠️ AI feedback error: {e}")
    
    # Extract AI insights for MongoDB
    def _extract_ai_insights(ai_text: str) -> dict:
        """Extract structured data from AI feedback"""
        blockers = []
        recommendations = []
        
        if not ai_text:
            return {"blockers": [], "recommendations": [], "summary": ""}
        
        lines = ai_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect sections
            if any(word in line.lower() for word in ['bloqueado', 'crítico', 'blocker', 'fallo', 'error']):
                current_section = 'blockers'
            elif any(word in line.lower() for word in ['recomendación', 'acción', 'revisar', 'mejorar', 'action']):
                current_section = 'recommendations'
            
            # Extract bullet points
            if current_section and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                clean_line = line.lstrip('-•* ').strip()
                if clean_line and len(clean_line) > 5:
                    if current_section == 'blockers' and len(blockers) < 3:
                        blockers.append(clean_line)
                    elif current_section == 'recommendations' and len(recommendations) < 3:
                        recommendations.append(clean_line)
        
        return {
            "blockers": blockers,
            "recommendations": recommendations,
            "summary": ai_text[:500] if ai_text else ""
        }
    
    ai_insights = _extract_ai_insights(ai_feedback)
    
    # Save to MongoDB 💾
    print("\n" + "="*60)
    print("💾 MONGODB SYNC - HISTÓRICO & ANALYTICS")
    print("="*60)
    try:
        mongo = MongoSync()
        if mongo.enabled:
            # Usar UUID para execution batch
            execution_id = str(uuid4())
            
            # Obtener info de git/GitHub
            commit_sha = os.getenv("COMMIT_SHA", os.getenv("GITHUB_SHA", "unknown"))
            branch = os.getenv("BRANCH_NAME", os.getenv("GITHUB_HEAD_REF", "main"))
            pr_number = None
            if os.getenv("GITHUB_REF", "").startswith("refs/pull/"):
                try:
                    pr_number = int(os.getenv("GITHUB_REF", "").split("/")[2])
                except:
                    pass
            github_actor = os.getenv("GITHUB_ACTOR") or os.getenv("USER") or os.getenv("USERNAME", "dev")
            
            # Guardar cada test result
            print(f"\n📝 Saving {len(results)} test results...")
            for result in results:
                mongo.save_test_result(
                    result=result,
                    execution_id=execution_id,
                    commit_sha=commit_sha,
                    branch=branch,
                    pr_number=pr_number,
                    github_actor=github_actor,
                    testrail_case_id=case_id_map.get(f"{result.feature}.{result.scenario}"),
                )
            
            # Guardar execution summary
            print(f"\n📊 Saving execution summary...")
            mongo.save_execution_summary(
                execution_id=execution_id,
                branch=branch,
                commit_sha=commit_sha,
                results=results,
                pr_number=pr_number,
                github_actor=github_actor,
                testrail_run_id=run_id,
                ai_summary={
                    "pr_comment": ai_feedback,
                    "technical_summary": ai_insights.get("summary"),
                    "blockers": ai_insights.get("blockers", []),
                    "recommendations": ai_insights.get("recommendations", []),
                },
            )
            
            # Mostrar stats
            stats = mongo.get_branch_stats(branch)
            if stats:
                print(f"\n📈 Branch Stats ({branch}):")
                print(f"   Pass Rate: {stats.get('pass_rate', 0):.1f}%")
                print(f"   Total Tests: {stats.get('total_tests', 0)}")
                print(f"   Avg Duration: {stats.get('avg_duration_ms', 0):.0f}ms")
            
            # Detectar flaky tests
            flaky = mongo.get_flaky_tests(min_flakiness=0.3)
            if flaky:
                print(f"\n🔴 Flaky Tests Detected:")
                for test in flaky[:3]:  # Top 3
                    print(f"   {test['test_id']}: {test['flakiness']*100:.0f}% failure rate")
            
            mongo.close()
        else:
            print("⚠️ MongoDB not configured. Skipping historical data storage.")
    except Exception as e:
        print(f"⚠️ MongoDB error: {e}")
    
    # Send to Slack 📢
    print("\n" + "="*60)
    print("📢 SLACK NOTIFICATION")
    print("="*60)
    try:
        slack = SlackNotifier()
        if slack.enabled:
            # Obtener info para Slack
            commit_sha = os.getenv("COMMIT_SHA", os.getenv("GITHUB_SHA", _get_git_commit()))
            branch = os.getenv("BRANCH_NAME", os.getenv("GITHUB_HEAD_REF", "main"))
            pr_number = None
            if os.getenv("GITHUB_REF", "").startswith("refs/pull/"):
                try:
                    pr_number = int(os.getenv("GITHUB_REF", "").split("/")[2])
                except:
                    pass
            github_actor = os.getenv("GITHUB_ACTOR") or os.getenv("USER") or os.getenv("USERNAME", "dev")
            commit_sha = os.getenv("COMMIT_SHA", os.getenv("GITHUB_SHA", _get_git_commit()))
            
            # Calcular métricas
            passed = sum(1 for r in results if r.status == "passed")
            failed = sum(1 for r in results if r.status == "failed")
            skipped = sum(1 for r in results if r.status == "skipped")
            total = len(results)
            total_duration = sum(r.duration for r in results) * 1000
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            # Determinar risk level
            if pass_rate == 100:
                risk_level = "LOW"
            elif pass_rate >= 90:
                risk_level = "MEDIUM"
            else:
                risk_level = "CRITICAL"
            
            # Enviar a Slack
            # Limpiar AI feedback para Slack (remover markdown)
            clean_feedback = ai_feedback.replace("## ", "").replace("# ", "").replace("markdown", "").strip()
            
            slack.send_results(
                pass_rate=pass_rate,
                total_tests=total,
                passed_tests=passed,
                failed_tests=failed,
                skipped_tests=skipped,
                duration_ms=total_duration,
                risk_level=risk_level,
                branch=branch,
                testrail_run_id=run_id,
                github_actor=github_actor,
                commit_sha=commit_sha,
                pr_number=pr_number,
                ai_comment=clean_feedback[:500] if clean_feedback else None,
                ai_blockers=ai_insights.get("blockers", []),
                ai_recommendations=ai_insights.get("recommendations", []),
            )
            slack.close()
        else:
            print("⚠️ Slack not configured. Skipping Slack notification.")
    except Exception as e:
        print(f"⚠️ Slack error: {e}")
    
    print("\n" + "="*60)
    print(f"✅ Run #{run_id}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()