"""
Verification Rules Engine for VERDICT
Mini DSL for defining and evaluating verification rules
"""

import yaml
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Rule:
    """Represents a single verification rule"""
    
    def __init__(self, rule_dict: Dict):
        self.name = rule_dict.get("name", "Unnamed Rule")
        self.type = rule_dict.get("type", "unknown")
        self.condition = rule_dict.get("condition", "true")
        self.action = rule_dict.get("action", "warn")  # reject, warn, log
        self.severity = rule_dict.get("severity", "medium")  # critical, high, medium, low
        self.message = rule_dict.get("message", "Rule failed")
        self.description = rule_dict.get("description", "")
    
    def to_dict(self) -> Dict:
        """Convert rule to dictionary"""
        return {
            "name": self.name,
            "type": self.type,
            "condition": self.condition,
            "action": self.action,
            "severity": self.severity,
            "message": self.message,
            "description": self.description
        }


class RuleEvaluationResult:
    """Result of evaluating a single rule"""
    
    def __init__(self, rule: Rule, passed: bool, error: Optional[str] = None):
        self.rule = rule
        self.passed = passed
        self.error = error
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary"""
        return {
            "rule_name": self.rule.name,
            "type": self.rule.type,
            "passed": self.passed,
            "action": self.rule.action,
            "severity": self.rule.severity,
            "message": self.rule.message if not self.passed else None,
            "error": self.error
        }


class RulesEngine:
    """
    Rules engine that loads and evaluates verification rules
    Implements a mini DSL for rule-based verification
    """
    
    def __init__(self, rules_file: str = "verification_rules.yaml"):
        """
        Initialize the rules engine
        
        Args:
            rules_file: Path to YAML rules configuration file
        """
        self.rules_file = rules_file
        self.rules: List[Rule] = []
        self.load_rules()
    
    def load_rules(self) -> bool:
        """
        Load rules from YAML configuration file
        
        Returns:
            True if rules loaded successfully, False otherwise
        """
        try:
            rules_path = Path(self.rules_file)
            
            if not rules_path.exists():
                logger.warning(f"[RulesEngine] Rules file not found: {self.rules_file}")
                return False
            
            with open(rules_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config or 'rules' not in config:
                logger.error("[RulesEngine] Invalid rules file format - missing 'rules' key")
                return False
            
            # Parse rules
            self.rules = []
            for rule_dict in config['rules']:
                try:
                    rule = Rule(rule_dict)
                    self.rules.append(rule)
                except Exception as e:
                    logger.error(f"[RulesEngine] Error parsing rule: {e}")
                    continue
            
            logger.info(f"[RulesEngine] Loaded {len(self.rules)} verification rules")
            return True
            
        except Exception as e:
            logger.error(f"[RulesEngine] Error loading rules file: {e}")
            return False
    
    def evaluate_rules(self, context: Dict) -> Dict:
        """
        Evaluate all rules against the provided context
        
        Args:
            context: Dictionary containing all data needed for rule evaluation
                    (market_data, sentiment_data, ftso_price, etc.)
        
        Returns:
            Dictionary with evaluation results and overall status
        """
        if not self.rules:
            logger.warning("[RulesEngine] No rules loaded, skipping evaluation")
            return {
                "rules_evaluated": 0,
                "rules_passed": 0,
                "rules_failed": 0,
                "critical_failures": 0,
                "overall_status": "no_rules",
                "should_block": False,
                "results": []
            }
        
        results = []
        passed_count = 0
        failed_count = 0
        critical_failures = 0
        should_block = False
        
        # Evaluate each rule
        for rule in self.rules:
            try:
                result = self._evaluate_rule(rule, context)
                results.append(result.to_dict())
                
                if result.passed:
                    passed_count += 1
                else:
                    failed_count += 1
                    
                    # Check if this failure should block the decision
                    if rule.action == "reject":
                        should_block = True
                        if rule.severity in ["critical", "high"]:
                            critical_failures += 1
                
            except Exception as e:
                logger.error(f"[RulesEngine] Error evaluating rule '{rule.name}': {e}")
                # Treat evaluation errors as failures for safety
                results.append({
                    "rule_name": rule.name,
                    "type": rule.type,
                    "passed": False,
                    "action": rule.action,
                    "severity": rule.severity,
                    "message": f"Rule evaluation error: {str(e)}",
                    "error": str(e)
                })
                failed_count += 1
        
        # Determine overall status
        if critical_failures > 0:
            overall_status = "critical_failure"
        elif should_block:
            overall_status = "blocked"
        elif failed_count > 0:
            overall_status = "warnings"
        else:
            overall_status = "passed"
        
        return {
            "rules_evaluated": len(self.rules),
            "rules_passed": passed_count,
            "rules_failed": failed_count,
            "critical_failures": critical_failures,
            "overall_status": overall_status,
            "should_block": should_block,
            "results": results,
            "timestamp": context.get("timestamp", "")
        }
    
    def _evaluate_rule(self, rule: Rule, context: Dict) -> RuleEvaluationResult:
        """
        Evaluate a single rule
        
        Args:
            rule: Rule to evaluate
            context: Evaluation context
            
        Returns:
            RuleEvaluationResult
        """
        try:
            # Parse and evaluate the condition
            condition_result = self._evaluate_condition(rule.condition, context)
            
            # Rule passes if condition evaluates to True
            passed = bool(condition_result)
            
            return RuleEvaluationResult(rule, passed)
            
        except Exception as e:
            logger.error(f"[RulesEngine] Error evaluating rule '{rule.name}': {e}")
            return RuleEvaluationResult(rule, False, error=str(e))
    
    def _evaluate_condition(self, condition: str, context: Dict) -> bool:
        """
        Evaluate a rule condition
        
        Args:
            condition: Condition string (e.g., "ftso_price_diff_pct <= 2.0")
            context: Evaluation context
            
        Returns:
            Boolean result of condition evaluation
        """
        # Build safe evaluation namespace with context variables
        namespace = self._build_namespace(context)
        
        # Replace comparison operators and boolean keywords for Python
        condition = condition.strip()
        
        # Handle special cases
        if condition.lower() == "true":
            return True
        if condition.lower() == "false":
            return False
        
        # Evaluate condition in safe namespace
        try:
            # Use eval with restricted namespace for safety
            result = eval(condition, {"__builtins__": {}}, namespace)
            return bool(result)
        except Exception as e:
            logger.error(f"[RulesEngine] Condition evaluation error: {condition} -> {e}")
            # If we can't evaluate, fail safe (return False)
            return False
    
    def _build_namespace(self, context: Dict) -> Dict[str, Any]:
        """
        Build evaluation namespace from context
        
        Args:
            context: Raw context dictionary
            
        Returns:
            Namespace dictionary with flattened variables
        """
        # Helper class to allow dot notation access to dictionaries
        class DotDict:
            def __init__(self, data):
                self._data = data
            
            def __getattr__(self, key):
                value = self._data.get(key)
                if isinstance(value, dict):
                    return DotDict(value)
                return value
        
        namespace = {}
        
        # Add direct context values
        for key, value in context.items():
            if not key.startswith('_'):
                namespace[key] = value
        
        # Add nested dictionary access with dot notation support
        if 'market_data' in context:
            namespace['market_data'] = DotDict(context['market_data'])
        
        if 'sentiment_data' in context:
            namespace['sentiment_data'] = DotDict(context['sentiment_data'])
        
        if 'leverage_suggestion' in context:
            namespace['leverage_suggestion'] = DotDict(context['leverage_suggestion'])
        
        # Calculate FTSO price difference percentage if available
        if 'ftso_price' in context and 'market_data' in context:
            ftso_price = context.get('ftso_price', 0)
            declared_price = context.get('market_data', {}).get('price', 0)
            
            if declared_price > 0:
                price_diff_pct = abs(ftso_price - declared_price) / declared_price * 100
                namespace['ftso_price_diff_pct'] = price_diff_pct
            else:
                namespace['ftso_price_diff_pct'] = 100.0  # Invalid price
        
        # Add Python boolean values for YAML comparisons
        namespace['true'] = True
        namespace['True'] = True
        namespace['false'] = False
        namespace['False'] = False
        namespace['null'] = None
        namespace['None'] = None
        
        return namespace
    
    def get_rules_summary(self) -> Dict:
        """
        Get summary of loaded rules
        
        Returns:
            Dictionary with rules summary
        """
        return {
            "total_rules": len(self.rules),
            "rules_by_type": self._count_by_attribute("type"),
            "rules_by_severity": self._count_by_attribute("severity"),
            "rules_by_action": self._count_by_attribute("action"),
            "rules": [rule.to_dict() for rule in self.rules]
        }
    
    def _count_by_attribute(self, attribute: str) -> Dict[str, int]:
        """Count rules by a specific attribute"""
        counts = {}
        for rule in self.rules:
            value = getattr(rule, attribute, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    def reload_rules(self) -> bool:
        """
        Reload rules from file
        
        Returns:
            True if reload successful
        """
        logger.info("[RulesEngine] Reloading verification rules...")
        return self.load_rules()
