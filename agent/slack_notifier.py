#!/usr/bin/env python3
"""
Slack Notification Module
Sends test execution results to Slack channel
"""

import os
import requests
import json
from typing import Optional, List, Dict, Any
from datetime import datetime


class SlackNotifier:
    """📢 Slack Integration for Test Results"""

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack notifier
        
        Args:
            webhook_url: Slack webhook URL. If None, tries env vars or config
        """
        if not webhook_url:
            webhook_url = os.getenv("SLACK_WEBHOOK_URL") or os.getenv("SLACK_INCOMING_WEBHOOK")
            
            # Try config file
            if not webhook_url:
                try:
                    config_path = os.path.join(
                        os.path.dirname(os.path.dirname(__file__)), "..", "testrail.config.json"
                    )
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            webhook_url = config.get("slack", {}).get("webhook_url")
                except Exception as e:
                    print(f"⚠️ Could not read Slack webhook from config: {e}")
        
        if not webhook_url:
            print("⚠️ Slack: No webhook URL provided. Skipping Slack notifications.")
            print("   Set SLACK_WEBHOOK_URL env var or add 'slack.webhook_url' to testrail.config.json")
            self.enabled = False
            return
        
        self.webhook_url = webhook_url
        self.enabled = True
        print(f"✓ Slack notifier initialized")

    def send_results(
        self,
        pass_rate: float,
        total_tests: int,
        passed_tests: int,
        failed_tests: int,
        skipped_tests: int,
        duration_ms: float,
        risk_level: str,
        branch: str = "main",
        testrail_run_id: Optional[int] = None,
        github_actor: Optional[str] = None,
        commit_sha: Optional[str] = None,
        pr_number: Optional[int] = None,
        ai_comment: Optional[str] = None,
        ai_blockers: Optional[List[str]] = None,
        ai_recommendations: Optional[List[str]] = None,
    ) -> bool:
        """
        Send test results to Slack
        
        Args:
            pass_rate: Pass rate percentage
            total_tests: Total number of tests
            passed_tests: Number of passed tests
            failed_tests: Number of failed tests
            skipped_tests: Number of skipped tests
            duration_ms: Total duration in milliseconds
            risk_level: LOW, MEDIUM, or CRITICAL
            branch: Git branch name
            testrail_run_id: TestRail run ID
            github_actor: GitHub username who triggered
            commit_sha: Commit SHA
            pr_number: PR number if applicable
            ai_comment: AI feedback comment
            ai_blockers: List of blocking issues
            ai_recommendations: List of recommendations
        """
        if not self.enabled:
            return False

        try:
            # Determine color based on risk level
            color_map = {
                "LOW": "#36a64f",      # Green
                "MEDIUM": "#ff9900",   # Orange
                "CRITICAL": "#ff0000"  # Red
            }
            color = color_map.get(risk_level, "#808080")

            # Determine emoji based on pass rate
            if pass_rate == 100:
                status_emoji = "✅"
            elif pass_rate >= 90:
                status_emoji = "🟡"
            else:
                status_emoji = "🔴"

            # Clean AI text (remove markdown formatting)
            ai_text = (ai_comment or "No analysis").replace("**", "").replace("_", "").replace("`", "")
            # Clean AI text - NO LIMIT on length, Slack will handle it
            ai_text = (ai_comment or "No analysis").replace("**", "").replace("_", "").replace("`", "").strip()

            # Build blockers field - NO CHARACTER LIMIT, show all items
            blockers_list = []
            if ai_blockers and len(ai_blockers) > 0:
                for blocker in ai_blockers:
                    # Remove markdown formatting but keep full text
                    clean_text = blocker.replace("**", "").replace("_", "").replace("`", "").strip()
                    blockers_list.append(clean_text)
            blockers_text = "\n".join([f"• {b}" for b in blockers_list]) if blockers_list else "✓ None detected"

            # Build recommendations field - NO CHARACTER LIMIT, show all items
            recommendations_list = []
            if ai_recommendations and len(ai_recommendations) > 0:
                for rec in ai_recommendations:
                    # Remove markdown formatting but keep full text
                    clean_text = rec.replace("**", "").replace("_", "").replace("`", "").strip()
                    recommendations_list.append(clean_text)
            recommendations_text = "\n".join([f"• {r}" for r in recommendations_list]) if recommendations_list else "None"

            # Build executor info
            executor_text = "Unknown"
            if github_actor and github_actor.lower() != "unknown":
                executor_text = f"@{github_actor}"
            
            # Build commit/PR info
            context_items = [executor_text]
            if pr_number:
                context_items.append(f"PR #{pr_number}")
            if commit_sha:
                context_items.append(commit_sha[:7])
            context_text = " • ".join(context_items)

            # Build Slack message (using Block Kit format - clean and professional)
            payload = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{status_emoji} Karate Test Results",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Pass Rate*\n{pass_rate:.1f}%"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Risk Level*\n{risk_level}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Duration*\n{duration_ms:.0f}ms"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Branch*\n{branch}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"✅ *Passed:* {passed_tests}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"❌ *Failed:* {failed_tests}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"⏭️ *Skipped:* {skipped_tests}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"📊 *Total:* {total_tests}"
                            }
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*🤖 AI Analysis*\n{ai_text}"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*🚨 Blockers*\n{blockers_text}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*💡 Recommendations*\n{recommendations_text}"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"{context_text} • <t:{int(datetime.utcnow().timestamp())}:t>"
                            }
                        ]
                    }
                ],
                "attachments": [
                    {
                        "color": color,
                        "footer": "agent-karate",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }

            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                print(f"✓ Slack notification sent successfully")
                return True
            else:
                print(f"⚠️ Slack notification failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"⚠️ Slack notification error: {e}")
            return False

    def close(self):
        """No resources to close for Slack"""
        pass
