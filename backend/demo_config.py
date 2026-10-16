import os


def is_public_demo():
    """
    Return True when SolarQC is running in public demo mode.
    """
    return os.getenv(
        "SOLARQC_PUBLIC_DEMO", "false"
    ).strip().lower() in {"true", "1", "yes"}


def allow_full_ai():
    """
    Full AI is only available in local development.
    """
    return not is_public_demo()