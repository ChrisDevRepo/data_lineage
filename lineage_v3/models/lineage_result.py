"""
Enhanced result models for Phase 2: Serial flow architecture with step tracking.

These models track parsing steps internally while maintaining backward compatibility
with the existing output schema (List[int] for inputs/outputs).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Literal, Optional
import time


@dataclass
class StepResult:
    """
    Result from a single parsing step.

    Tracks what each step (regex, sqlglot, ai) found and how long it took.
    """
    step_name: Literal['regex', 'sqlglot', 'ai']
    sources_found: int
    targets_found: int
    confidence: float
    execution_time_ms: float
    skipped: bool = False  # True if step was skipped due to early exit

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging."""
        return {
            'step': self.step_name,
            'sources': self.sources_found,
            'targets': self.targets_found,
            'confidence': self.confidence,
            'time_ms': round(self.execution_time_ms, 2),
            'skipped': self.skipped
        }


@dataclass
class LineageResult:
    """
    Enhanced parser result with step-by-step tracking.

    Maintains backward compatibility: to_dict() returns the same format as before,
    but internally tracks which step found each dependency.

    Phase 2 Features:
    - Step history tracking
    - Monotonic confidence (never decreases)
    - Early exit capability
    """
    object_id: int

    # Backward compatible outputs (List[int])
    inputs: List[int] = field(default_factory=list)
    outputs: List[int] = field(default_factory=list)

    # Enhanced tracking
    confidence: float = 0.0
    primary_source: Literal['regex', 'sqlglot', 'ai', 'hybrid'] = 'regex'
    step_history: List[StepResult] = field(default_factory=list)

    # Quality metrics (existing fields)
    quality_check: Optional[Dict[str, Any]] = None
    parse_error: Optional[str] = None

    def add_step(self, step: StepResult):
        """
        Add a parsing step to history.

        Ensures monotonic confidence: new confidence must be >= previous.
        """
        if step.confidence < self.confidence:
            # Log warning but allow it (might be intentional fallback)
            import logging
            logging.getLogger(__name__).warning(
                f"Step {step.step_name} has lower confidence ({step.confidence:.2f}) "
                f"than previous ({self.confidence:.2f}). Keeping higher confidence."
            )
            # Don't decrease confidence
            step.confidence = self.confidence

        self.step_history.append(step)

        # Update confidence to latest step's confidence (monotonic due to check above)
        self.confidence = step.confidence

    def update_dependencies(
        self,
        new_inputs: List[int],
        new_outputs: List[int],
        source: Literal['regex', 'sqlglot', 'ai']
    ):
        """
        Update inputs/outputs from a parsing step.

        Args:
            new_inputs: Object IDs found as inputs
            new_outputs: Object IDs found as outputs
            source: Which step found these
        """
        self.inputs = new_inputs
        self.outputs = new_outputs
        self.primary_source = source

    def merge_dependencies(
        self,
        additional_inputs: List[int],
        additional_outputs: List[int]
    ):
        """
        Merge additional dependencies (e.g., from AI).

        Uses set union to avoid duplicates.
        """
        self.inputs = list(set(self.inputs + additional_inputs))
        self.outputs = list(set(self.outputs + additional_outputs))

        # If merging, it's a hybrid result
        if additional_inputs or additional_outputs:
            self.primary_source = 'hybrid'

    def should_run_ai(self, ai_threshold: float) -> bool:
        """
        Determine if AI should run based on current confidence.

        Phase 2 Early Exit: Skip AI if confidence >= threshold (0.90).

        Args:
            ai_threshold: Confidence threshold (default 0.90)

        Returns:
            True if AI should run, False to skip
        """
        return self.confidence < ai_threshold

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for storage/API.

        IMPORTANT: Maintains backward compatibility with existing schema.
        Returns same format as before (simple List[int] for inputs/outputs).
        """
        result = {
            'object_id': self.object_id,
            'inputs': self.inputs,  # Simple list of IDs (backward compatible)
            'outputs': self.outputs,
            'confidence': self.confidence,
            'source': self.primary_source,
        }

        # Add quality check if present
        if self.quality_check:
            result['quality_check'] = self.quality_check

        # Add error if present
        if self.parse_error:
            result['parse_error'] = self.parse_error

        return result

    def to_dict_with_steps(self) -> Dict[str, Any]:
        """
        Extended format with step history (for debugging/logging).

        This is NOT stored in the database to maintain compatibility.
        """
        result = self.to_dict()
        result['step_history'] = [step.to_dict() for step in self.step_history]
        return result

    def get_step_summary(self) -> str:
        """
        Get human-readable summary of parsing steps.

        Example: "regex(0.50) → sqlglot(0.85) → ai(skipped)"
        """
        if not self.step_history:
            return "No steps"

        parts = []
        for step in self.step_history:
            if step.skipped:
                parts.append(f"{step.step_name}(skipped)")
            else:
                parts.append(f"{step.step_name}({step.confidence:.2f})")

        return " → ".join(parts)
