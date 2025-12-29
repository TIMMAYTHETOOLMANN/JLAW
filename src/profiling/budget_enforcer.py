"""
Budget Enforcer
===============

Enforces token and cost budgets to prevent runaway API costs during
forensic investigations.

Features:
- Set maximum token budgets
- Set maximum cost budgets (USD)
- Real-time budget checking before agent execution
- Budget tracking and reporting
- Graceful degradation when approaching limits

Usage:
    from src.profiling import BudgetEnforcer, BudgetExceededError
    
    # Create budget enforcer
    enforcer = BudgetEnforcer(
        max_tokens=100000,  # 100K tokens
        max_cost_usd=5.00   # $5.00
    )
    
    # Check before executing agent
    try:
        enforcer.check_budget(tokens=5000, cost=0.15)
        # Execute agent...
        enforcer.record_usage(tokens=5000, cost=0.15)
    except BudgetExceededError as e:
        print(f"Budget exceeded: {e}")
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class BudgetExceededError(Exception):
    """Exception raised when budget limits are exceeded."""
    
    def __init__(
        self,
        message: str,
        budget_type: str,
        current: float,
        limit: float
    ):
        """
        Initialize budget exceeded error.
        
        Args:
            message: Error message
            budget_type: Type of budget exceeded ("tokens" or "cost")
            current: Current usage
            limit: Budget limit
        """
        super().__init__(message)
        self.budget_type = budget_type
        self.current = current
        self.limit = limit


@dataclass
class BudgetStatus:
    """Current budget status."""
    tokens_used: int
    tokens_limit: Optional[int]
    tokens_remaining: Optional[int]
    tokens_percentage: Optional[float]
    
    cost_used: float
    cost_limit: Optional[float]
    cost_remaining: Optional[float]
    cost_percentage: Optional[float]
    
    at_risk: bool  # True if >80% of any budget used
    exceeded: bool  # True if any budget exceeded
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tokens": {
                "used": self.tokens_used,
                "limit": self.tokens_limit,
                "remaining": self.tokens_remaining,
                "percentage": self.tokens_percentage
            },
            "cost": {
                "used": round(self.cost_used, 4),
                "limit": self.cost_limit,
                "remaining": round(self.cost_remaining, 4) if self.cost_remaining else None,
                "percentage": self.cost_percentage
            },
            "at_risk": self.at_risk,
            "exceeded": self.exceeded
        }


class BudgetEnforcer:
    """
    Enforce token and cost budgets.
    
    Provides real-time budget checking and enforcement to prevent
    runaway API costs during investigations.
    """
    
    # Warning threshold (percentage of budget)
    WARNING_THRESHOLD = 0.80  # 80%
    
    def __init__(
        self,
        max_tokens: Optional[int] = None,
        max_cost_usd: Optional[float] = None,
        strict_mode: bool = True
    ):
        """
        Initialize budget enforcer.
        
        Args:
            max_tokens: Maximum total tokens allowed (None for no limit)
            max_cost_usd: Maximum total cost in USD (None for no limit)
            strict_mode: If True, raise exception when budget exceeded.
                        If False, log warning but allow execution.
        """
        self.max_tokens = max_tokens
        self.max_cost_usd = max_cost_usd
        self.strict_mode = strict_mode
        
        self.current_tokens = 0
        self.current_cost = 0.0
        
        self._warning_logged_tokens = False
        self._warning_logged_cost = False
        
        if max_tokens:
            logger.info(f"Token budget enforcer initialized: {max_tokens:,} tokens")
        if max_cost_usd:
            logger.info(f"Cost budget enforcer initialized: ${max_cost_usd:.2f}")
        if not max_tokens and not max_cost_usd:
            logger.warning("BudgetEnforcer initialized without any limits")
    
    def check_budget(
        self,
        tokens: int,
        cost: float,
        agent_name: Optional[str] = None
    ):
        """
        Check if operation would exceed budget.
        
        Args:
            tokens: Number of tokens for the operation
            cost: Cost in USD for the operation
            agent_name: Optional agent name for logging
            
        Raises:
            BudgetExceededError: If operation would exceed budget and strict_mode=True
        """
        # Check token budget
        if self.max_tokens:
            new_tokens = self.current_tokens + tokens
            if new_tokens > self.max_tokens:
                message = (
                    f"Token budget would be exceeded: "
                    f"{new_tokens:,} > {self.max_tokens:,}"
                )
                if agent_name:
                    message = f"[{agent_name}] {message}"
                
                if self.strict_mode:
                    raise BudgetExceededError(
                        message,
                        budget_type="tokens",
                        current=new_tokens,
                        limit=self.max_tokens
                    )
                else:
                    logger.warning(f"BUDGET WARNING: {message}")
            
            # Check if approaching limit (80%)
            elif new_tokens > (self.max_tokens * self.WARNING_THRESHOLD) and not self._warning_logged_tokens:
                percentage = (new_tokens / self.max_tokens) * 100
                logger.warning(
                    f"Token budget at {percentage:.1f}%: "
                    f"{new_tokens:,} / {self.max_tokens:,}"
                )
                self._warning_logged_tokens = True
        
        # Check cost budget
        if self.max_cost_usd:
            new_cost = self.current_cost + cost
            if new_cost > self.max_cost_usd:
                message = (
                    f"Cost budget would be exceeded: "
                    f"${new_cost:.4f} > ${self.max_cost_usd:.2f}"
                )
                if agent_name:
                    message = f"[{agent_name}] {message}"
                
                if self.strict_mode:
                    raise BudgetExceededError(
                        message,
                        budget_type="cost",
                        current=new_cost,
                        limit=self.max_cost_usd
                    )
                else:
                    logger.warning(f"BUDGET WARNING: {message}")
            
            # Check if approaching limit (80%)
            elif new_cost > (self.max_cost_usd * self.WARNING_THRESHOLD) and not self._warning_logged_cost:
                percentage = (new_cost / self.max_cost_usd) * 100
                logger.warning(
                    f"Cost budget at {percentage:.1f}%: "
                    f"${new_cost:.4f} / ${self.max_cost_usd:.2f}"
                )
                self._warning_logged_cost = True
    
    def record_usage(
        self,
        tokens: int,
        cost: float,
        agent_name: Optional[str] = None
    ):
        """
        Record token and cost usage.
        
        Args:
            tokens: Number of tokens used
            cost: Cost in USD
            agent_name: Optional agent name for logging
        """
        self.current_tokens += tokens
        self.current_cost += cost
        
        logger.debug(
            f"Budget usage recorded{f' [{agent_name}]' if agent_name else ''}: "
            f"+{tokens:,} tokens (+${cost:.4f}) | "
            f"Total: {self.current_tokens:,} tokens (${self.current_cost:.4f})"
        )
    
    def get_status(self) -> BudgetStatus:
        """
        Get current budget status.
        
        Returns:
            BudgetStatus object with current usage and limits
        """
        # Calculate token metrics
        tokens_remaining = None
        tokens_percentage = None
        if self.max_tokens:
            tokens_remaining = max(0, self.max_tokens - self.current_tokens)
            tokens_percentage = (self.current_tokens / self.max_tokens) * 100
        
        # Calculate cost metrics
        cost_remaining = None
        cost_percentage = None
        if self.max_cost_usd:
            cost_remaining = max(0.0, self.max_cost_usd - self.current_cost)
            cost_percentage = (self.current_cost / self.max_cost_usd) * 100
        
        # Check if at risk or exceeded
        at_risk = False
        exceeded = False
        
        if tokens_percentage and tokens_percentage >= (self.WARNING_THRESHOLD * 100):
            at_risk = True
        if tokens_percentage and tokens_percentage > 100:
            exceeded = True
        
        if cost_percentage and cost_percentage >= (self.WARNING_THRESHOLD * 100):
            at_risk = True
        if cost_percentage and cost_percentage > 100:
            exceeded = True
        
        return BudgetStatus(
            tokens_used=self.current_tokens,
            tokens_limit=self.max_tokens,
            tokens_remaining=tokens_remaining,
            tokens_percentage=round(tokens_percentage, 1) if tokens_percentage else None,
            cost_used=self.current_cost,
            cost_limit=self.max_cost_usd,
            cost_remaining=cost_remaining,
            cost_percentage=round(cost_percentage, 1) if cost_percentage else None,
            at_risk=at_risk,
            exceeded=exceeded
        )
    
    def reset(self):
        """Reset usage counters."""
        self.current_tokens = 0
        self.current_cost = 0.0
        self._warning_logged_tokens = False
        self._warning_logged_cost = False
        logger.info("Budget counters reset")
    
    def get_remaining_budget(self) -> Dict[str, Any]:
        """
        Get remaining budget information.
        
        Returns:
            Dictionary with remaining tokens and cost
        """
        remaining = {
            "tokens": None,
            "cost": None,
            "can_continue": True
        }
        
        if self.max_tokens:
            remaining["tokens"] = max(0, self.max_tokens - self.current_tokens)
            if remaining["tokens"] == 0:
                remaining["can_continue"] = False
        
        if self.max_cost_usd:
            remaining["cost"] = max(0.0, self.max_cost_usd - self.current_cost)
            if remaining["cost"] <= 0:
                remaining["can_continue"] = False
        
        return remaining
    
    def __repr__(self) -> str:
        """String representation."""
        status = self.get_status()
        parts = []
        
        if self.max_tokens:
            parts.append(
                f"Tokens: {status.tokens_used:,}/{self.max_tokens:,} "
                f"({status.tokens_percentage or 0:.1f}%)"
            )
        
        if self.max_cost_usd:
            parts.append(
                f"Cost: ${status.cost_used:.4f}/${self.max_cost_usd:.2f} "
                f"({status.cost_percentage or 0:.1f}%)"
            )
        
        if not parts:
            return "BudgetEnforcer(no limits set)"
        
        return f"BudgetEnforcer({', '.join(parts)})"
