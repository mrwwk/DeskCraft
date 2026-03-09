"""
Interactive evaluation metrics for multi-turn user simulation tasks.

Provides a delegating evaluator that routes to existing metric functions,
allowing interactive tasks to reuse the full existing evaluation infrastructure.
"""

import logging
from desktop_env.evaluators.metrics import general as general_metrics
from desktop_env.evaluators.metrics import gimp as gimp_metrics
from desktop_env.evaluators.metrics import new_gimp as new_gimp_metrics

logger = logging.getLogger("desktopenv.evaluators.interactive")


def check_interactive_final_result(result_state, expected_state=None, **kwargs):
    """
    Generic evaluator for interactive tasks — delegates to an existing metric function.
    
    The task config should specify a "delegate_func" in the evaluator options
    to indicate which existing metric to use for final result checking.
    
    If no delegate is specified, falls back to a simple file existence check.
    
    Args:
        result_state: The result state obtained by the getter
        expected_state: The expected state obtained by the getter (if any)
        **kwargs: Additional options, including "delegate_func"
        
    Returns:
        float: 1.0 if the final result passes, 0.0 otherwise
    """
    delegate_func_name = kwargs.pop("delegate_func", None)

    if delegate_func_name is None:
        # Default: just check that the result exists and is non-empty
        if result_state is not None:
            if isinstance(result_state, (str, bytes)) and len(result_state) > 0:
                return 1.0
            elif isinstance(result_state, str) and result_state.strip():
                return 1.0
        return 0.0

    # Try to find the delegate function in known metric modules
    func = None
    for module in [new_gimp_metrics, gimp_metrics, general_metrics]:
        if hasattr(module, delegate_func_name):
            func = getattr(module, delegate_func_name)
            break

    if func is None:
        logger.error(
            f"Delegate function '{delegate_func_name}' not found in any metric module"
        )
        return 0.0

    # Call the delegate with appropriate arguments
    try:
        if expected_state is not None:
            return float(func(result_state, expected_state, **kwargs))
        else:
            return float(func(result_state, **kwargs))
    except Exception as e:
        logger.error(f"Error calling delegate function '{delegate_func_name}': {e}")
        return 0.0
