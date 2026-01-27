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
            
            # Custom fields
            'custom_build_number': str(build_data['build_number']),
            'custom_branch': build_data['branch'],
            'custom_commit_sha': build_data['commit_sha'],
            'custom_environment': build_data.get('environment', 'dev'),
        }
        
        # Add Jira issue if provided
        if build_data.get('jira_issue'):
            run_payload['custom_jira_issue'] = build_data['jira_issue']
        
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
        
        results_payload = []
        
        for result in test_results:
            automation_id = f"{result.feature}.{result.scenario}"
            case_id = case_id_map.get(automation_id)
            
            if not case_id:
                print(f"⚠️ Case ID not found for {automation_id}, skipping")
                continue
            
            # Map status
            if result.status == 'passed':
                status_id = 1
            elif result.status == 'failed':
                status_id = 5
            else:  # skipped, undefined, etc.
                status_id = 3
            
            result_payload = {
                'case_id': case_id,
                'status_id': status_id,
                'elapsed': f"{result.duration:.2f}s",
                'comment': result.error_message or "Test passed",
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
        
        results = self.client.get_results_for_run(run_id)
        
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
                case_id = result.get('case_id')
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
