from PIL import Image
import pytest

from dataviz_mcp.review_views import build_review_views


@pytest.mark.parametrize('display_width', [None, 360, 900, 1800])
def test_delivery_view_uses_display_width_and_preserves_aspect(tmp_path, display_width):
    artifact = tmp_path / 'chart.png'
    Image.new('RGB', (1200, 2400), '#abcdef').save(artifact)
    views = build_review_views(artifact, tmp_path, 'review', display_width_px=display_width)
    with Image.open(views[0]) as native, Image.open(views[1]) as delivery:
        assert native.size == (1200, 2400)
        assert delivery.size == (display_width or 640, 2 * (display_width or 640))
        assert native.getpixel((100, 100)) == delivery.getpixel((100, 100))
