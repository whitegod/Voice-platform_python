"""
Policy Planner
Validates and enforces business rules and compliance
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class PolicyViolationType(Enum):
    """Types of policy violations"""
    UNAUTHORIZED = "unauthorized"
    RATE_LIMIT = "rate_limit"
    DATA_VALIDATION = "data_validation"
    COMPLIANCE = "compliance"
    SAFETY = "safety"


class PolicyViolation:
    """Represents a policy violation"""
    
    def __init__(
        self,
        violation_type: PolicyViolationType,
        message: str,
        severity: str = "error"
    ):
        self.violation_type = violation_type
        self.message = message
        self.severity = severity


class PolicyPlanner:
    """
    Validates action plans against business rules and policies.
    Ensures compliance and safety before execution.
    """

    def __init__(
        self,
        rate_limit_per_minute: int = 60,
        rate_limit_per_hour: int = 1000,
        require_moderation: bool = True
    ):
        """
        Initialize policy planner.

        Args:
            rate_limit_per_minute: Max requests per minute per tenant
            rate_limit_per_hour: Max requests per hour per tenant
            require_moderation: Whether to require content moderation
        """
        self.rate_limit_per_minute = rate_limit_per_minute
        self.rate_limit_per_hour = rate_limit_per_hour
        self.require_moderation = require_moderation
        
        # In-memory rate limiting (use Redis in production)
        self.request_counts = {}
        
        logger.info("PolicyPlanner initialized")

    async def validate_plan(
        self,
        tenant_id: str,
        plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> tuple[bool, List[PolicyViolation]]:
        """
        Validate action plan against policies.

        Args:
            tenant_id: Tenant identifier
            plan: Action plan to validate
            context: Execution context

        Returns:
            (is_valid, violations)
        """
        violations = []

        try:
            # Check rate limits
            rate_limit_violations = await self._check_rate_limits(tenant_id)
            violations.extend(rate_limit_violations)

            # Check authentication and authorization
            auth_violations = self._check_authorization(tenant_id, plan, context)
            violations.extend(auth_violations)

            # Check data validation
            data_violations = self._validate_data(plan)
            violations.extend(data_violations)

            # Check content safety
            if self.require_moderation:
                safety_violations = self._check_safety(plan, context)
                violations.extend(safety_violations)

            # Check for critical violations
            is_valid = not any(v.severity == "error" for v in violations)

            if not is_valid:
                logger.warning(f"Plan validation failed for tenant {tenant_id}: "
                             f"{len(violations)} violations")
            else:
                logger.debug(f"Plan validation passed for tenant {tenant_id}")

            return is_valid, violations

        except Exception as e:
            logger.error(f"Policy validation error: {e}")
            return False, [PolicyViolation(
                PolicyViolationType.COMPLIANCE,
                f"Validation error: {e}",
                "error"
            )]

    async def _check_rate_limits(self, tenant_id: str) -> List[PolicyViolation]:
        """Check rate limiting policies"""
        violations = []
        
        try:
            # Simple in-memory rate limiting
            # In production, use Redis with sliding windows
            
            current_count = self.request_counts.get(tenant_id, 0)
            
            if current_count >= self.rate_limit_per_minute:
                violations.append(PolicyViolation(
                    PolicyViolationType.RATE_LIMIT,
                    "Rate limit exceeded",
                    "error"
                ))
            else:
                self.request_counts[tenant_id] = current_count + 1

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")

        return violations

    def _check_authorization(
        self,
        tenant_id: str,
        plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[PolicyViolation]:
        """Check authorization policies"""
        violations = []

        try:
            # Check if tenant is authorized for the requested actions
            actions = plan.get("actions", [])
            
            for action in actions:
                if action.get("requires_auth"):
                    if not context.get("auth_token"):
                        violations.append(PolicyViolation(
                            PolicyViolationType.UNAUTHORIZED,
                            f"Action '{action.get('name')}' requires authentication",
                            "error"
                        ))

        except Exception as e:
            logger.error(f"Authorization check failed: {e}")

        return violations

    def _validate_data(self, plan: Dict[str, Any]) -> List[PolicyViolation]:
        """Validate data in the plan"""
        violations = []

        try:
            # Check required fields
            if not plan.get("intent"):
                violations.append(PolicyViolation(
                    PolicyViolationType.DATA_VALIDATION,
                    "Missing required field: intent",
                    "error"
                ))

            # Validate entities
            entities = plan.get("entities", {})
            for key, value in entities.items():
                if value is None or value == "":
                    violations.append(PolicyViolation(
                        PolicyViolationType.DATA_VALIDATION,
                        f"Invalid entity value for '{key}'",
                        "warning"
                    ))

        except Exception as e:
            logger.error(f"Data validation failed: {e}")

        return violations

    def _check_safety(
        self,
        plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[PolicyViolation]:
        """Check content safety"""
        violations = []

        try:
            # Check if content passed moderation
            moderation_result = context.get("moderation_result", {})
            
            if not moderation_result.get("is_safe", True):
                flagged = moderation_result.get("flagged_categories", [])
                violations.append(PolicyViolation(
                    PolicyViolationType.SAFETY,
                    f"Content flagged for: {', '.join(flagged)}",
                    "error"
                ))

        except Exception as e:
            logger.error(f"Safety check failed: {e}")

        return violations

    def enforce_compliance(
        self,
        tenant_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enforce compliance rules on data.

        Args:
            tenant_id: Tenant identifier
            data: Data to sanitize

        Returns:
            Sanitized data
        """
        try:
            # Remove sensitive fields
            sanitized = data.copy()
            
            sensitive_fields = [
                "password", "api_key", "secret", "token",
                "ssn", "credit_card"
            ]
            
            for field in sensitive_fields:
                if field in sanitized:
                    sanitized[field] = "***REDACTED***"

            return sanitized

        except Exception as e:
            logger.error(f"Compliance enforcement failed: {e}")
            return data

    def get_policy_summary(self) -> Dict[str, Any]:
        """Get current policy configuration"""
        return {
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "rate_limit_per_hour": self.rate_limit_per_hour,
            "require_moderation": self.require_moderation
        }

