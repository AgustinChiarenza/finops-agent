"""Pytest configuration — ensures required settings exist before app modules import."""
import os

# config.py requires OBS_AK / OBS_SK. Provide dummy values for unit tests.
# (No real OBS calls are made in the unit suite.)
os.environ.setdefault("OBS_AK", "test-ak")
os.environ.setdefault("OBS_SK", "test-sk")
os.environ.setdefault("OBS_BUCKET", "test-bucket")
os.environ.setdefault("MAAS_API_KEY", "")  # insights disabled by default in tests
