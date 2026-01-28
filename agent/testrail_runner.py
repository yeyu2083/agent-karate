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
            automation_id = f"{result.feature}.{result.scenario}"
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
                'test_id': test_id,
                'status_id': status_id,
                'comment': result.error_message or f"Test {result.status}",
            }
            
            results_payload.append(result_payload)
        
        # Batch submit
        if results_payload:
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
    
    def generate_run_report(self, run_id: int) -> str:
        """Generate markdown report for a run"""
        run = self.client.get_run(run_id)
        
        if not run:
            return f"❌ Could not retrieve run #{run_id}"
        
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
        
        report = f"""
# TestRail Run Report: {run['name']}

## Summary
- **Run ID**: #{run['id']}
- **Total**: {total}
- **Passed**: {passed} ({pass_rate:.1f}%)
- **Failed**: {failed}
- **Skipped**: {skipped}
- **URL**: {self.client.settings.testrail_url}/index.php?/runs/view/{run['id']}

## Failed Tests
"""
        
        for result in results:
            if result.get('status_id') == 5:  # Failed
                test_id = result.get('test_id')
                case_id = test_to_case.get(test_id, 'unknown')
                comment = result.get('comment', 'N/A')
                report += f"\n- Case #{case_id}: {comment}"
        
        return report
    
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
