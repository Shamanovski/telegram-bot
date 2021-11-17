import pytest


def pytest_addoption(parser):
    parser.addoption("--channel", action="store")


@pytest.fixture
def channel(request):
    return request.config.getoption("--channel")
