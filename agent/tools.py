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
    llm_provider: str = "openai"
    
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: Optional[str] = None
    azure_openai_deployment_name: Optional[str] = None
    
    anthropic_api_key: Optional[str] = None
    anthropic_model: Optional[str] = None
    
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

    def search_test_issue(self, test_name: str) -> Optional[str]:
        url = f"{self.settings.jira_base_url}/rest/api/3/search"
        query = f"project={self.settings.xray_project_key} AND summary ~ '{test_name}' AND issuetype = Test"
        params = {
            "jql": query,
            "fields": "key,summary"
        }
        response = requests.get(url, headers=self.headers, auth=self.auth, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("issues"):
                return data["issues"][0]["key"]
        return None

    def import_execution_to_xray(self, payload: dict) -> Dict[str, Any]:
        url = f"{self.settings.jira_base_url}/rest/raven/2.0/import/execution"
        response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
        return response.json() if response.status_code == 200 else {"error": response.text}

    def get_or_create_test_issue(self, feature_name: str, scenario_name: str) -> Optional[str]:
        test_key = self.search_test_issue(f"{feature_name} - {scenario_name}")
        if not test_key:
            url = f"{self.settings.jira_base_url}/rest/api/3/issue"
            payload = {
                "fields": {
                    "project": {"key": self.settings.xray_project_key},
                    "summary": f"{feature_name} - {scenario_name}",
                    "issuetype": {"name": "Test"},
                    "description": f"Automated test from Karate feature: {feature_name}"
                }
            }
            response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
            if response.status_code == 201:
                return response.json()["key"]
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