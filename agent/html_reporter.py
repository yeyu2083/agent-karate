#!/usr/bin/env python3
"""
HTML Report Generator for Test Results
Creates professional HTML reports that can be downloaded and viewed in browser
"""

from typing import List
from .state import TestResult
from datetime import datetime


def generate_html_report(results: List[TestResult], run_id: int = None, build_number: str = "unknown") -> str:
    """Generate a professional HTML report from test results"""
    
    total = len(results)
    passed = sum(1 for r in results if r.status == "passed")
    failed = sum(1 for r in results if r.status == "failed")
    pass_rate = (passed / total * 100) if total > 0 else 0
    total_duration = sum(r.duration for r in results)
    
    # Determine status color
    if pass_rate == 100:
        status_color = "#4CAF50"
        status_text = "PASS"
        status_icon = "✓"
    elif pass_rate >= 90:
        status_color = "#FF9800"
        status_text = "WARNING"
        status_icon = "⚠"
    else:
        status_color = "#F44336"
        status_text = "FAILED"
        status_icon = "✕"
    
    # Build results rows
    results_rows = ""
    for i, result in enumerate(results, 1):
        status_badge = "PASSED" if result.status == "passed" else "FAILED"
        status_color_row = "#4CAF50" if result.status == "passed" else "#F44336"
        
        results_rows += f"""
        <tr>
            <td>{i}</td>
            <td><strong>{result.feature}</strong></td>
            <td>{result.scenario}</td>
            <td><span style="background-color: {status_color_row}; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;">{status_badge}</span></td>
            <td>{result.duration:.2f}s</td>
            <td>{result.error_message[:50] + "..." if result.error_message and len(result.error_message) > 50 else result.error_message or "N/A"}</td>
        </tr>
        """
    
    # Build failed tests section
    failed_section = ""
    if failed > 0:
        failed_section = "<h3 style=\"color: #F44336; margin-top: 30px;\">Failed Tests Details</h3>"
        for result in results:
            if result.status == "failed":
                failed_section += f"""
        <div style="background-color: #ffebee; border-left: 4px solid #F44336; padding: 15px; margin-bottom: 10px; border-radius: 4px;">
            <h4 style="margin: 0 0 10px 0; color: #F44336;">{result.feature}</h4>
            <p><strong>Scenario:</strong> {result.scenario}</p>
            <p><strong>Duration:</strong> {result.duration:.2f}s</p>
            <p><strong>Error:</strong></p>
            <pre style="background-color: #fff3e0; padding: 10px; border-radius: 3px; overflow-x: auto;">{result.error_message or "No error details"}</pre>
        </div>
        """
    
    # Current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - {build_number}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .status-badge {{
            display: inline-block;
            background-color: {status_color};
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 1.2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px 20px;
            background-color: #f9f9f9;
        }}
        
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        
        .metric-card h3 {{
            color: #999;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        
        .metric-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        
        .content {{
            padding: 30px 20px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        
        table th {{
            background-color: #f5f5f5;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
            color: #333;
        }}
        
        table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        
        table tr:hover {{
            background-color: #f9f9f9;
        }}
        
        .footer {{
            background-color: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 0.9em;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background-color: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin: 15px 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: {pass_rate}%;
            transition: width 0.3s ease;
        }}
        
        .recommendation {{
            background-color: #e3f2fd;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        
        .recommendation h4 {{
            color: #1976D2;
            margin-bottom: 5px;
        }}
        
        .recommendation p {{
            color: #424242;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Test Execution Report</h1>
            <p>Build #{build_number} - Karate API Testing</p>
            <div class="status-badge">{status_icon} {status_text}</div>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <h3>Pass Rate</h3>
                <div class="value">{pass_rate:.1f}%</div>
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
            </div>
            <div class="metric-card">
                <h3>Total Tests</h3>
                <div class="value">{total}</div>
            </div>
            <div class="metric-card">
                <h3>Passed</h3>
                <div class="value" style="color: #4CAF50;">{passed}</div>
            </div>
            <div class="metric-card">
                <h3>Failed</h3>
                <div class="value" style="color: #F44336;">{failed}</div>
            </div>
            <div class="metric-card">
                <h3>Total Duration</h3>
                <div class="value">{total_duration:.2f}s</div>
            </div>
            <div class="metric-card">
                <h3>Timestamp</h3>
                <div class="value" style="font-size: 0.9em; margin-top: 5px;">{timestamp}</div>
            </div>
        </div>
        
        <div class="content">
            <h2 style="color: #333; margin-bottom: 20px;">Test Results</h2>
            
            <table>
                <thead>
                    <tr>
                        <th style="width: 5%">#</th>
                        <th style="width: 25%">Feature</th>
                        <th style="width: 25%">Scenario</th>
                        <th style="width: 15%">Status</th>
                        <th style="width: 10%">Duration</th>
                        <th style="width: 20%">Error</th>
                    </tr>
                </thead>
                <tbody>
                    {results_rows}
                </tbody>
            </table>
            
            {failed_section}
            
            <div class="recommendation">
                <h4>Recommendation</h4>
                <p>
                    {'✓ All tests passed! The build is ready for deployment.' if pass_rate == 100 else
                     '⚠ Review the failed tests before merging to main.' if pass_rate >= 90 else
                     '✕ Critical failures detected. Do not merge until resolved.'}
                </p>
            </div>
            
            {f'<p><strong>Run ID:</strong> {run_id}</p>' if run_id else ''}
        </div>
        
        <div class="footer">
            <p>Generated by TestRail Automation Agent | {timestamp}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html
