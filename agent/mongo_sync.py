#!/usr/bin/env python3
"""
MongoDB Sync Module
Persist test execution data, AI feedback, and historical trends to MongoDB
"""

import os
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
import json

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    import certifi
except ImportError:
    MongoClient = None

from .state import TestResult
from .mongo_schema import (
    TestResultDocument,
    ExecutionSummaryDocument,
    StatusEnum,
    RiskLevelEnum,
)


class MongoSync:
    """💾 MongoDB Integration for Historical Data & Analytics"""

    def __init__(self, mongo_uri: Optional[str] = None):
        """
        Initialize MongoDB connection
        
        Args:
            mongo_uri: Connection string. If None, tries env vars or config
        """
        if MongoClient is None:
            print("⚠️  pymongo not installed. Install: pip install pymongo")
            self.enabled = False
            return

        # Determinar URI
        if not mongo_uri:
            mongo_uri = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")
            if not mongo_uri:
                # Intentar leer de config
                try:
                    config_path = os.path.join(
                        os.path.dirname(os.path.dirname(__file__)), "testrail.config.json"
                    )
                    if os.path.exists(config_path):
                        with open(config_path, "r", encoding="utf-8") as f:
                            config = json.load(f)
                            mongo_uri = config.get("mongodb", {}).get("uri")
                except Exception as e:
                    print(f"⚠️ Could not read MongoDB URI from config: {e}")

        if not mongo_uri:
            print("⚠️ MongoDB: No URI provided. Skipping MongoDB sync.")
            print("   Set MONGO_URI env var or add 'mongodb.uri' to testrail.config.json")
            self.enabled = False
            return

        try:
            # Conectar con timeout y certificados SSL
            self.client = MongoClient(
                mongo_uri, 
                serverSelectionTimeoutMS=5000,
                tlsCAFile=certifi.where()
            )
            self.client.admin.command("ping")  # Test connection
            
            self.db = self.client.get_database()
            self.enabled = True
            print(f"✅ MongoDB: Conectado exitosamente a '{self.db.name}'")
            print(f"   URI: {mongo_uri.split('@')[1] if '@' in mongo_uri else 'local'}")
            
            # Listar collections existentes
            existing_collections = self.db.list_collection_names()
            if existing_collections:
                print(f"   Collections: {', '.join(existing_collections)}")
            else:
                print(f"   (Base de datos vacía - se crearán al guardar)")
                
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ MongoDB: Conexión fallida")
            print(f"   Error: {e}")
            print(f"   Verifica:")
            print(f"   • Contraseña correcta en MONGO_URI")
            print(f"   • IP whitelisted en MongoDB Atlas (Security → Network Access)")
            print(f"   • Cluster está activo")
            self.enabled = False
        except Exception as e:
            print(f"⚠️ MongoDB initialization error: {e}")
            self.enabled = False

    def save_test_result(
        self,
        result: TestResult,
        execution_id: str,
        commit_sha: str,
        branch: str = "main",
        pr_number: Optional[int] = None,
        github_actor: Optional[str] = None,
        testrail_case_id: Optional[int] = None,
        ai_analysis: Optional[dict] = None,
    ) -> bool:
        """
        💾 Save individual test result to MongoDB
        
        Args:
            result: TestResult from Karate
            execution_id: Batch ID for this run
            commit_sha: Git commit SHA
            branch: Git branch name
            pr_number: GitHub PR number if applicable
            github_actor: GitHub username
            testrail_case_id: TestRail case ID if synced
            ai_analysis: AI feedback dict with keys: risk_level, root_cause, user_impact, action
        """
        if not self.enabled:
            return False

        try:
            test_id = f"{result.feature}.{result.scenario}"
            
            # Build base document
            doc = {
                "test_id": test_id,
                "execution_id": execution_id,
                "run_date": datetime.utcnow(),
                "branch": branch,
                "pr_number": pr_number,
                "commit_sha": commit_sha,
                "github_actor": github_actor,
                "feature": result.feature,
                "scenario": result.scenario,
                "tags": result.tags,
                "status": result.status,
                "duration_ms": result.duration * 1000,
                "error_message": result.error_message,
                "gherkin_steps": result.gherkin_steps,
                "background_steps": result.background_steps,
                "prerequisites": result.prerequisites,
                "expected_assertions": result.expected_assertions,
                "testrail_case_id": testrail_case_id,
            }

            # Add AI analysis if provided
            if ai_analysis:
                doc.update({
                    "ai_risk_level": ai_analysis.get("risk_level"),
                    "ai_root_cause": ai_analysis.get("root_cause"),
                    "ai_user_impact": ai_analysis.get("user_impact"),
                    "ai_recommended_action": ai_analysis.get("action"),
                })

            # Insert or update
            collection = self.db["test_results"]
            result_obj = collection.update_one(
                {"test_id": test_id, "execution_id": execution_id},
                {"$set": doc},
                upsert=True,
            )

            status = "inserted" if result_obj.upserted_id else "updated"
            print(f"  💾 MongoDB: {test_id} ({status})")
            return True

        except Exception as e:
            print(f"⚠️ MongoDB save_test_result failed: {e}")
            return False

    def save_execution_summary(
        self,
        execution_id: str,
        branch: str,
        commit_sha: str,
        results: List[TestResult],
        pr_number: Optional[int] = None,
        github_actor: Optional[str] = None,
        testrail_run_id: Optional[int] = None,
        ai_summary: Optional[dict] = None,
    ) -> bool:
        """
        📈 Save execution summary aggregating all test results
        
        Args:
            execution_id: Batch ID
            branch: Git branch
            commit_sha: Git commit
            results: List of TestResult
            pr_number: PR number
            github_actor: GitHub username
            testrail_run_id: TestRail run ID
            ai_summary: Dict with: pr_comment, technical_summary, blockers, recommendations
        """
        if not self.enabled or not results:
            return False

        try:
            passed = sum(1 for r in results if r.status == "passed")
            failed = sum(1 for r in results if r.status == "failed")
            skipped = sum(1 for r in results if r.status == "skipped")
            total = len(results)
            total_duration = sum(r.duration for r in results) * 1000

            # Determine risk level
            pass_rate = (passed / total * 100) if total > 0 else 0
            if pass_rate == 100:
                risk_level = "LOW"
            elif pass_rate >= 90:
                risk_level = "MEDIUM"
            else:
                risk_level = "CRITICAL"

            # Build summary doc
            doc = {
                "execution_batch_id": execution_id,
                "run_date": datetime.utcnow(),
                "branch": branch,
                "pr_number": pr_number,
                "commit_sha": commit_sha,
                "github_actor": github_actor,
                "total_tests": total,
                "passed_tests": passed,
                "failed_tests": failed,
                "skipped_tests": skipped,
                "overall_pass_rate": pass_rate,
                "total_duration_ms": total_duration,
                "overall_risk_level": risk_level,
                "failed_features": list(set(r.feature for r in results if r.status == "failed")),
                "testrail_run_id": testrail_run_id,
                "test_result_ids": [f"{r.feature}.{r.scenario}" for r in results],
            }

            # Add AI summary if provided
            if ai_summary:
                doc.update({
                    "ai_pr_comment": ai_summary.get("pr_comment"),
                    "ai_technical_summary": ai_summary.get("technical_summary"),
                    "ai_blockers": ai_summary.get("blockers", []),
                    "ai_recommendations": ai_summary.get("recommendations", []),
                })

            # Insert
            collection = self.db["execution_summaries"]
            result_obj = collection.insert_one(doc)
            print(f"  📈 MongoDB: Execution summary {execution_id} saved")
            return True

        except Exception as e:
            print(f"⚠️ MongoDB save_execution_summary failed: {e}")
            return False

    def get_test_history(self, feature: str, scenario: str, limit: int = 10) -> List[dict]:
        """
        📊 Retrieve execution history for a specific test
        
        Args:
            feature: Feature name
            scenario: Scenario name
            limit: Number of recent executions to return
        """
        if not self.enabled:
            return []

        try:
            collection = self.db["test_results"]
            test_id = f"{feature}.{scenario}"
            results = list(
                collection.find({"test_id": test_id})
                .sort("run_date", -1)
                .limit(limit)
            )
            return results
        except Exception as e:
            print(f"⚠️ MongoDB get_test_history failed: {e}")
            return []

    def get_flaky_tests(self, min_flakiness: float = 0.3) -> List[dict]:
        """
        🔴 Identify flaky tests (inconsistent pass/fail)
        
        Args:
            min_flakiness: Threshold (0.3 = 30% failure rate qualifies as flaky)
        """
        if not self.enabled:
            return []

        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$test_id",
                        "total": {"$sum": 1},
                        "failed": {
                            "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                        },
                    }
                },
                {
                    "$project": {
                        "test_id": "$_id",
                        "flakiness": {"$divide": ["$failed", "$total"]},
                        "failure_count": "$failed",
                        "total_runs": "$total",
                    }
                },
                {"$match": {"flakiness": {"$gte": min_flakiness}}},
                {"$sort": {"flakiness": -1}},
            ]

            collection = self.db["test_results"]
            results = list(collection.aggregate(pipeline))
            return results
        except Exception as e:
            print(f"⚠️ MongoDB get_flaky_tests failed: {e}")
            return []

    def get_branch_stats(self, branch: str, days: int = 7) -> dict:
        """
        📊 Get aggregated stats for a branch (last N days)
        
        Args:
            branch: Git branch name
            days: Number of days to look back
        """
        if not self.enabled:
            return {}

        try:
            from datetime import timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {
                    "$match": {
                        "branch": branch,
                        "run_date": {"$gte": start_date},
                    }
                },
                {
                    "$group": {
                        "_id": "$branch",
                        "total_tests": {"$sum": 1},
                        "passed": {
                            "$sum": {"$cond": [{"$eq": ["$status", "passed"]}, 1, 0]}
                        },
                        "failed": {
                            "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                        },
                        "avg_duration_ms": {"$avg": "$duration_ms"},
                    }
                },
            ]

            collection = self.db["test_results"]
            results = list(collection.aggregate(pipeline))
            
            if results:
                stats = results[0]
                stats["pass_rate"] = (
                    (stats["passed"] / stats["total_tests"] * 100)
                    if stats["total_tests"] > 0
                    else 0
                )
                return stats
            
            return {}
        except Exception as e:
            print(f"⚠️ MongoDB get_branch_stats failed: {e}")
            return {}

    def close(self):
        """Close MongoDB connection"""
        if self.enabled and hasattr(self, "client"):
            self.client.close()
            print("✓ MongoDB connection closed")
