"""Tests for node type validation — all 8 node types render without error."""

import pytest

from canvas_mcp.models import (
    CanvasNode,
    NodeStyle,
    NODE_STYLES,
)
from canvas_mcp.parser import parse_yaml
from canvas_mcp.renderer import CanvasRenderer


# The 8 canonical node types
ALL_NODE_TYPES = ["input", "output", "process", "decision", "ai", "source", "static", "default"]


class TestNodeTypeStyles:
    """Verify each node type has a defined style."""

    def test_all_types_in_style_map(self):
        """All 8 node types should have entries in NODE_STYLES."""
        for node_type in ALL_NODE_TYPES:
            assert node_type in NODE_STYLES, f"Missing style for node type: {node_type}"

    def test_node_styles_count(self):
        """There should be exactly 8 node type styles."""
        assert len(NODE_STYLES) == 8

    def test_each_style_has_border_color(self):
        """Every node style should have a non-empty border color."""
        for node_type, style in NODE_STYLES.items():
            assert style.border_color, f"No border_color for {node_type}"
            assert style.border_color.startswith("#"), f"Invalid color for {node_type}: {style.border_color}"

    def test_styles_are_unique_colors(self):
        """Each node type should have a distinct border color."""
        colors = [s.border_color for s in NODE_STYLES.values()]
        assert len(set(colors)) == len(colors), "Some node types share the same border color"


class TestNodeStyleResolution:
    """Test node style resolution (default vs custom)."""

    def test_default_style_resolution(self):
        """A node without custom style should get its type's default."""
        node = CanvasNode(id="test", type="input", content="test")
        style = node.get_style()
        assert style.border_color == NODE_STYLES["input"].border_color

    def test_custom_style_overrides(self):
        """A node with custom style should use it instead of the default."""
        custom = NodeStyle(border_color="#123456")
        node = CanvasNode(id="test", type="input", content="test", style=custom)
        style = node.get_style()
        assert style.border_color == "#123456"

    def test_unknown_type_falls_back_to_default(self):
        """An unknown node type should fall back to the 'default' style."""
        node = CanvasNode(id="test", type="nonexistent", content="test")
        style = node.get_style()
        assert style.border_color == NODE_STYLES["default"].border_color


class TestNodeTypeRendering:
    """Verify that all 8 node types render without errors."""

    @pytest.fixture
    def renderer(self):
        return CanvasRenderer(scale=1.0)

    @pytest.mark.parametrize("node_type", ALL_NODE_TYPES)
    def test_single_node_renders(self, renderer, node_type):
        """Each node type should render to PNG bytes without error."""
        yaml_str = f"""\
title: {node_type} Test
nodes:
  - id: test-node
    type: {node_type}
    content: "Testing {node_type} node"
"""
        canvas = parse_yaml(yaml_str)
        png_bytes = renderer.render(canvas)
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0
        # PNG magic bytes
        assert png_bytes[:4] == b"\x89PNG"

    def test_all_types_together(self, renderer, all_types_canvas):
        """All 8 node types in one canvas should render without error."""
        png_bytes = renderer.render(all_types_canvas)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"

    def test_all_types_with_organize(self, renderer, all_types_canvas):
        """All 8 types should render with the organize algorithm enabled."""
        png_bytes = renderer.render(all_types_canvas, organize=True)
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 100

    @pytest.mark.parametrize("node_type", ALL_NODE_TYPES)
    def test_node_type_with_long_content(self, renderer, node_type):
        """Nodes with long content should still render without error."""
        long_text = "This is a very long content string that should be word-wrapped " * 5
        yaml_str = f"""\
title: Long Content {node_type}
nodes:
  - id: long
    type: {node_type}
    content: "{long_text}"
"""
        canvas = parse_yaml(yaml_str)
        png_bytes = renderer.render(canvas)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"

    @pytest.mark.parametrize("node_type", ALL_NODE_TYPES)
    def test_node_type_with_empty_content(self, renderer, node_type):
        """Nodes with empty content should still render without error."""
        yaml_str = f"""\
title: Empty Content {node_type}
nodes:
  - id: empty
    type: {node_type}
    content: ""
"""
        canvas = parse_yaml(yaml_str)
        png_bytes = renderer.render(canvas)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"


class TestNodeAutoSizing:
    """Test that auto-sizing computes reasonable dimensions."""

    @pytest.fixture
    def renderer(self):
        return CanvasRenderer(scale=1.0)

    def test_empty_content_has_minimum_size(self, renderer):
        """Nodes with empty content should still meet minimum dimensions."""
        node = CanvasNode(id="small", type="default", content="")
        w, h = renderer.compute_node_size(node)
        assert w >= renderer.MIN_NODE_WIDTH
        assert h >= renderer.MIN_NODE_HEIGHT

    def test_long_content_increases_height(self, renderer):
        """Nodes with more content should be taller."""
        short_node = CanvasNode(id="short", type="default", content="Short")
        long_node = CanvasNode(id="long", type="default", content="This is a much longer content string that will definitely need multiple lines of text to fully display")
        _, h_short = renderer.compute_node_size(short_node)
        _, h_long = renderer.compute_node_size(long_node)
        assert h_long >= h_short

    def test_width_capped_at_max(self, renderer):
        """Node width should not exceed MAX_NODE_WIDTH."""
        node = CanvasNode(id="wide", type="default", content="x" * 1000)
        w, _ = renderer.compute_node_size(node)
        assert w <= renderer.MAX_NODE_WIDTH
