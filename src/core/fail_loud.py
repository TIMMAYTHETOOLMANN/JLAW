"""
FailLoud Mixin
===============

Mixin that enforces non-silent failure behaviour for node execution.

Every node analyzer inheriting this mixin will:
- Log errors at ``ERROR`` level (never ``DEBUG``) before propagating.
- Reject empty/null results (``None``, ``[]``, ``{}``) by raising
  :class:`~src.core.exceptions.NodeExecutionError` instead of
  returning silently.
- Re-raise caught exceptions after logging so that the pipeline
  can make an informed halt/continue decision rather than proceeding
  on garbage data.

Usage::

    from src.core.fail_loud import FailLoudMixin

    class MyNodeAnalyzer(FailLoudMixin):
        NODE_ID = "NODE_99"

        async def analyze(self, data):
            result = self._do_analysis(data)
            # Will raise NodeExecutionError if result is None/[]/{}
            self.validate_result(result, "analyze")
            return result
"""

import logging
from typing import Any, Optional

from src.core.exceptions import NodeExecutionError

logger = logging.getLogger(__name__)


class FailLoudMixin:
    """Mixin that prevents silent failures in node execution.

    Subclasses **must** set ``NODE_ID`` as a class-level attribute
    (e.g. ``NODE_ID = "NODE_7"``).  If not set, the class name is
    used as a fallback identifier in error messages.

    Public helpers
    --------------
    - :meth:`validate_result` — call after producing a result to
      ensure it is non-empty.
    - :meth:`fail_loud` — log an error and raise
      :class:`NodeExecutionError`.
    """

    NODE_ID: str = ""

    # ------------------------------------------------------------------
    # Result validation
    # ------------------------------------------------------------------
    def validate_result(
        self,
        result: Any,
        method_name: str = "analyze",
    ) -> None:
        """Raise :class:`NodeExecutionError` if *result* is empty.

        "Empty" means ``None``, an empty ``list``, or an empty ``dict``.
        Non-empty falsy values (``0``, ``False``, ``""``) are **not**
        considered empty — they may be legitimate analysis outputs.

        Args:
            result: The value returned by the analysis method.
            method_name: Name of the calling method (for diagnostics).

        Raises:
            NodeExecutionError: If *result* is ``None``, ``[]``, or ``{}``.
        """
        node_label = self.NODE_ID or self.__class__.__name__
        if result is None or result == [] or result == {}:
            msg = (
                f"{node_label}.{method_name}() produced no results "
                f"(got {type(result).__name__})"
            )
            logger.error(msg)
            raise NodeExecutionError(msg, node_id=self.NODE_ID or None)

    # ------------------------------------------------------------------
    # Explicit failure helper
    # ------------------------------------------------------------------
    def fail_loud(
        self,
        error: Exception,
        context: str = "",
    ) -> None:
        """Log *error* at ERROR level and re-raise as :class:`NodeExecutionError`.

        Use this inside ``except`` blocks instead of swallowing:

        .. code-block:: python

            except Exception as e:
                self.fail_loud(e, context="parsing 10-K filing")

        Args:
            error: The original exception.
            context: Optional human-readable description of what was
                happening when the error occurred.

        Raises:
            NodeExecutionError: Always.
        """
        node_label = self.NODE_ID or self.__class__.__name__
        detail = f" during {context}" if context else ""
        msg = f"{node_label} failed{detail}: {error}"
        logger.error(msg, exc_info=True)
        raise NodeExecutionError(msg, node_id=self.NODE_ID or None) from error
