# testrail_runner.py
"""
TestRail Test Execution
Execute tests and submit results to TestRail
"""

from typing import List, Optional, Dict, Any
from .testrail_client import TestRailClient
from .state import TestResult


class TestRailRunner:
    """Execute tests and submit results to TestRail"""
    
    def __init__(self, testrail_client: TestRailClient):
        self.client = testrail_client
    
    def create_run_from_build(
        self,
        project_id: int,
        suite_id: int,
        build_data: Dict[str, Any],
        case_ids: List[int]
    ) -> Optional[int]:
        """Create TestRail run for a build"""
        
        run_payload = {
            'suite_id': suite_id,
            'name': f"Build #{build_data['build_number']} - {build_data['branch']}",
            'description': self._build_description(build_data),
            'include_all': False,
            'case_ids': case_ids,
        }
        
        run = self.client.add_run(project_id, run_payload)
        
        if run:
            print(f"✓ Created run #{run['id']}: {run_payload['name']}")
            return run['id']
        
        return None
    
    def submit_results(
        self,
        run_id: int,
        test_results: List[TestResult],
        case_id_map: Dict[str, int]
    ) -> bool:
        """
        Submit test results to TestRail run (batch)
        
        Args:
            run_id: TestRail run ID
            test_results: List of TestResult from Karate
            case_id_map: Mapping of automation_id → case_id
        """
        
        # Get tests in the run to get test_ids
        tests_in_run = self.client.get_tests(run_id)
        print(f"   Found {len(tests_in_run)} tests in run")
        
        # Build case_id → test_id mapping
        test_id_map = {}
        for test in tests_in_run:
            test_id_map[test['case_id']] = test['id']
        
        results_payload = []
        
        for result in test_results:
            # Match the same logic as sync_cases_from_karate
            if result.feature == result.scenario:
                # Fallback mode: feature summary only
                automation_id = result.feature
            else:
                # Individual scenario mode
                scenario_clean = result.scenario.split('.')[0] if '.' in result.scenario else result.scenario
                automation_id = f"{result.feature}.{scenario_clean}"
            
            case_id = case_id_map.get(automation_id)
            
            if not case_id:
                print(f"⚠️ Case ID not found for {automation_id}, skipping")
                continue
            
            test_id = test_id_map.get(case_id)
            if not test_id:
                print(f"⚠️ Test ID not found for case {case_id}, skipping")
                continue
            
            # Map status
            if result.status == 'passed':
                status_id = 1
            elif result.status == 'failed':
                status_id = 5
            else:  # skipped, undefined, etc.
                status_id = 3
            
            result_payload = {
                'test_id': int(test_id),
                'status_id': int(status_id),
                'comment': result.error_message or f"Test {result.status}",
            }
            
            results_payload.append(result_payload)
        
        # Batch submit
        if results_payload:
            print(f"\n📤 Payload to send:")
            for r in results_payload:
                print(f"   {r}")
            
            success = self.client.add_results_batch(run_id, results_payload)
            
            if success:
                print(f"✓ Submitted {len(results_payload)} results to run #{run_id}")
                return True
        
        return False
    
    def attach_artifact(self, run_id: int, artifact_path: str) -> bool:
        """Attach Karate JSON to run"""
        try:
            result = self.client.add_attachment_to_run(run_id, artifact_path, 'karate.json')
            if result:
                print(f"✓ Attached artifact to run #{run_id}")
                return True
        except Exception as e:
            print(f"⚠️ Could not attach artifact: {e}")
        
        return False
    
    def generate_run_report(self, run_id: int) -> dict:
        """Generate comprehensive report for a run (returns dict with markdown and data)"""
        run = self.client.get_run(run_id)
        
        if not run:
            return {
                'markdown': f"❌ Could not retrieve run #{run_id}",
                'run_id': run_id,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'total': 0
            }
        
        # Get tests and results
        tests = self.client.get_tests(run_id)
        results = self.client.get_results_for_run(run_id)
        
        # Build test_id → case_id mapping
        test_to_case = {test['id']: test['case_id'] for test in tests}
        
        passed = sum(1 for r in results if r.get('status_id') == 1)
        failed = sum(1 for r in results if r.get('status_id') == 5)
        skipped = sum(1 for r in results if r.get('status_id') == 3)
        total = len(results)
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        # Build status emoji
        if failed == 0:
            status_emoji = "✅"
        elif passed == 0:
            status_emoji = "❌"
        else:
            status_emoji = "⚠️"
        
        # Calculate percentages safely
        failed_rate = (failed/total*100) if total > 0 else 0
        skipped_rate = (skipped/total*100) if total > 0 else 0
        
        report = f"""{status_emoji} **TestRail Run #{run['id']}** - {run['name']}

### 📊 Results Summary
| Metric | Count | Rate |
|--------|-------|------|
| Total | {total} | 100% |
| ✅ Passed | {passed} | {pass_rate:.1f}% |
| ❌ Failed | {failed} | {failed_rate:.1f}% |
| ⏭️ Skipped | {skipped} | {skipped_rate:.1f}% |

### 🔗 Links
- [View in TestRail]({self.client.settings.testrail_url}/index.php?/runs/view/{run['id']})

### Failed Tests
"""
        
        if failed > 0:
            for result in results:
                if result.get('status_id') == 5:  # Failed
                    test_id = result.get('test_id')
                    case_id = test_to_case.get(test_id, 'unknown')
                    comment = result.get('comment', 'N/A')
                    report += f"- **Case #{case_id}**: {comment}\n"
        else:
            report += "✅ All tests passed!\n"
        
        return {
            'markdown': report,
            'run_id': run_id,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'total': total,
            'pass_rate': pass_rate,
            'testrail_url': f"{self.client.settings.testrail_url}/index.php?/runs/view/{run['id']}"
        }
    
    def _build_description(self, build_data: Dict[str, Any]) -> str:
        """Build run description"""
        lines = [
            f"Build: #{build_data['build_number']}",
            f"Branch: {build_data['branch']}",
            f"Commit: {build_data['commit_sha']}",
        ]
        
        if build_data.get('commit_message'):
            lines.append(f"Message: {build_data['commit_message']}")
        
        if build_data.get('jira_issue'):
            lines.append(f"Jira: {build_data['jira_issue']}")
        
        lines.append(f"Environment: {build_data.get('environment', 'dev')}")
        
        return '\n'.join(lines)
