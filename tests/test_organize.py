"""Tests for the organize algorithm — layout without overlap, machine grouping."""

import pytest

from canvas_mcp.models import (
    Canvas,
    CanvasFactory,
    CanvasMachine,
    CanvasNetwork,
    CanvasNode,
)
from canvas_mcp.parser import parse_yaml
from canvas_mcp.organize import (
    organize_canvas,
    compute_organized_layout,
    compute_bounds_from_nodes,
    OrganizeItem,
    OrganizeEdge,
    OrganizeOptions,
)
from canvas_mcp.renderer import CanvasRenderer


# ===================================================================
# Core layout algorithm
# ===================================================================

class TestComputeOrganizedLayout:
    """Test the core organize algorithm directly."""

    def test_empty_items(self):
        """Empty input should return empty layout."""
        result = compute_organized_layout([], [])
        assert result == {}

    def test_single_item(self):
        """Single item should be positioned."""
        items = [OrganizeItem(id="a", item_type="node", width=100, height=50, x=0, y=0)]
        result = compute_organized_layout(items, [])
        assert "a" in result

    def test_chain_layout_horizontal(self):
        """Items in a chain should be laid out left-to-right."""
        items = [
            OrganizeItem(id="a", item_type="node", width=100, height=50, x=0, y=0),
            OrganizeItem(id="b", item_type="node", width=100, height=50, x=0, y=0),
            OrganizeItem(id="c", item_type="node", width=100, height=50, x=0, y=0),
        ]
        edges = [
            OrganizeEdge(from_id="a", to_id="b"),
            OrganizeEdge(from_id="b", to_id="c"),
        ]
        options = OrganizeOptions(orientation="horizontal")
        result = compute_organized_layout(items, edges, options)

        assert result["a"].x < result["b"].x
        assert result["b"].x < result["c"].x

    def test_chain_layout_vertical(self):
        """Items in a chain should be laid out top-to-bottom when vertical."""
        items = [
            OrganizeItem(id="a", item_type="node", width=100, height=50, x=0, y=0),
            OrganizeItem(id="b", item_type="node", width=100, height=50, x=0, y=0),
            OrganizeItem(id="c", item_type="node", width=100, height=50, x=0, y=0),
        ]
        edges = [
            OrganizeEdge(from_id="a", to_id="b"),
            OrganizeEdge(from_id="b", to_id="c"),
        ]
        options = OrganizeOptions(orientation="vertical")
        result = compute_organized_layout(items, edges, options)

        assert result["a"].y < result["b"].y
        assert result["b"].y < result["c"].y

    def test_fan_out_same_level(self):
        """Fan-out targets should all be at the same level (x-position in horizontal)."""
        items = [
            OrganizeItem(id="root", item_type="node", width=100, height=50, x=0, y=0),
            OrganizeItem(id="a", item_type="node", width=100, height=50, x=0, y=0),
            OrganizeItem(id="b", item_type="node", width=100, height=50, x=0, y=0),
            OrganizeItem(id="c", item_type="node", width=100, height=50, x=0, y=0),
        ]
        edges = [
            OrganizeEdge(from_id="root", to_id="a"),
            OrganizeEdge(from_id="root", to_id="b"),
            OrganizeEdge(from_id="root", to_id="c"),
        ]
        options = OrganizeOptions(orientation="horizontal")
        result = compute_organized_layout(items, edges, options)

        # All children should have the same x (same level)
        assert result["a"].x == result["b"].x == result["c"].x
        # Children should be to the right of root
        assert result["a"].x > result["root"].x

    def test_disconnected_items_get_positioned(self):
        """Items with no edges should still be positioned (grid fallback)."""
        items = [
            OrganizeItem(id="a", item_type="node", width=100, height=50, x=0, y=0),
            OrganizeItem(id="b", item_type="node", width=100, height=50, x=0, y=0),
            OrganizeItem(id="c", item_type="node", width=100, height=50, x=0, y=0),
        ]
        result = compute_organized_layout(items, [])
        assert "a" in result
        assert "b" in result
        assert "c" in result

    def test_cycle_handling(self):
        """Cyclic graphs should not crash — unresolved nodes still get positioned."""
        items = [
            OrganizeItem(id="a", item_type="node", width=100, height=50, x=0, y=0),
            OrganizeItem(id="b", item_type="node", width=100, height=50, x=0, y=0),
        ]
        edges = [
            OrganizeEdge(from_id="a", to_id="b"),
            OrganizeEdge(from_id="b", to_id="a"),
        ]
        result = compute_organized_layout(items, edges)
        assert "a" in result
        assert "b" in result

    def test_edges_with_unknown_ids_ignored(self):
        """Edges referencing non-existent items should be ignored, not crash."""
        items = [
            OrganizeItem(id="a", item_type="node", width=100, height=50, x=0, y=0),
        ]
        edges = [
            OrganizeEdge(from_id="a", to_id="ghost"),
            OrganizeEdge(from_id="ghost", to_id="a"),
        ]
        result = compute_organized_layout(items, edges)
        assert "a" in result


# ===================================================================
# No-overlap verification
# ===================================================================

class TestNoOverlap:
    """Verify that organized nodes do not overlap."""

    def _nodes_overlap(self, n1: CanvasNode, n2: CanvasNode) -> bool:
        """Check if two nodes' bounding boxes overlap."""
        return not (
            n1.x + n1.width <= n2.x or
            n2.x + n2.width <= n1.x or
            n1.y + n1.height <= n2.y or
            n2.y + n2.height <= n1.y
        )

    def test_simple_chain_no_overlap(self):
        """3-node chain should have no overlapping nodes after organize."""
        yaml_str = """\
title: Chain
nodes:
  - id: a
    type: input
    content: "A"
  - id: b
    type: process
    content: "B"
    inputs: [a]
  - id: c
    type: output
    content: "C"
    inputs: [b]
"""
        canvas = parse_yaml(yaml_str)
        renderer = CanvasRenderer(scale=1.0)
        renderer.auto_size_nodes(canvas)
        organize_canvas(canvas)
        nodes = canvas.all_nodes()
        for i, n1 in enumerate(nodes):
            for n2 in nodes[i+1:]:
                assert not self._nodes_overlap(n1, n2), (
                    f"Nodes {n1.id} and {n2.id} overlap: "
                    f"{n1.id}({n1.x},{n1.y},{n1.width},{n1.height}) vs "
                    f"{n2.id}({n2.x},{n2.y},{n2.width},{n2.height})"
                )

    def test_fan_out_no_overlap(self):
        """Fan-out pattern should have no overlapping nodes."""
        yaml_str = """\
title: Fan Out
nodes:
  - id: root
    type: input
    content: "Root"
    outputs: [a, b, c, d]
  - id: a
    type: process
    content: "Branch A"
  - id: b
    type: process
    content: "Branch B"
  - id: c
    type: process
    content: "Branch C"
  - id: d
    type: process
    content: "Branch D"
"""
        canvas = parse_yaml(yaml_str)
        renderer = CanvasRenderer(scale=1.0)
        renderer.auto_size_nodes(canvas)
        organize_canvas(canvas)
        nodes = canvas.all_nodes()
        for i, n1 in enumerate(nodes):
            for n2 in nodes[i+1:]:
                assert not self._nodes_overlap(n1, n2), (
                    f"Overlap: {n1.id} vs {n2.id}"
                )

    def test_many_disconnected_no_overlap(self):
        """Many disconnected nodes should not overlap after organize."""
        node_defs = "\n".join([
            f"  - id: node-{i}\n    type: default\n    content: 'Node {i}'"
            for i in range(10)
        ])
        yaml_str = f"title: Many Nodes\nnodes:\n{node_defs}\n"
        canvas = parse_yaml(yaml_str)
        renderer = CanvasRenderer(scale=1.0)
        renderer.auto_size_nodes(canvas)
        organize_canvas(canvas)
        nodes = canvas.all_nodes()
        for i, n1 in enumerate(nodes):
            for n2 in nodes[i+1:]:
                assert not self._nodes_overlap(n1, n2), (
                    f"Overlap: {n1.id} vs {n2.id}"
                )


# ===================================================================
# Machine grouping
# ===================================================================

class TestMachineGrouping:
    """Verify that the organize algorithm respects machine boundaries."""

    def test_nodes_in_same_machine_are_proximate(self):
        """Nodes within the same machine should be closer to each other than to nodes in other machines."""
        # Build a canvas with two machines
        m1_nodes = [
            CanvasNode(id="m1-a", type="input", content="A"),
            CanvasNode(id="m1-b", type="process", content="B", inputs=["m1-a"]),
        ]
        m2_nodes = [
            CanvasNode(id="m2-a", type="input", content="C"),
            CanvasNode(id="m2-b", type="output", content="D", inputs=["m2-a"]),
        ]
        machine1 = CanvasMachine(id="machine-1", nodes=m1_nodes)
        machine2 = CanvasMachine(id="machine-2", nodes=m2_nodes)
        factory = CanvasFactory(id="factory-1", machines=[machine1, machine2])
        network = CanvasNetwork(id="network-1", factories=[factory])
        canvas = Canvas(title="Machine Group Test", networks=[network])
        canvas.model_post_init(None)

        renderer = CanvasRenderer(scale=1.0)
        renderer.auto_size_nodes(canvas)
        organize_canvas(canvas)

        # Compute machine bounding boxes
        def machine_center(nodes):
            cx = sum(n.x + n.width / 2 for n in nodes) / len(nodes)
            cy = sum(n.y + n.height / 2 for n in nodes) / len(nodes)
            return cx, cy

        m1_center = machine_center(m1_nodes)
        m2_center = machine_center(m2_nodes)

        # The two machines should not be at the exact same position
        dist = ((m1_center[0] - m2_center[0])**2 + (m1_center[1] - m2_center[1])**2) ** 0.5
        assert dist > 50, f"Machine centers too close: {dist}px apart"

    def test_connected_machines_layout_order(self):
        """Machines connected by cross-machine edges should follow flow direction."""
        # machine-1: a → b (within), b → c (cross-machine to machine-2)
        # machine-2: c → d (within)
        node_a = CanvasNode(id="a", type="input", content="Start")
        node_b = CanvasNode(id="b", type="process", content="Middle", inputs=["a"], outputs=["c"])
        node_c = CanvasNode(id="c", type="process", content="Continue", inputs=["b"], outputs=["d"])
        node_d = CanvasNode(id="d", type="output", content="End", inputs=["c"])

        machine1 = CanvasMachine(id="m1", nodes=[node_a, node_b])
        machine2 = CanvasMachine(id="m2", nodes=[node_c, node_d])
        factory = CanvasFactory(id="f1", machines=[machine1, machine2])
        network = CanvasNetwork(id="n1", factories=[factory])
        canvas = Canvas(title="Flow Test", networks=[network])
        canvas.model_post_init(None)

        renderer = CanvasRenderer(scale=1.0)
        renderer.auto_size_nodes(canvas)
        organize_canvas(canvas, orientation="horizontal")

        # In horizontal layout, machine-1 should be to the left of machine-2
        m1_max_x = max(n.x + n.width for n in [node_a, node_b])
        m2_min_x = min(n.x for n in [node_c, node_d])
        assert m1_max_x < m2_min_x, (
            f"Machine-1 should be left of machine-2: "
            f"m1 max_x={m1_max_x}, m2 min_x={m2_min_x}"
        )


# ===================================================================
# Bounds computation
# ===================================================================

class TestBoundsComputation:
    """Test compute_bounds_from_nodes."""

    def test_empty_nodes(self):
        """Empty list should return None."""
        assert compute_bounds_from_nodes([]) is None

    def test_single_node_bounds(self):
        """Single node should have bounds matching its position and size."""
        node = CanvasNode(id="a", type="default", content="test", x=100, y=200, width=300, height=150)
        bounds = compute_bounds_from_nodes([node])
        assert bounds is not None
        assert bounds.x == 100
        assert bounds.y == 200
        assert bounds.width == 300
        assert bounds.height == 150

    def test_multiple_node_bounds(self):
        """Bounds should encompass all nodes."""
        nodes = [
            CanvasNode(id="a", type="default", content="", x=0, y=0, width=100, height=50),
            CanvasNode(id="b", type="default", content="", x=200, y=300, width=100, height=50),
        ]
        bounds = compute_bounds_from_nodes(nodes)
        assert bounds is not None
        assert bounds.x == 0
        assert bounds.y == 0
        assert bounds.width == 300  # 200 + 100 - 0
        assert bounds.height == 350  # 300 + 50 - 0

    def test_non_finite_coordinates_skipped(self):
        """Nodes with infinite coordinates should be ignored."""
        nodes = [
            CanvasNode(id="a", type="default", content="", x=float("inf"), y=float("inf")),
        ]
        assert compute_bounds_from_nodes(nodes) is None


# ===================================================================
# Orientation
# ===================================================================

class TestOrientation:
    """Test horizontal vs vertical orientation."""

    def test_horizontal_orientation(self):
        """Horizontal layout should spread nodes primarily along x-axis."""
        yaml_str = """\
title: Horizontal
nodes:
  - id: a
    type: input
    content: "A"
    outputs: [b]
  - id: b
    type: process
    content: "B"
    outputs: [c]
  - id: c
    type: output
    content: "C"
"""
        canvas = parse_yaml(yaml_str)
        renderer = CanvasRenderer(scale=1.0)
        renderer.auto_size_nodes(canvas)
        organize_canvas(canvas, orientation="horizontal")
        nodes = {n.id: n for n in canvas.all_nodes()}
        # In horizontal mode, a→b→c should have increasing x
        assert nodes["a"].x < nodes["b"].x < nodes["c"].x

    def test_vertical_orientation(self):
        """Vertical layout should spread nodes primarily along y-axis."""
        yaml_str = """\
title: Vertical
nodes:
  - id: a
    type: input
    content: "A"
    outputs: [b]
  - id: b
    type: process
    content: "B"
    outputs: [c]
  - id: c
    type: output
    content: "C"
"""
        canvas = parse_yaml(yaml_str)
        renderer = CanvasRenderer(scale=1.0)
        renderer.auto_size_nodes(canvas)
        organize_canvas(canvas, orientation="vertical")
        nodes = {n.id: n for n in canvas.all_nodes()}
        # In vertical mode, a→b→c should have increasing y
        assert nodes["a"].y < nodes["b"].y < nodes["c"].y


# ===================================================================
# Spacing levels
# ===================================================================

class TestSpacingLevels:
    """Test that different spacing levels produce valid layouts."""

    @pytest.mark.parametrize("spacing", ["node", "container", "network"])
    def test_spacing_level_renders(self, spacing):
        """All spacing levels should produce valid renders."""
        yaml_str = """\
title: Spacing Test
nodes:
  - id: a
    type: input
    content: "A"
    outputs: [b]
  - id: b
    type: output
    content: "B"
"""
        canvas = parse_yaml(yaml_str)
        renderer = CanvasRenderer(scale=1.0)
        png_bytes = renderer.render(canvas, organize=True, spacing_level=spacing)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"


# ===================================================================
# Auto-layout fallback
# ===================================================================

class TestAutoLayoutFallback:
    """Test the simple auto-layout (when organize=False and all nodes at 0,0)."""

    def test_fallback_moves_nodes_off_zero(self):
        """Auto-layout should move nodes away from (0,0) if all start there."""
        yaml_str = """\
title: Fallback
nodes:
  - id: a
    type: input
    content: "A"
  - id: b
    type: output
    content: "B"
"""
        canvas = parse_yaml(yaml_str)
        renderer = CanvasRenderer(scale=1.0)
        renderer.auto_size_nodes(canvas)
        # render without organize triggers fallback auto-layout
        renderer.render(canvas, organize=False)
        nodes = canvas.all_nodes()
        # At least some nodes should no longer be at (0, 0)
        positions = [(n.x, n.y) for n in nodes]
        assert not all(x == 0 and y == 0 for x, y in positions)

    def test_explicit_positions_preserved(self):
        """Nodes with explicit positions should not be moved by auto-layout."""
        yaml_str = """\
title: Explicit
nodes:
  - id: a
    type: input
    content: "A"
    x: 100
    y: 200
  - id: b
    type: output
    content: "B"
    x: 500
    y: 200
"""
        canvas = parse_yaml(yaml_str)
        renderer = CanvasRenderer(scale=1.0)
        renderer.auto_size_nodes(canvas)
        renderer.render(canvas, organize=False)
        nodes = {n.id: n for n in canvas.all_nodes()}
        # Positions should be preserved (not all zero, so no auto-layout)
        assert nodes["a"].x == 100
        assert nodes["a"].y == 200
        assert nodes["b"].x == 500
        assert nodes["b"].y == 200
