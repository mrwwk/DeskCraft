import logging

logger = logging.getLogger("desktopenv.metrics.chrome")


def check_enabled_experiments(enabled_experiments, rule):
    """
    Check if the enabled experiments are as expected.

    Supports two rule types:
      - 'names': verifies that the enabled experiments list exactly matches
        the expected list (original behavior, for "enable" tasks).
      - 'disabled_names': verifies that none of the specified flag names appear
        in the enabled experiments list (for "disable" tasks).
    """
    if not enabled_experiments:
        enabled_experiments_names = []
    else:
        enabled_experiments_names = [
            experiment.split("@")[0] for experiment in enabled_experiments
        ]

    if rule['type'] == 'names':
        return 1.0 if enabled_experiments_names == rule['names'] else 0.0

    elif rule['type'] == 'disabled_names':
        for name in rule['names']:
            if name in enabled_experiments_names:
                logger.info(
                    "Flag '%s' is still enabled (should be disabled)", name
                )
                return 0.0
        return 1.0

    else:
        raise TypeError(f"{rule['type']} not support yet!")
