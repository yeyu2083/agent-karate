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
        """Skip Xray import - we handle tests via Jira issues directly"""
        print("ℹ️ Tests are managed as Jira issues, not via Xray import API")
        return {"status": "skipped", "reason": "Using native Jira issue tracking"}

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

    def get_or_create_test_issue(self, feature_name: str, scenario_name: str, parent_key: Optional[str] = None, steps: List[dict] = []) -> Optional[str]:
        test_key = self.search_test_issue(f"{feature_name} - {scenario_name}")
        if not test_key:
            url = f"{self.settings.jira_base_url}/rest/api/3/issue"
            
            # Intentar en orden incluyendo nombres en español
            issue_type_names = ["Test", "Prueba", "Task", "Tarea", "Story", "Historia"]
            
            # Construir descripción detallada con pasos
            description_content = [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Automated test from Karate feature: {feature_name}",
                            "marks": [{"type": "strong"}]
                        }
                    ]
                }
            ]
            
            # Tabla de pasos si existen
            if steps:
                description_content.append({"type": "paragraph", "content": [{"type": "text", "text": "Execution Steps:"}]})
                
                # Crear tabla manual para pasos en formato ADF de Jira
                # Nota: Las tablas ADF son complejas de construir manualmente sin librerías.
                # Usaremos CodeBlock para logs formateados que es más seguro y legible.
                steps_text = "Keyword | Step Name | Data | Status | Duration (ms)\n"
                steps_text += "--- | --- | --- | --- | ---\n"
                for step in steps:
                    status_icon = "✅" if step.get('status') == 'passed' else "❌"
                    
                    # Previsualización de data (si existe)
                    data_preview = ""
                    if step.get('data'):
                         data_val = str(step.get('data')).replace('\n', ' ')
                         # Trucar si es muy largo para la tabla
                         data_preview = (data_val[:30] + '...') if len(data_val) > 30 else data_val

                    steps_text += f"{step.get('keyword')} | {step.get('text')} | {data_preview} | {status_icon} {step.get('status')} | {step.get('duration_ms'):.2f}\n"
                    
                    # Mostrar data completa debajo del paso
                    if step.get('data'):
                        steps_lines = str(step.get('data')).split('\n')
                        for line in steps_lines:
                             steps_text += f"> Data: {line}\n"

                    if step.get('error'):
                         steps_text += f"> Error: {step.get('error')}\n"
                
                description_content.append({
                    "type": "codeBlock",
                    "attrs": {"language": "markdown"},
                    "content": [{"type": "text", "text": steps_text}]
                })
            else:
                description_content.append({
                     "type": "paragraph",
                     "content": [{"type": "text", "text": f"Scenario: {scenario_name}"}]
                })

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
                            "content": description_content
                        },
                        "labels": ["automated-test", "karate", "agent-created"]
                    }
                }
                response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
                if response.status_code == 201:
                    created_key = response.json()["key"]
                    print(f"✓ Created {issue_type_name} issue: {created_key}")
                    
                    return created_key
                else:

                    error_detail = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                    print(f"  Tipo '{issue_type_name}' falló ({response.status_code}): {error_detail}")
                    print(f"  Payload enviado: {json.dumps(payload, indent=2)}")
            
            print(f"✗ No se pudo crear issue para: {feature_name} - {scenario_name}")
        return test_key
        
    def link_to_parent(self, test_key: str, parent_key: str) -> bool:
        """Deprecated: not used anymore. Tests are created independently."""
        return False

    def link_test_to_execution(self, execution_key: str, test_key: str) -> bool:
        """Link a Test to a Test Execution issue (proper Xray link)"""
        try:
            url = f"{self.settings.jira_base_url}/rest/api/3/issue/{test_key}/link"
            payload = {
                "outwardIssue": {"key": execution_key},
                "type": {"name": "is executed by"}
            }
            response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
            if response.status_code == 201:
                print(f"✓ Test {test_key} linked to Execution {execution_key}")
                return True
            else:
                print(f"⚠️ Failed to link {test_key} to {execution_key}: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error linking test to execution: {e}")
            return False

    def link_test_execution_to_parent(self, execution_key: str, parent_key: str) -> bool:
        """Link Test Execution to parent issue (US/Story)"""
        try:
            url = f"{self.settings.jira_base_url}/rest/api/3/issue/{parent_key}/link"
            
            # Try: PARENT "is tested by" EXECUTION
            payload = {
                "inwardIssue": {"key": execution_key},
                "type": {"name": "is tested by"}
            }
            response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
            
            if response.status_code == 201:
                print(f"✓ {parent_key} is tested by {execution_key}")
                return True
            elif response.status_code == 404:
                print(f"⚠️ Parent issue {parent_key} not found. Skipping link.")
                return False
            else:
                # Fallback to "relates to"
                payload = {
                    "outwardIssue": {"key": parent_key},
                    "type": {"name": "relates to"}
                }
                response = requests.post(
                    f"{self.settings.jira_base_url}/rest/api/3/issue/{execution_key}/link",
                    headers=self.headers,
                    auth=self.auth,
                    json=payload
                )
                if response.status_code == 201:
                    print(f"✓ {execution_key} relates to {parent_key}")
                    return True
                else:
                    print(f"⚠️ Could not link {execution_key} to {parent_key}")
                    return False
        except Exception as e:
            print(f"❌ Error linking execution to parent: {e}")
            return False

    def link_issues(self, source_key: str, target_key: str, link_name: str = "Relates") -> bool:
        """Generic link between two issues"""
        # Note: Xray uses normal issue links for Test Executions -> Tests in simple mode
        return self.link_to_parent(target_key, source_key)

    def add_comment(self, issue_key: str, comment_body: str) -> bool:
        url = f"{self.settings.jira_base_url}/rest/api/3/issue/{issue_key}/comment"
        payload = {
            "body": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment_body}]
                    }
                ]
            }
        }
        try:
             response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
             return response.status_code == 201
        except:
             return False

    def transition_issue(self, issue_key: str, target_status_name: str) -> bool:
        """Transition an issue to a new status (e.g. Done)"""
        # 1. Get available transitions
        url = f"{self.settings.jira_base_url}/rest/api/3/issue/{issue_key}/transitions"
        try:
            response = requests.get(url, headers=self.headers, auth=self.auth)
            if response.status_code != 200:
                print(f"⚠️ Could not fetch transitions for {issue_key}")
                return False
            
            transitions = response.json().get('transitions', [])
            target_transition_id = None
            
            for t in transitions:
                if t['name'].lower() == target_status_name.lower():
                    target_transition_id = t['id']
                    break
            
            if not target_transition_id:
                print(f"⚠️ Transition '{target_status_name}' not found for {issue_key}. Available: {[t['name'] for t in transitions]}")
                return False
            
            # 2. Perform transition
            post_payload = {"transition": {"id": target_transition_id}}
            post_response = requests.post(url, headers=self.headers, auth=self.auth, json=post_payload)
            
            if post_response.status_code == 204:
                print(f"✅ Issue {issue_key} moved to '{target_status_name}'")
                return True
            else:
                print(f"❌ Failed to transition {issue_key}: {post_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error transitioning issue: {e}")
            return False

    def create_test_plan(self, summary: str = "Automated Test Plan") -> Optional[str]:
        """Create a Test Plan container in Xray"""
        from datetime import datetime
        
        url = f"{self.settings.jira_base_url}/rest/api/3/issue"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Test Plan names to try
        plan_types = ["test-plan", "Test Plan", "Plan de Pruebas", "Epic"]
        issue_type_id = None
        used_type = None
        
        for pt in plan_types:
            issue_type_id = self.get_issue_type_id(pt)
            if issue_type_id:
                used_type = pt
                print(f"Using issue type for Test Plan: {pt} ({issue_type_id})")
                break
        
        if not issue_type_id:
            print("⚠️ Could not find suitable issue type for Test Plan.")
            return None
        
        payload = {
            "fields": {
                "project": {"key": self.settings.xray_project_key},
                "summary": f"{summary} - {timestamp}",
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
                                    "text": "Test Plan for automated Karate test execution",
                                    "marks": [{"type": "strong"}]
                                }
                            ]
                        }
                    ]
                },
                "labels": ["test-plan", "automated", "karate"]
            }
        }
        
        # Add fields for test-plan type if it's the X-Ray specific type
        if used_type and used_type.lower() == "test-plan":
            payload["fields"]["assignee"] = {"name": self.settings.jira_email.split("@")[0]}
        
        response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
        if response.status_code == 201:
            plan_key = response.json()["key"]
            print(f"✓ Created Test Plan: {plan_key}")
            return plan_key
        else:
            error_msg = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            print(f"✗ Failed to create Test Plan ({used_type}): {response.status_code}")
            print(f"  Error: {error_msg}")
            print(f"  Payload: {json.dumps(payload, indent=2)}")
            
            # Fallback: Try with Epic if test-plan failed
            if used_type and used_type.lower() == "test-plan":
                print(f"  Falling back to Epic...")
                return self._create_epic_as_test_plan(summary)
            return None
    
    def _create_epic_as_test_plan(self, summary: str) -> Optional[str]:
        """Fallback: Create an Epic to use as Test Plan"""
        from datetime import datetime
        
        url = f"{self.settings.jira_base_url}/rest/api/3/issue"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        issue_type_id = self.get_issue_type_id("Epic")
        if not issue_type_id:
            print("⚠️ Could not find Epic issue type.")
            return None
        
        payload = {
            "fields": {
                "project": {"key": self.settings.xray_project_key},
                "summary": f"Test Plan (Epic) - {summary} - {timestamp}",
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
                                    "text": "Test Plan container (Epic fallback)"
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
        if response.status_code == 201:
            epic_key = response.json()["key"]
            print(f"✓ Created Epic (Test Plan fallback): {epic_key}")
            return epic_key
        else:
            print(f"✗ Fallback Epic also failed: {response.status_code}")
            return None

    def create_test_execution(self, parent_key: Optional[str] = None, test_plan_key: Optional[str] = None) -> Optional[str]:
        """Create a Test Execution issue in Xray for tracking test runs"""
        from datetime import datetime
        import os
        
        url = f"{self.settings.jira_base_url}/rest/api/3/issue"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        summary = f"Test Execution - {timestamp}"
        if parent_key:
            summary = f"Test Execution for {parent_key} - {timestamp}"
        
        # Intentar encontrar issue type 'Test Execution' o 'Ejecución de Prueba' o 'Task'
        execution_types = ["test-execution", "Test Execution", "Ejecución de Prueba", "Task", "Tarea"]
        issue_type_id = None
        used_type = None
        
        for et in execution_types:
            issue_type_id = self.get_issue_type_id(et)
            if issue_type_id:
                used_type = et
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
                                    "text": "Automated test execution from Karate",
                                    "marks": [{"type": "strong"}]
                                }
                            ]
                        },
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Parent US: {parent_key or 'N/A'}"
                                }
                            ]
                        },
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Test Plan: {test_plan_key or 'N/A'}"
                                }
                            ]
                        }
                    ]
                },
                "labels": ["automated-execution", "karate", "agent-created"]
            }
        }
        
        # Add X-Ray specific fields for test-execution type
        if used_type and used_type.lower() == "test-execution":
            # These are typical X-Ray fields
            payload["fields"]["assignee"] = {"name": self.settings.jira_email.split("@")[0]}
            payload["fields"]["environment"] = "Automated"
            payload["fields"]["revision"] = os.getenv("GITHUB_SHA", "unknown")[:7]
            payload["fields"]["testExecutionType"] = "Automated"
        
        response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
        if response.status_code == 201:
            exec_key = response.json()["key"]
            print(f"✓ Created Test Execution: {exec_key}")
            return exec_key
        else:
            error_msg = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            print(f"✗ Failed to create Test Execution ({used_type}): {response.status_code}")
            print(f"  Error: {error_msg}")
            print(f"  Payload: {json.dumps(payload, indent=2)}")
            
            # Fallback: Try with Task if test-execution failed
            if used_type and used_type.lower() == "test-execution":
                print(f"  Falling back to Task...")
                return self._create_task_as_test_execution(summary, parent_key, test_plan_key)
            return None
    
    def _create_task_as_test_execution(self, summary: str, parent_key: Optional[str], test_plan_key: Optional[str]) -> Optional[str]:
        """Fallback: Create a Task to use as Test Execution"""
        url = f"{self.settings.jira_base_url}/rest/api/3/issue"
        
        issue_type_id = self.get_issue_type_id("Task")
        if not issue_type_id:
            print("⚠️ Could not find Task issue type.")
            return None
        
        payload = {
            "fields": {
                "project": {"key": self.settings.xray_project_key},
                "summary": f"Test Execution (Task) - {summary}",
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
                                    "text": "Test Execution container (Task fallback) from automated Karate tests"
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
        if response.status_code == 201:
            task_key = response.json()["key"]
            print(f"✓ Created Task (Test Execution fallback): {task_key}")
            return task_key
        else:
            print(f"✗ Fallback Task also failed: {response.status_code}")
            return None
    
    def link_test_plan_to_parent(self, test_plan_key: str, parent_key: str) -> bool:
        """Link Test Plan to parent issue (US/Story)"""
        try:
            url = f"{self.settings.jira_base_url}/rest/api/3/issue/{parent_key}/link"
            
            # Try: PARENT "is tested by" TEST PLAN
            payload = {
                "inwardIssue": {"key": test_plan_key},
                "type": {"name": "is tested by"}
            }
            response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
            
            if response.status_code == 201:
                print(f"✓ {parent_key} is tested by {test_plan_key}")
                return True
            elif response.status_code == 404:
                print(f"⚠️ Parent issue {parent_key} not found. Skipping link.")
                return False
            else:
                # Fallback to "relates to"
                payload = {
                    "outwardIssue": {"key": parent_key},
                    "type": {"name": "relates to"}
                }
                response = requests.post(
                    f"{self.settings.jira_base_url}/rest/api/3/issue/{test_plan_key}/link",
                    headers=self.headers,
                    auth=self.auth,
                    json=payload
                )
                if response.status_code == 201:
                    print(f"✓ {test_plan_key} relates to {parent_key}")
                    return True
                else:
                    print(f"⚠️ Could not link {test_plan_key} to {parent_key}")
                    return False
        except Exception as e:
            print(f"❌ Error linking test plan to parent: {e}")
            return False

    def link_execution_to_test_plan(self, execution_key: str, test_plan_key: str) -> bool:
        """Link Test Execution to Test Plan"""
        try:
            url = f"{self.settings.jira_base_url}/rest/api/3/issue/{test_plan_key}/link"
            
            # Test Plan "contains" or "is related to" Test Execution
            payload = {
                "inwardIssue": {"key": execution_key},
                "type": {"name": "contains"}
            }
            response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
            
            if response.status_code == 201:
                print(f"✓ {test_plan_key} contains {execution_key}")
                return True
            elif response.status_code == 404:
                print(f"⚠️ Test Plan {test_plan_key} not found.")
                return False
            else:
                # Fallback to "relates to"
                payload = {
                    "outwardIssue": {"key": test_plan_key},
                    "type": {"name": "relates to"}
                }
                response = requests.post(
                    f"{self.settings.jira_base_url}/rest/api/3/issue/{execution_key}/link",
                    headers=self.headers,
                    auth=self.auth,
                    json=payload
                )
                if response.status_code == 201:
                    print(f"✓ {execution_key} relates to {test_plan_key}")
                    return True
                else:
                    print(f"⚠️ Could not link {execution_key} to {test_plan_key}")
                    return False
        except Exception as e:
            print(f"❌ Error linking execution to test plan: {e}")
            return False