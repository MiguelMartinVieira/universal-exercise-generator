import re
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class Validator:
    def __init__(self, rules: List[Dict[str, Any]]):
        self.rules = rules

    def validate_batch(self, exercises: List[Dict[str, str]]) -> Tuple[bool, List[str]]:
        """
        Validates a batch of exercises.
        Returns: (passed_all, list_of_errors)
        """
        all_passed = True
        errors = []

        for idx, ex in enumerate(exercises):
            # 1. Structure Check
            if "enunciado" not in ex or "solucion" not in ex:
                errors.append(f"Exercise {idx+1}: Missing fields.")
                all_passed = False
                continue

            content_to_check = ex['enunciado'] + " " + ex['solucion']

            # 2. Rule Checks
            for rule in self.rules:
                if not self._check_rule(rule, content_to_check):
                    msg = rule.get('message', f"Failed rule {rule.get('name')}")
                    errors.append(f"Exercise {idx+1}: {msg}")
                    all_passed = False
        
        return all_passed, errors

    def _check_rule(self, rule: Dict[str, Any], content: str) -> bool:
        r_type = rule.get('type')
        should_match = rule.get('should_match', True) # Default: Pattern MUST exist
        
        if r_type == 'regex':
            pattern = rule.get('pattern')
            if not pattern: return True
            found = bool(re.search(pattern, content))
            
            if should_match:
                return found # Success if found
            else:
                return not found # Success if NOT found
        
        return True
