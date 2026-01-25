import json
import os
from typing import List, Dict, Any
from .state import TestResult


class KarateParser:
    @staticmethod
    def parse_karate_json(file_path: str) -> List[TestResult]:
        results: List[TestResult] = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                print(f"No data found in Karate JSON file: {file_path}")
                return results
            
            # Si es un resumen (tiene keys como 'efficiency', 'totalTime', etc.)
            if isinstance(data, dict) and 'featureSummary' in data:
                print("Detected Karate summary format")
                feature_summary = data.get('featureSummary', [])
                print(f"Feature summary has {len(feature_summary)} features")
                
                for feature_item in feature_summary:
                    if isinstance(feature_item, dict):
                        feature_name = feature_item.get('name', 'Unknown Feature')
                        passed_count = feature_item.get('passedCount', 0)
                        failed_count = feature_item.get('failedCount', 0)
                        scenario_count = feature_item.get('scenarioCount', 0)
                        duration = feature_item.get('durationMillis', 0) / 1000  # convertir a segundos
                        is_failed = feature_item.get('failed', False)
                        
                        print(f"Processing feature: {feature_name}")
                        print(f"  Passed: {passed_count}, Failed: {failed_count}, Total: {scenario_count}")
                        
                        # Si hay fallos, marcar feature como failed
                        if failed_count > 0:
                            status = 'failed'
                            error_msg = f"Failed scenarios: {failed_count}"
                        else:
                            status = 'passed'
                            error_msg = None
                        
                        # Crear un test result por feature (no por scenario)
                        results.append(TestResult(
                            feature=feature_name,
                            scenario=f"{passed_count}/{scenario_count} scenarios passed",
                            status=status,
                            duration=duration,
                            error_message=error_msg
                        ))
                
                if results:
                    print(f"Successfully parsed {len(results)} test results from feature summary")
                    return results
            
            # Si no es un resumen, intentar parsing normal
            features = []
            if isinstance(data, list):
                features = data
            elif isinstance(data, dict):
                if 'elements' in data:
                    features = [data]
                elif 'features' in data:
                    features = data.get('features', [])
                else:
                    print(f"Unexpected JSON structure. Keys: {list(data.keys())}")
                    return results
            
            print(f"Found {len(features)} feature(s) in Karate JSON")
            
            for feature in features:
                results.extend(KarateParser._parse_feature_data(feature, ""))
            
            print(f"Successfully parsed {len(results)} test results")
            
        except FileNotFoundError:
            print(f"Karate JSON file not found: {file_path}")
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in Karate file: {e}")
        except Exception as e:
            print(f"Error parsing Karate JSON: {e}")
            import traceback
            traceback.print_exc()
        
        return results

    @staticmethod
    def _parse_feature_data(feature: Dict, source: str = "") -> List[TestResult]:
        results: List[TestResult] = []
        
        if not isinstance(feature, dict):
            return results
        
        feature_name = feature.get('name', 'Unknown Feature')
        elements = feature.get('elements', [])
        
        if not isinstance(elements, list):
            print(f"Elements for feature '{feature_name}' is not a list: {type(elements)}")
            elements = []
        
        for scenario in elements:
            if not isinstance(scenario, dict):
                continue
            
            scenario_type = scenario.get('type')
            if scenario_type not in ['scenario', 'Scenario']:
                continue
            
            scenario_name = scenario.get('name', 'Unknown Scenario')
            scenario_status = scenario.get('status')
            
            if not scenario_status:
                steps = scenario.get('steps', [])
                if isinstance(steps, list):
                    passed_steps = sum(1 for s in steps if isinstance(s, dict) and s.get('result', {}).get('status') == 'passed')
                    failed_steps = sum(1 for s in steps if isinstance(s, dict) and s.get('result', {}).get('status') == 'failed')
                    scenario_status = 'passed' if failed_steps == 0 else 'failed'
                else:
                    scenario_status = 'unknown'
            
            status = 'passed' if scenario_status == 'passed' else 'failed'
            
            steps_data = [] # Data completa de pasos para Jira
            if isinstance(steps, list):
                duration = sum(
                    step.get('result', {}).get('duration', 0) 
                    for step in steps 
                    if isinstance(step, dict) and 'result' in step
                ) / 1e9
                
                # Extraer info detallada de pasos
                for step in steps:
                    if isinstance(step, dict):
                        result = step.get('result', {})
                        step_info = {
                            "keyword": step.get('keyword', ''),
                            "text": step.get('name', ''),
                            "status": result.get('status', 'unknown'),
                            "duration_ms": result.get('duration', 0) / 1e6, # nanoseconds to milliseconds
                            "error": result.get('error_message', None)
                        }
                        steps_data.append(step_info)
            else:
                duration = 0.0
            
            error_message = None
            if status == 'failed':
                if isinstance(steps, list):
                    for step in steps:
                        if isinstance(step, dict):
                            result = step.get('result', {})
                            if result.get('status') == 'failed':
                                error_message = result.get('error_message', 'Unknown error')
                                break
            
            results.append(TestResult(
                feature=feature_name,
                scenario=scenario_name,
                status=status,
                duration=duration,
                error_message=error_message,
                steps=steps_data
            ))
        
        return results
