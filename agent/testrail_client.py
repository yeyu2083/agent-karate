# testrail_client.py
"""
TestRail API Client
Wrapper for TestRail REST API v2
"""

import requests
import json
from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings


class TestRailSettings(BaseSettings):
    testrail_url: str
    testrail_email: str
    testrail_api_key: str
    testrail_project_id: int
    testrail_suite_id: int = 1
    
    def __init__(self, **data):
        super().__init__(**data)
        # Clean up URL (remove whitespace/newlines from secrets)
        self.testrail_url = self.testrail_url.strip()
        self.testrail_email = self.testrail_email.strip()
        self.testrail_api_key = self.testrail_api_key.strip()
    
    class Config:
        env_file = ".env"


class TestRailClient:
    """TestRail API Client"""
    
    def __init__(self, settings: TestRailSettings):
        self.settings = settings
        self.auth = (settings.testrail_email, settings.testrail_api_key)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.base_url = f"{settings.testrail_url.rstrip('/')}/index.php?/api/v2"
    
    def check_connection(self) -> bool:
        """Verify connection to TestRail"""
        try:
            response = requests.get(
                f"{self.base_url}/get_projects",
                auth=self.auth,
                headers=self.headers
            )
            if response.status_code == 200:
                projects = response.json()
                print(f"✅ Successfully connected to TestRail")
                print(f"   Found {len(projects)} project(s)")
                return True
            else:
                print(f"❌ Failed to connect to TestRail. Status: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error connecting to TestRail: {e}")
            return False
    
    # ===== Project & Suite Management =====
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """GET /get_project/{project_id}"""
        url = f"{self.base_url}/get_project/{project_id}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error getting project {project_id}: {e}")
            return None
    
    def get_suite(self, suite_id: int) -> Optional[Dict[str, Any]]:
        """GET /get_suite/{suite_id}"""
        url = f"{self.base_url}/get_suite/{suite_id}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error getting suite {suite_id}: {e}")
            return None
    
    def get_sections(self, project_id: int, suite_id: int) -> List[Dict[str, Any]]:
        """GET /get_sections/{project_id}&suite_id={suite_id}"""
        url = f"{self.base_url}/get_sections/{project_id}"
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers,
                params={"suite_id": suite_id}
            )
            response.raise_for_status()
            data = response.json()
            # TestRail API v2 wraps results in a dict with 'sections' key
            if isinstance(data, dict) and 'sections' in data:
                return data['sections']
            # Fallback for other formats
            if isinstance(data, dict):
                return list(data.values())
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"❌ Error getting sections: {e}")
            return []
    
    # ===== Test Case Management =====
    def get_case(self, case_id: int) -> Optional[Dict[str, Any]]:
        """GET /get_case/{case_id}"""
        url = f"{self.base_url}/get_case/{case_id}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error getting case {case_id}: {e}")
            return None
    
    def get_cases(self, project_id: int, suite_id: int) -> List[Dict[str, Any]]:
        """GET /get_cases/{project_id}&suite_id={suite_id}"""
        url = f"{self.base_url}/get_cases/{project_id}"
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers,
                params={"suite_id": suite_id}
            )
            response.raise_for_status()
            data = response.json()
            # TestRail API v2 wraps results in a dict with 'cases' key
            if isinstance(data, dict) and 'cases' in data:
                return data['cases']
            # Fallback for other formats
            if isinstance(data, dict):
                return list(data.values())
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"❌ Error getting cases: {e}")
            return []
    
    def add_case(self, section_id: int, case_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """POST /add_case/{section_id}"""
        url = f"{self.base_url}/add_case/{section_id}"
        try:
            print(f"   DEBUG: Sending to {url}")
            print(f"   DEBUG: Payload = {case_data}")
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=case_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error adding case: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response body: {e.response.text}")
            return None
    
    def update_case(self, case_id: int, case_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """POST /update_case/{case_id}"""
        url = f"{self.base_url}/update_case/{case_id}"
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=case_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error updating case {case_id}: {e}")
            return None
    
    # ===== Test Run Management =====
    def get_run(self, run_id: int) -> Optional[Dict[str, Any]]:
        """GET /get_run/{run_id}"""
        url = f"{self.base_url}/get_run/{run_id}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error getting run {run_id}: {e}")
            return None
    
    def get_runs(self, project_id: int) -> List[Dict[str, Any]]:
        """GET /get_runs/{project_id}"""
        url = f"{self.base_url}/get_runs/{project_id}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error getting runs: {e}")
            return []
    
    def add_run(self, project_id: int, run_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """POST /add_run/{project_id}"""
        url = f"{self.base_url}/add_run/{project_id}"
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=run_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error adding run: {e}")
            print(f"   Payload: {json.dumps(run_data, indent=2)}")
            return None
    
    def update_run(self, run_id: int, run_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """POST /update_run/{run_id}"""
        url = f"{self.base_url}/update_run/{run_id}"
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=run_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error updating run {run_id}: {e}")
            return None
    
    def close_run(self, run_id: int) -> bool:
        """POST /close_run/{run_id}"""
        url = f"{self.base_url}/close_run/{run_id}"
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json={}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ Error closing run {run_id}: {e}")
            return False
    
    def get_tests(self, run_id: int) -> List[Dict[str, Any]]:
        """GET /get_tests/{run_id}"""
        url = f"{self.base_url}/get_tests/{run_id}"
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            # TestRail API v2 wraps results in a dict with 'tests' key
            if isinstance(data, dict) and 'tests' in data:
                return data['tests']
            # Fallback for other formats
            if isinstance(data, dict):
                return list(data.values())
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"❌ Error getting tests: {e}")
            return []
    
    # ===== Test Result Management =====
    def add_result(self, run_id: int, case_id: int, result_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """POST /add_result_for_case/{run_id}/{case_id}"""
        url = f"{self.base_url}/add_result_for_case/{run_id}/{case_id}"
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=result_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error adding result for case {case_id}: {e}")
            return None
    
    def add_results_batch(self, run_id: int, results: List[Dict[str, Any]]) -> bool:
        """POST /add_results/{run_id} (batch submission)"""
        url = f"{self.base_url}/add_results/{run_id}"
        try:
            payload = {"results": results}
            print(f"   DEBUG: Sending batch results to {url}")
            print(f"   DEBUG: Payload = {json.dumps(payload, indent=2)}")
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ Error adding batch results: {e}")
            print(f"   Response: {response.text if 'response' in locals() else 'N/A'}")
            return False
    
    def get_results_for_run(self, run_id: int) -> List[Dict[str, Any]]:
        """GET /get_results_for_run/{run_id}"""
        url = f"{self.base_url}/get_results_for_run/{run_id}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            # TestRail API v2 wraps results in a dict with 'results' key
            if isinstance(data, dict) and 'results' in data:
                return data['results']
            # Fallback
            if isinstance(data, dict):
                return list(data.values())
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"❌ Error getting results for run {run_id}: {e}")
            return []
            return []
    
    def get_results_for_case(self, run_id: int, case_id: int) -> List[Dict[str, Any]]:
        """GET /get_results_for_case/{run_id}/{case_id}"""
        url = f"{self.base_url}/get_results_for_case/{run_id}/{case_id}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error getting results for case {case_id}: {e}")
            return []
    
    # ===== Attachments =====
    def add_attachment_to_run(self, run_id: int, filepath: str, filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """POST /add_attachment_to_run/{run_id}"""
        url = f"{self.base_url}/add_attachment_to_run/{run_id}"
        try:
            with open(filepath, 'rb') as f:
                files = {'attachment': (filename or filepath.split('/')[-1], f)}
                # Don't use json header for multipart
                response = requests.post(
                    url,
                    auth=self.auth,
                    files=files
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"❌ Error adding attachment: {e}")
            return None
