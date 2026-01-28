import json
import os
from typing import List, Dict, Any, Optional
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
            
            # Estructura 1: scenarioResults (nuevo formato detallado)
            if isinstance(data, dict) and 'scenarioResults' in data:
                print("✓ Detected detailed format with scenarioResults")
                scenario_results = data.get('scenarioResults', [])
                feature_name = data.get('name', 'Unknown Feature')
                
                if isinstance(scenario_results, list):
                    for scenario in scenario_results:
                        result = KarateParser._parse_scenario_result(scenario, feature_name)
                        if result:
                            results.append(result)
                    
                    if results:
                        print(f"✓ Successfully parsed {len(results)} test results from scenarioResults")
                        return results
            
            # Estructura 2: elementos (formato antiguo)
            features = []
            if isinstance(data, list):
                features = data
            elif isinstance(data, dict):
                if 'elements' in data:
                    features = [data]
                elif 'features' in data:
                    features = data.get('features', [])
            
            if features:
                print(f"Found {len(features)} feature(s) in Karate JSON")
                for feature in features:
                    results.extend(KarateParser._parse_feature_data(feature, ""))
                
                if results:
                    print(f"✓ Successfully parsed {len(results)} test results from features")
                    return results
            
            # Fallback a resumen si no hay nada más
            if isinstance(data, dict) and 'featureSummary' in data:
                print("Detected Karate summary format (fallback)")
                feature_summary = data.get('featureSummary', [])
                print(f"Feature summary has {len(feature_summary)} features")
                
                for feature_item in feature_summary:
                    name = feature_item.get('name', 'Unknown')
                    status = 'passed' if not feature_item.get('failed', False) else 'failed'
                    duration = feature_item.get('durationMillis', 0) / 1000.0
                    
                    results.append(TestResult(
                        feature=name,
                        scenario=name,
                        status=status,
                        duration=duration,
                        error_message=None,
                        steps=[],
                        gherkin_steps=[],
                        background_steps=[],
                        expected_assertions=[],
                        examples=[]
                    ))
                
                if results:
                    print(f"✓ Successfully parsed {len(results)} test results from feature summary")
                    return results
            
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
    def _parse_scenario_result(scenario: Dict, feature_name: str) -> Optional[TestResult]:
        """Parse individual scenario from scenarioResults"""
        try:
            scenario_name = scenario.get('name', 'Unknown Scenario')
            
            # Status viene del campo 'failed' (booleano)
            # failed=true → status='failed', failed=false → status='passed'
            is_failed = scenario.get('failed', False)
            status = 'failed' if is_failed else 'passed'
            
            duration_ms = scenario.get('durationMillis', 0)
            duration = duration_ms / 1000.0
            
            error_message = None
            steps_data = scenario.get('stepResults', [])
            
            # Extraer error si existe
            if is_failed:
                error_message = scenario.get('error', 'Test failed')
            
            # Extraer pasos del Gherkin
            gherkin_steps = KarateParser._extract_gherkin_steps_from_result(scenario)
            background_steps = []  # No disponible en este formato
            expected_assertions = KarateParser._extract_expected_assertions_from_result(scenario)
            examples = []
            
            return TestResult(
                feature=feature_name,
                scenario=scenario_name,
                status=status,
                duration=duration,
                error_message=error_message,
                steps=steps_data,
                gherkin_steps=gherkin_steps,
                background_steps=background_steps,
                expected_assertions=expected_assertions,
                examples=examples
            )
        except Exception as e:
            print(f"⚠️ Error parsing scenario: {e}")
            return None
    
    @staticmethod
    def _extract_gherkin_steps_from_result(scenario: Dict) -> List[str]:
        """Extraer pasos del scenario result"""
        steps = []
        try:
            step_results = scenario.get('stepResults', [])
            for step_result in step_results:
                if isinstance(step_result, dict):
                    step = step_result.get('step', {})
                    if isinstance(step, dict):
                        prefix = step.get('prefix', '').strip()  # Given, When, Then, And, *
                        text = step.get('text', '').strip()
                        
                        # Mapear prefijos de Karate a Gherkin
                        if prefix == '*':
                            prefix = 'Given'  # O And, pero usamos Given como default
                        
                        if prefix and text:
                            steps.append(f"{prefix} {text}")
        except Exception:
            pass
        return steps
    
    @staticmethod
    def _extract_expected_assertions_from_result(scenario: Dict) -> List[str]:
        """Extraer aserciones de los pasos"""
        assertions = []
        try:
            step_results = scenario.get('stepResults', [])
            for step_result in step_results:
                if isinstance(step_result, dict):
                    step = step_result.get('step', {})
                    if isinstance(step, dict):
                        prefix = step.get('prefix', '').strip()
                        text = step.get('text', '').strip()
                        
                        # Capturar Then y And como aserciones
                        if any(kw in prefix for kw in ['Then', 'And', '*']) and text:
                            if any(x in text for x in ['status', 'match', '==']):
                                assertions.append(f"{prefix} {text}")
        except Exception:
            pass
        return assertions
    
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
                        
                        # Extraer DocStrings (ej. payloads JSON, XML)
                        doc_string_data = None
                        if 'doc_string' in step:
                             doc_s = step['doc_string']
                             if isinstance(doc_s, dict):
                                 doc_string_data = doc_s.get('value')
                        
                        step_info = {
                            "keyword": step.get('keyword', ''),
                            "text": step.get('name', ''),
                            "status": result.get('status', 'unknown'),
                            "duration_ms": result.get('duration', 0) / 1e6, # nanoseconds to milliseconds
                            "error": result.get('error_message', None),
                            "data": doc_string_data
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
            
            # Extraer pasos del Gherkin si disponible
            gherkin_steps = KarateParser._extract_gherkin_steps(feature, scenario)
            background_steps = KarateParser._extract_background_steps(feature)
            expected_assertions = KarateParser._extract_expected_assertions(scenario)
            examples = KarateParser._extract_examples(feature, scenario)
            
            results.append(TestResult(
                feature=feature_name,
                scenario=scenario_name,
                status=status,
                duration=duration,
                error_message=error_message,
                steps=steps_data,
                gherkin_steps=gherkin_steps,
                background_steps=background_steps,
                expected_assertions=expected_assertions,
                examples=examples
            ))
        
        return results
    
    @staticmethod
    def _extract_gherkin_steps(feature: Dict, scenario: Dict) -> List[str]:
        """Extraer pasos del JSON del Gherkin (Given, When, Then)"""
        steps = []
        try:
            scenario_steps = scenario.get('steps', [])
            for step in scenario_steps:
                if isinstance(step, dict):
                    keyword = step.get('keyword', '').strip()  # Given, When, Then, And
                    text = step.get('text', '').strip()
                    if keyword and text:
                        steps.append(f"{keyword} {text}")
        except Exception as e:
            pass
        return steps
    
    @staticmethod
    def _extract_background_steps(feature: Dict) -> List[str]:
        """Extraer pasos del Background de la feature"""
        steps = []
        try:
            background = feature.get('background')
            if background and isinstance(background, dict):
                background_steps = background.get('steps', [])
                for step in background_steps:
                    if isinstance(step, dict):
                        keyword = step.get('keyword', '').strip()  # Given, And, etc
                        text = step.get('text', '').strip()
                        if keyword and text:
                            steps.append(f"{keyword} {text}")
        except Exception as e:
            pass
        return steps
    
    @staticmethod
    def _extract_expected_assertions(scenario: Dict) -> List[str]:
        """Extraer match statements (Then/And match) como aserciones esperadas"""
        assertions = []
        try:
            scenario_steps = scenario.get('steps', [])
            for step in scenario_steps:
                if isinstance(step, dict):
                    keyword = step.get('keyword', '').strip()
                    text = step.get('text', '').strip()
                    
                    # Capturar: Then status, Then/And match, Then/And anything
                    if any(kw in keyword for kw in ['Then', 'And']) and text:
                        # Incluir status, match, y otras aserciones
                        if any(x in text for x in ['status', 'match', '==']):
                            assertions.append(f"{keyword} {text}")
        except Exception as e:
            pass
        return assertions
    
    @staticmethod
    def _extract_examples(feature: Dict, scenario: Dict) -> List[dict]:
        """Extraer datos de Examples si es Scenario Outline"""
        examples = []
        try:
            # Buscar en scenario.examples si existe (Scenario Outline)
            scenario_examples = scenario.get('examples', [])
            for example_block in scenario_examples:
                if isinstance(example_block, dict):
                    rows = example_block.get('rows', [])
                    for row in rows:
                        if isinstance(row, dict):
                            cells = row.get('cells', [])
                            examples.append(cells)
        except Exception as e:
            pass
        return examples
