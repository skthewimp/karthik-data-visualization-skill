import pytest

from dataviz_mcp.rendering import probe_renderers


@pytest.fixture(scope="session")
def renderer_availability():
    """Probe once, only when a selected integration test needs R."""
    return probe_renderers()


@pytest.fixture(scope="session")
def require_ggplot2(renderer_availability):
    if not renderer_availability["renderers"]["ggplot2"]["available"]:
        pytest.skip("ggplot2+ragg not installed")
