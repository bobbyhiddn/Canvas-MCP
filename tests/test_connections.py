"""Tests for connection/edge parsing — inputs resolve correctly, missing refs handled."""

import pytest

from canvas_mcp.models import (
    Canvas,
    CanvasFactory,
    CanvasMachine,
    CanvasNetwork,
    CanvasNode,
)
from canvas_mcp.parser import parse_yaml
from canvas_mcp.renderer import CanvasRenderer


class TestConnectionParsing:
    """Test that connections (edges) are correctly parsed from inputs/outputs."""

    def test_input_creates_connection(self):
        """A node listing another in 'inputs' should create a connection."""
        yaml_str = """\
title: Input Connection
nodes:
  - id: a
    type: input
    content: "Source"
  - id: b
    type: output
    content: "Sink"
    inputs: [a]
"""
        canvas = parse_yaml(yaml_str)
        conns = canvas.all_connections()
        assert ("a", "b") in conns

    def test_output_creates_connection(self):
        """A node listing another in 'outputs' should create a connection."""
        yaml_str = """\
title: Output Connection
nodes:
  - id: a
    type: input
    content: "Source"
    outputs: [b]
  - id: b
    type: output
    content: "Sink"
"""
        canvas = parse_yaml(yaml_str)
        conns = canvas.all_connections()
        assert ("a", "b") in conns

    def test_bidirectional_dedup(self):
        """Declaring a connection on both sides should not create duplicates."""
        yaml_str = """\
title: Bidirectional
nodes:
  - id: a
    type: input
    content: "Source"
    outputs: [b]
  - id: b
    type: output
    content: "Sink"
    inputs: [a]
"""
        canvas = parse_yaml(yaml_str)
        conns = canvas.all_connections()
        # Should have exactly one (a, b) connection
        assert conns.count(("a", "b")) == 1

    def test_chain_connections(self, simple_canvas):
        """A chain a→b→c should have 2 connections."""
        conns = set(simple_canvas.all_connections())
        assert ("start", "process") in conns
        assert ("process", "end") in conns

    def test_fan_out(self):
        """One node feeding multiple should create multiple connections."""
        yaml_str = """\
title: Fan Out
nodes:
  - id: src
    type: input
    content: "Source"
    outputs: [a, b, c]
  - id: a
    type: process
    content: "A"
  - id: b
    type: process
    content: "B"
  - id: c
    type: process
    content: "C"
"""
        canvas = parse_yaml(yaml_str)
        conns = set(canvas.all_connections())
        assert ("src", "a") in conns
        assert ("src", "b") in conns
        assert ("src", "c") in conns

    def test_fan_in(self):
        """Multiple nodes feeding one should create multiple connections."""
        yaml_str = """\
title: Fan In
nodes:
  - id: a
    type: input
    content: "A"
  - id: b
    type: input
    content: "B"
  - id: c
    type: input
    content: "C"
  - id: sink
    type: output
    content: "Sink"
    inputs: [a, b, c]
"""
        canvas = parse_yaml(yaml_str)
        conns = set(canvas.all_connections())
        assert ("a", "sink") in conns
        assert ("b", "sink") in conns
        assert ("c", "sink") in conns

    def test_no_connections(self):
        """Disconnected nodes should produce zero connections."""
        yaml_str = """\
title: Disconnected
nodes:
  - id: a
    type: input
    content: "Alone A"
  - id: b
    type: output
    content: "Alone B"
"""
        canvas = parse_yaml(yaml_str)
        conns = canvas.all_connections()
        assert len(conns) == 0

    def test_self_referencing_input(self):
        """A node that references itself in inputs shouldn't crash."""
        yaml_str = """\
title: Self Ref
nodes:
  - id: loop
    type: process
    content: "I reference myself"
    inputs: [loop]
"""
        canvas = parse_yaml(yaml_str)
        conns = canvas.all_connections()
        # Self-edge should exist (the parser doesn't filter it)
        assert ("loop", "loop") in conns


class TestMissingNodeReferences:
    """Test handling of connections that reference non-existent nodes."""

    def test_missing_input_ref_still_parses(self):
        """A node referencing a non-existent input should still parse."""
        yaml_str = """\
title: Missing Input
nodes:
  - id: a
    type: output
    content: "References ghost"
    inputs: [ghost]
"""
        canvas = parse_yaml(yaml_str)
        node = canvas.all_nodes()[0]
        assert "ghost" in node.inputs

    def test_missing_output_ref_still_parses(self):
        """A node referencing a non-existent output should still parse."""
        yaml_str = """\
title: Missing Output
nodes:
  - id: a
    type: input
    content: "References ghost"
    outputs: [ghost]
"""
        canvas = parse_yaml(yaml_str)
        node = canvas.all_nodes()[0]
        assert "ghost" in node.outputs

    def test_missing_ref_appears_in_connections(self):
        """Missing references should still appear in all_connections."""
        yaml_str = """\
title: Ghost Connection
nodes:
  - id: a
    type: input
    content: "test"
    outputs: [ghost]
"""
        canvas = parse_yaml(yaml_str)
        conns = canvas.all_connections()
        assert ("a", "ghost") in conns

    def test_missing_ref_renders_without_crash(self):
        """Rendering with missing node refs should not crash."""
        yaml_str = """\
title: Ghost Render
nodes:
  - id: a
    type: input
    content: "References non-existent node"
    outputs: [nonexistent]
  - id: b
    type: output
    content: "References non-existent input"
    inputs: [alsonotreal]
"""
        canvas = parse_yaml(yaml_str)
        renderer = CanvasRenderer(scale=1.0)
        # The renderer skips connections where source or target can't be found
        png_bytes = renderer.render(canvas)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"

    def test_missing_ref_renders_with_organize(self):
        """Organizing with missing node refs should not crash."""
        yaml_str = """\
title: Ghost Organize
nodes:
  - id: a
    type: input
    content: "test"
    outputs: [ghost]
  - id: b
    type: output
    content: "test"
    inputs: [a]
"""
        canvas = parse_yaml(yaml_str)
        renderer = CanvasRenderer(scale=1.0)
        png_bytes = renderer.render(canvas, organize=True)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"


class TestConnectionRendering:
    """Test that connections render correctly between nodes."""

    @pytest.fixture
    def renderer(self):
        return CanvasRenderer(scale=1.0)

    def test_horizontal_connection_renders(self, renderer):
        """Nodes arranged horizontally should render with horizontal beziers."""
        yaml_str = """\
title: Horizontal
nodes:
  - id: left
    type: input
    content: "Left"
    x: 0
    y: 0
    outputs: [right]
  - id: right
    type: output
    content: "Right"
    x: 400
    y: 0
"""
        canvas = parse_yaml(yaml_str)
        png_bytes = renderer.render(canvas, organize=False)
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0

    def test_vertical_connection_renders(self, renderer):
        """Nodes arranged vertically should render with vertical beziers."""
        yaml_str = """\
title: Vertical
nodes:
  - id: top
    type: input
    content: "Top"
    x: 0
    y: 0
    outputs: [bottom]
  - id: bottom
    type: output
    content: "Bottom"
    x: 0
    y: 600
"""
        canvas = parse_yaml(yaml_str)
        png_bytes = renderer.render(canvas, organize=False)
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0

    def test_many_connections_render(self, renderer):
        """A fully connected graph should render without error."""
        yaml_str = """\
title: Dense
nodes:
  - id: center
    type: process
    content: "Hub"
    outputs: [a, b, c, d]
  - id: a
    type: input
    content: "A"
  - id: b
    type: input
    content: "B"
  - id: c
    type: input
    content: "C"
  - id: d
    type: input
    content: "D"
"""
        canvas = parse_yaml(yaml_str)
        png_bytes = renderer.render(canvas, organize=True)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"


class TestNodeLookup:
    """Test the Canvas flat-access helpers."""

    def test_get_node_found(self, simple_canvas):
        """get_node should return the correct node."""
        node = simple_canvas.get_node("start")
        assert node is not None
        assert node.id == "start"

    def test_get_node_not_found(self, simple_canvas):
        """get_node should return None for unknown ids."""
        assert simple_canvas.get_node("nonexistent") is None

    def test_all_nodes_count(self, simple_canvas):
        """all_nodes should return all nodes in the canvas."""
        assert len(simple_canvas.all_nodes()) == 3

    def test_node_map_updated_on_init(self):
        """The node map should be populated after model_post_init."""
        node_a = CanvasNode(id="a", type="input", content="A")
        node_b = CanvasNode(id="b", type="output", content="B")
        machine = CanvasMachine(id="m", nodes=[node_a, node_b])
        factory = CanvasFactory(id="f", machines=[machine])
        network = CanvasNetwork(id="n", factories=[factory])
        canvas = Canvas(title="Test", networks=[network])
        canvas.model_post_init(None)
        assert canvas.get_node("a") is node_a
        assert canvas.get_node("b") is node_b
