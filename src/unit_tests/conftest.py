import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--should-visualize",
        action="store",
        default="false",
        help="Enable or disable visualization in tests (true/false)",
    )


@pytest.fixture
def should_visualize(request):
    return request.config.getoption("--should-visualize").lower() == "true"
