"""Tests for YAML recipe parsing — valid recipes, malformed YAML, missing fields."""

import pytest
import yaml

from canvas_mcp.parser import parse_yaml, parse_file, canvas_to_yaml, _parse_node
from canvas_mcp.models import (
    Canvas,
    CanvasNode,
    CanvasMachine,
    CanvasFactory,
    CanvasNetwork,
    NodeStyle,
)


# ===================================================================
# Valid simple-format parsing
# ===================================================================

class TestSimpleFormatParsing:
    """Tests for the simplified flat YAML format."""

    def test_parse_minimal_recipe(self):
        """A recipe with just a title and one node should parse."""
        yaml_str = """\
title: Minimal
nodes:
  - id: only
    type: input
    content: "The only node"
"""
        canvas = parse_yaml(yaml_str)
        assert canvas.title == "Minimal"
        assert len(canvas.all_nodes()) == 1
        assert canvas.all_nodes()[0].id == "only"

    def test_parse_simple_recipe(self, simple_canvas):
        """Standard 3-node recipe parses correctly."""
        assert simple_canvas.title == "Simple Test"
        nodes = simple_canvas.all_nodes()
        assert len(nodes) == 3
        node_ids = {n.id for n in nodes}
        assert node_ids == {"start", "process", "end"}

    def test_simple_format_creates_hierarchy(self, simple_canvas):
        """Simple format wraps nodes in auto-generated machine/factory/network."""
        assert len(simple_canvas.networks) == 1
        network = simple_canvas.networks[0]
        assert network.id == "network-1"
        assert len(network.factories) == 1
        factory = network.factories[0]
        assert factory.id == "factory-1"
        assert len(factory.machines) == 1
        machine = factory.machines[0]
        assert machine.id == "machine-1"

    def test_node_types_preserved(self, simple_canvas):
        """Node types should match what was specified in the recipe."""
        node_map = {n.id: n for n in simple_canvas.all_nodes()}
        assert node_map["start"].type == "input"
        assert node_map["process"].type == "process"
        assert node_map["end"].type == "output"

    def test_node_content_preserved(self, simple_canvas):
        """Node content text should be preserved."""
        node_map = {n.id: n for n in simple_canvas.all_nodes()}
        assert node_map["start"].content == "Begin here"
        assert node_map["process"].content == "Do work"
        assert node_map["end"].content == "Done"

    def test_node_inputs_preserved(self, simple_canvas):
        """Node inputs list should be preserved."""
        node_map = {n.id: n for n in simple_canvas.all_nodes()}
        assert node_map["process"].inputs == ["start"]
        assert node_map["end"].inputs == ["process"]

    def test_default_background(self):
        """Default background color should be #11111b."""
        canvas = parse_yaml("title: Test\nnodes:\n  - id: a\n    type: default\n    content: x")
        assert canvas.background_color == "#11111b"

    def test_custom_background(self):
        """Background color can be overridden."""
        yaml_str = """\
title: Custom BG
background: "#ff0000"
nodes:
  - id: a
    type: default
    content: test
"""
        canvas = parse_yaml(yaml_str)
        assert canvas.background_color == "#ff0000"

    def test_default_node_type(self):
        """Nodes without a type field should default to 'default'."""
        yaml_str = """\
title: No Type
nodes:
  - id: a
    content: "No type specified"
"""
        canvas = parse_yaml(yaml_str)
        assert canvas.all_nodes()[0].type == "default"

    def test_node_label(self):
        """Nodes with an explicit label should preserve it."""
        yaml_str = """\
title: Labeled
nodes:
  - id: my-node
    type: input
    content: "Some content"
    label: "My Custom Label"
"""
        canvas = parse_yaml(yaml_str)
        node = canvas.all_nodes()[0]
        assert node.label == "My Custom Label"
        assert node.get_label() == "My Custom Label"

    def test_node_label_fallback(self):
        """Nodes without a label should use their id as the display label."""
        yaml_str = """\
title: No Label
nodes:
  - id: my-node
    type: input
    content: "Some content"
"""
        canvas = parse_yaml(yaml_str)
        node = canvas.all_nodes()[0]
        assert node.label is None
        assert node.get_label() == "my-node"

    def test_node_with_outputs(self):
        """Nodes can specify outputs instead of (or alongside) inputs."""
        yaml_str = """\
title: Outputs
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
        node_map = {n.id: n for n in canvas.all_nodes()}
        assert node_map["a"].outputs == ["b"]

    def test_node_custom_dimensions(self):
        """Nodes can specify custom width and height."""
        yaml_str = """\
title: Custom Size
nodes:
  - id: big
    type: default
    content: "Big node"
    width: 500
    height: 300
"""
        canvas = parse_yaml(yaml_str)
        node = canvas.all_nodes()[0]
        assert node.width == 500.0
        assert node.height == 300.0

    def test_node_custom_position(self):
        """Nodes can specify x and y coordinates."""
        yaml_str = """\
title: Positioned
nodes:
  - id: placed
    type: default
    content: "Placed node"
    x: 100
    y: 200
"""
        canvas = parse_yaml(yaml_str)
        node = canvas.all_nodes()[0]
        assert node.x == 100.0
        assert node.y == 200.0

    def test_node_default_position(self):
        """Nodes without x/y should default to (0, 0)."""
        yaml_str = """\
title: Default Position
nodes:
  - id: a
    type: default
    content: "test"
"""
        canvas = parse_yaml(yaml_str)
        node = canvas.all_nodes()[0]
        assert node.x == 0.0
        assert node.y == 0.0

    def test_node_custom_style(self):
        """Nodes can override default styling."""
        yaml_str = """\
title: Styled
nodes:
  - id: custom
    type: input
    content: "Custom styled"
    style:
      border_color: "#ff00ff"
      fill_color: "#000000"
"""
        canvas = parse_yaml(yaml_str)
        node = canvas.all_nodes()[0]
        assert node.style is not None
        assert node.style.border_color == "#ff00ff"
        assert node.style.fill_color == "#000000"

    def test_empty_nodes_list(self):
        """A recipe with an empty nodes list should produce an empty canvas."""
        yaml_str = """\
title: Empty
nodes: []
"""
        canvas = parse_yaml(yaml_str)
        assert len(canvas.all_nodes()) == 0

    def test_no_nodes_key(self):
        """A recipe without a 'nodes' key should still parse (empty canvas)."""
        yaml_str = "title: No Nodes\n"
        canvas = parse_yaml(yaml_str)
        assert len(canvas.all_nodes()) == 0


# ===================================================================
# Valid hierarchical-format parsing
# ===================================================================

class TestHierarchicalFormatParsing:
    """Tests for the full hierarchical YAML format (canvas > networks > factories > machines > nodes)."""

    def test_parse_hierarchical(self, hierarchical_canvas):
        """Hierarchical recipe with machines and factories parses correctly."""
        assert hierarchical_canvas.title == "Hierarchical Test"
        assert len(hierarchical_canvas.all_nodes()) == 4

    def test_hierarchy_structure(self, hierarchical_canvas):
        """Verify the full hierarchy: network > factory > machines > nodes."""
        assert len(hierarchical_canvas.networks) == 1
        network = hierarchical_canvas.networks[0]
        assert network.id == "net-1"
        assert network.label == "Test Network"

        assert len(network.factories) == 1
        factory = network.factories[0]
        assert factory.id == "fac-1"
        assert factory.label == "Factory One"

        assert len(factory.machines) == 2
        m1, m2 = factory.machines
        assert m1.id == "mach-1"
        assert m2.id == "mach-2"

        assert len(m1.nodes) == 2
        assert len(m2.nodes) == 2

    def test_hierarchical_node_map(self, hierarchical_canvas):
        """The node map should allow lookup by id."""
        node_a = hierarchical_canvas.get_node("a")
        assert node_a is not None
        assert node_a.type == "input"

        node_d = hierarchical_canvas.get_node("d")
        assert node_d is not None
        assert node_d.type == "output"

    def test_hierarchical_connections(self, hierarchical_canvas):
        """Cross-machine connections should be detected."""
        connections = hierarchical_canvas.all_connections()
        # a→b, b→c, c→d = 3 connections
        assert len(connections) >= 3
        conn_set = set(connections)
        assert ("a", "b") in conn_set or ("b", "a") in conn_set  # a→b via inputs

    def test_multi_factory(self, multi_factory_canvas):
        """Multiple factories within a network should parse correctly."""
        assert multi_factory_canvas.title == "Multi-Factory Test"
        network = multi_factory_canvas.networks[0]
        assert len(network.factories) == 3
        factory_ids = [f.id for f in network.factories]
        assert "fac-input" in factory_ids
        assert "fac-process" in factory_ids
        assert "fac-output" in factory_ids

    def test_hierarchical_defaults(self):
        """Missing optional fields should use defaults."""
        yaml_str = """\
canvas:
  networks:
    - id: net
      factories:
        - id: fac
          machines:
            - id: mach
              nodes:
                - id: n1
                  content: "test"
"""
        canvas = parse_yaml(yaml_str)
        assert canvas.title == "Untitled Canvas"
        assert canvas.version == "2.0"
        node = canvas.all_nodes()[0]
        assert node.type == "default"

    def test_factory_style(self):
        """Factory container style should be parsed."""
        yaml_str = """\
canvas:
  title: Styled Factory
  networks:
    - id: net
      factories:
        - id: fac
          style:
            border_color: "#ff0000"
            label_color: "#00ff00"
          machines:
            - id: mach
              nodes:
                - id: n1
                  type: default
                  content: "test"
"""
        canvas = parse_yaml(yaml_str)
        factory = canvas.networks[0].factories[0]
        assert factory.style is not None
        assert factory.style.border_color == "#ff0000"
        assert factory.style.label_color == "#00ff00"

    def test_machine_style(self):
        """Machine container style should be parsed."""
        yaml_str = """\
canvas:
  title: Styled Machine
  networks:
    - id: net
      factories:
        - id: fac
          machines:
            - id: mach
              style:
                fill_color: "#222222"
                alpha: 200
              nodes:
                - id: n1
                  type: default
                  content: "test"
"""
        canvas = parse_yaml(yaml_str)
        machine = canvas.networks[0].factories[0].machines[0]
        assert machine.style is not None
        assert machine.style.fill_color == "#222222"
        assert machine.style.alpha == 200


# ===================================================================
# Malformed / invalid YAML
# ===================================================================

class TestMalformedYAML:
    """Tests for error handling with bad input."""

    def test_empty_string(self):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError, match="Empty YAML"):
            parse_yaml("")

    def test_none_yaml(self):
        """YAML that parses to None should raise ValueError."""
        with pytest.raises(ValueError, match="Empty YAML"):
            parse_yaml("---\n")

    def test_invalid_yaml_syntax(self):
        """Malformed YAML should raise a yaml error."""
        with pytest.raises(yaml.YAMLError):
            parse_yaml("title: test\n  invalid:\nindentation: broken\n    - oops")

    def test_node_missing_id(self):
        """A node without an 'id' field should raise KeyError."""
        yaml_str = """\
title: Missing ID
nodes:
  - type: input
    content: "No id here"
"""
        with pytest.raises(KeyError):
            parse_yaml(yaml_str)

    def test_plain_string_yaml(self):
        """Plain string YAML (not a dict) should raise an error."""
        with pytest.raises((TypeError, AttributeError)):
            parse_yaml("just a plain string")

    def test_list_yaml(self):
        """YAML that parses to a list should raise an error."""
        with pytest.raises((TypeError, AttributeError)):
            parse_yaml("- item1\n- item2\n")


# ===================================================================
# Serialization round-trip
# ===================================================================

class TestSerialization:
    """Tests for canvas_to_yaml serialization."""

    def test_round_trip_hierarchical(self, hierarchical_canvas):
        """Parse → serialize → re-parse should produce equivalent data."""
        yaml_out = canvas_to_yaml(hierarchical_canvas)
        canvas2 = parse_yaml(yaml_out)
        assert canvas2.title == hierarchical_canvas.title
        assert len(canvas2.all_nodes()) == len(hierarchical_canvas.all_nodes())
        orig_ids = {n.id for n in hierarchical_canvas.all_nodes()}
        new_ids = {n.id for n in canvas2.all_nodes()}
        assert orig_ids == new_ids

    def test_round_trip_preserves_types(self, hierarchical_canvas):
        """Serialization round-trip should preserve node types."""
        yaml_out = canvas_to_yaml(hierarchical_canvas)
        canvas2 = parse_yaml(yaml_out)
        orig_map = {n.id: n.type for n in hierarchical_canvas.all_nodes()}
        new_map = {n.id: n.type for n in canvas2.all_nodes()}
        assert orig_map == new_map

    def test_round_trip_preserves_connections(self, hierarchical_canvas):
        """Serialization round-trip should preserve connections."""
        yaml_out = canvas_to_yaml(hierarchical_canvas)
        canvas2 = parse_yaml(yaml_out)
        orig_conns = set(hierarchical_canvas.all_connections())
        new_conns = set(canvas2.all_connections())
        assert orig_conns == new_conns

    def test_serialization_output_is_valid_yaml(self, simple_canvas):
        """canvas_to_yaml should produce valid YAML."""
        yaml_out = canvas_to_yaml(simple_canvas)
        data = yaml.safe_load(yaml_out)
        assert isinstance(data, dict)
        assert "canvas" in data
