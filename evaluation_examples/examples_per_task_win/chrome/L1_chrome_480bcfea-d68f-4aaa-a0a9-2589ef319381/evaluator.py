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
    def parse_experiment(experiment):
        name, separator, value = str(experiment).partition("@")
        return name, value if separator else None

    enabled_experiments_by_name = {}
    for experiment in enabled_experiments or []:
        name, value = parse_experiment(experiment)
        enabled_experiments_by_name.setdefault(name, []).append(value)

    enabled_experiments_names = list(enabled_experiments_by_name.keys())

    if rule['type'] == 'names':
        return 1.0 if enabled_experiments_names == rule['names'] else 0.0

    elif rule['type'] == 'disabled_names':
        disabled_values = {"0", "2", "disabled", "disable", "false", "off"}
        enabled_values = {"1", "enabled", "enable", "true", "on"}

        for name in rule['names']:
            values = enabled_experiments_by_name.get(name, [])
            if not values:
                continue

            if all(value is not None and value.lower() in disabled_values for value in values):
                continue

            if any(value is None or value.lower() in enabled_values for value in values):
                logger.info(
                    "Flag '%s' is still enabled (should be disabled)", name
                )
                return 0.0

            logger.info(
                "Flag '%s' has unknown experiment values %s; treating as enabled",
                name,
                values,
            )
            return 0.0

        return 1.0

    else:
        raise TypeError(f"{rule['type']} not support yet!")
