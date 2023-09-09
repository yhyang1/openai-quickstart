import pytest

def pytest_addoption(parser):
    parser.addoption("--openai_api_key", action="store_true", help="Run openai_api_key tests")






