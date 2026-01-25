# tools.py
import requests
import json
from typing import List, Dict, Any, Optional
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()


class JiraXraySettings(BaseSettings):
    jira_base_url: str
    jira_email: str
    jira_api_token: str
    xray_project_key: str
    llm_provider: str = "glm"
    
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: Optional[str] = None
    azure_openai_deployment_name: Optional[str] = None
    
    anthropic_api_key: Optional[str] = None
    anthropic_model: Optional[str] = None

    google_api_key: Optional[str] = None
    google_model: str = "gemini-1.5-pro"

    zai_api_key: Optional[str] = None
    zai_model: str = "GLM-4.7-flash"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    class Config:
        env_file = ".env"


class JiraXrayClient:
    def __init__(self, settings: JiraXraySettings):
        self.settings = settings
        self.auth = (settings.jira_email, settings.jira_api_token)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def check_connection(self) -> bool:
        """Verify connection to Jira"""
        url = f"{self.settings.jira_base_url}/rest/api/3/myself"
        try:
            response = requests.get(url, headers=self.headers, auth=self.auth)
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Successfully connected to Jira as {user_data.get('displayName')} ({user_data.get('emailAddress')})")
                return True
            else:
                print(f"❌ Failed to connect to Jira. Status: {response.status_code}")
                # Print shorter error message
                try: 
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ Error connecting to Jira: {e}")
            return False

    def search_test_issue(self, test_name: str) -> Optional[str]:
        url = f"{self.settings.jira_base_url}/rest/api/3/search"
        # Buscar por nombre, sin restringir a tipo "Test"
        query = f"project={self.settings.xray_project_key} AND summary ~ '{test_name}'"
        params = {
            "jql": query,
            "fields": "key,summary,issuetype"
        }
        response = requests.get(url, headers=self.headers, auth=self.auth, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("issues"):
                return data["issues"][0]["key"]
        return None

    def import_execution_to_xray(self, payload: dict) -> Dict[str, Any]:
        """Import execution results to Xray"""
        # Determine if we are on Cloud or Server/DC
        is_cloud = "atlassian.net" in self.settings.jira_base_url
        
        if is_cloud:
            # Xray Cloud uses a separate API endpoint and authentication mechanism (Client ID/Secret)
            # which is different from Jira Basic Auth.
            # Using the internal raven proxy usually doesn't work with API tokens.
            # However, for simplicity, we will try the /import/execution endpoint that sometimes works 
            # if the plugin is configured to accept it, OR we skip it if we don't have separate credentials.
            
            # If we don't have Xray Cloud client credentials, we unfortunately can't use the Xray API directly.
            # But since we already created the Test Execution manually in 'map_to_xray_node', 
            # and we are not using the Xray 'import' feature to CREATE the execution but to UPDATE it?
            # Actually, the payload constructed in 'map_to_xray_node' is for the Xray Import API.
            
            # If we are manually creating issues, we might just want to update the status of the run.
            # Since integrating full Xray Cloud Auth is complex without ClientID/Secret, 
            # and likely the user only has Jira credentials, we will default to skipping this step strictly 
            # and relying on the 'Test Execution' issue created in 'map_to_xray_node'.
            
            print("⚠️ Xray Cloud detected. Skipping direct Xray Import API call as it requires separate credentials.")
            print("ℹ️ The Test Execution issue has been created in Jira manually.")
            return {"status": "skipped", "reason": "Xray Cloud requires Client ID/Secret"}
            
        else:
            # Jira Server / Data Center
            url = f"{self.settings.jira_base_url}/rest/raven/2.0/import/execution"
            response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
            return response.json() if response.status_code == 200 else {"error": response.text}

    def get_issue_type_id(self, type_name: str) -> Optional[str]:
        """Get the ID of an issue type by name from the project configuration"""
        url = f"{self.settings.jira_base_url}/rest/api/3/project/{self.settings.xray_project_key}"
        response = requests.get(url, headers=self.headers, auth=self.auth)
        
        if response.status_code == 200:
            project_data = response.json()
            issue_types = project_data.get("issueTypes", [])
            
            # Print available issue types for debugging
            available_types = [t.get("name") for t in issue_types]
            print(f"ℹ️ Available issue types in project {self.settings.xray_project_key}: {available_types}")
            
            for issue_type in issue_types:
                # Case-insensitive comparison
                if issue_type.get("name").lower() == type_name.lower():
                    print(f"Found project issue type '{issue_type.get('name')}' with ID: {issue_type.get('id')}")
                    return issue_type.get('id')
        
        print(f"Could not find issue type '{type_name}' in project {self.settings.xray_project_key}")
        return self._get_global_issue_type_id(type_name)

    def _get_global_issue_type_id(self, type_name: str) -> Optional[str]:
        """Fallback: Get global issue type ID"""
        url = f"{self.settings.jira_base_url}/rest/api/3/issuetype"
        response = requests.get(url, headers=self.headers, auth=self.auth)
        if response.status_code == 200:
            for issue_type in response.json():
                if issue_type.get("name") == type_name:
                    return issue_type.get('id')
        return None

    def get_or_create_test_issue(self, feature_name: str, scenario_name: str, parent_key: Optional[str] = None) -> Optional[str]:
        test_key = self.search_test_issue(f"{feature_name} - {scenario_name}")
        if not test_key:
            url = f"{self.settings.jira_base_url}/rest/api/3/issue"
            
            # Intentar en orden incluyendo nombres en español
            issue_type_names = ["Test", "Prueba", "Task", "Tarea", "Story", "Historia"]
            
            for issue_type_name in issue_type_names:
                # Obtener el ID dinámicamente
                issue_type_id = self.get_issue_type_id(issue_type_name)
                if not issue_type_id:
                    print(f"  Skipping '{issue_type_name}' (not found in project)")
                    continue
                
                payload = {
                    "fields": {
                        "project": {"key": self.settings.xray_project_key},
                        "summary": f"{feature_name} - {scenario_name}",
                        "issuetype": {"id": issue_type_id},
                        "description": {
                            "version": 1,
                            "type": "doc",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": f"Automated test from Karate feature: {feature_name}"
                                        }
                                    ]
                                },
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": f"Scenario: {scenario_name}"
                                        }
                                    ]
                                }
                            ]
                        },
                        "labels": ["automated-test", "karate"]
                    }
                }
                response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
                if response.status_code == 201:
                    created_key = response.json()["key"]
                    print(f"✓ Created {issue_type_name} issue: {created_key}")
                    
                    # Vincular al parent si existe
                    if parent_key:
                        self.link_to_parent(created_key, parent_key)
                    
                    return created_key
                else:
                    error_detail = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                    print(f"  Tipo '{issue_type_name}' falló ({response.status_code}): {error_detail}")
                    print(f"  Payload enviado: {json.dumps(payload, indent=2)}")
            
            print(f"✗ No se pudo crear issue para: {feature_name} - {scenario_name}")
        return test_key
        
    def link_to_parent(self, test_key: str, parent_key: str) -> bool:
        """Link a test issue to a parent issue (Epic, Story, Task, etc.)"""
        try:
            url = f"{self.settings.jira_base_url}/rest/api/3/issue/{test_key}/link"
            payload = {
                "outwardIssue": {"key": parent_key},
                "type": {"name": "is tested by"}
            }
            response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
            if response.status_code == 201:
                print(f"✓ Linked {test_key} to {parent_key}")
                return True
            else:
                print(f"✗ Failed to link {test_key} to {parent_key}: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error linking {test_key} to {parent_key}: {str(e)}")
            return False

    def create_test_execution(self, parent_key: Optional[str] = None) -> Optional[str]:
        """Create a Test Execution issue in Xray for tracking test runs"""
        from datetime import datetime
        
        url = f"{self.settings.jira_base_url}/rest/api/3/issue"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        summary = f"Test Execution - {timestamp}"
        if parent_key:
            summary = f"Test Execution for {parent_key} - {timestamp}"
        
        # Intentar encontrar issue type 'Test Execution' o 'Ejecución de Prueba' o 'Task'
        execution_types = ["Test Execution", "Ejecución de Prueba", "Task", "Tarea"]
        issue_type_id = None
        
        for et in execution_types:
            issue_type_id = self.get_issue_type_id(et)
            if issue_type_id:
                print(f"Using issue type for execution: {et} ({issue_type_id})")
                break
        
        if not issue_type_id:
            print("⚠️ Could not find suitable issue type for Test Execution.")
            return None
        
        payload = {
            "fields": {
                "project": {"key": self.settings.xray_project_key},
                "summary": summary,
                "issuetype": {"id": issue_type_id},
                "description": {
                    "version": 1,
                    "type": "doc",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Automated test execution from Karate"
                                }
                            ]
                        },
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Parent: {parent_key or 'N/A'}"
                                }
                            ]
                        }
                    ]
                },
                "labels": ["automated-execution", "karate"]
            }
        }
        
        response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
        if response.status_code == 201:
            exec_key = response.json()["key"]
            print(f"✓ Created Test Execution: {exec_key}")
            
            # Vincular al parent si existe
            if parent_key:
                self.link_to_parent(exec_key, parent_key)
            
            return exec_key
        else:
            print(f"✗ Failed to create Test Execution: {response.status_code}")
            return None