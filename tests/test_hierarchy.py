"""Tests for hierarchical format — networks/factories/machines parse and render."""

import pytest

from canvas_mcp.models import (
    Canvas,
    CanvasFactory,
    CanvasMachine,
    CanvasNetwork,
    CanvasNode,
    ContainerStyle,
)
from canvas_mcp.parser import parse_yaml, canvas_to_yaml
from canvas_mcp.renderer import CanvasRenderer
from canvas_mcp.organize import organize_canvas


# ===================================================================
# Hierarchical structure parsing
# ===================================================================

class TestHierarchyParsing:
    """Test parsing of the full hierarchical YAML format."""

    def test_single_network(self, hierarchical_canvas):
        """Single network should parse correctly."""
        assert len(hierarchical_canvas.networks) == 1
        net = hierarchical_canvas.networks[0]
        assert net.id == "net-1"
        assert net.get_label() == "Test Network"

    def test_factory_within_network(self, hierarchical_canvas):
        """Factory should be nested within its network."""
        factory = hierarchical_canvas.networks[0].factories[0]
        assert factory.id == "fac-1"
        assert factory.get_label() == "Factory One"

    def test_machines_within_factory(self, hierarchical_canvas):
        """Machines should be nested within their factory."""
        machines = hierarchical_canvas.networks[0].factories[0].machines
        assert len(machines) == 2
        assert machines[0].id == "mach-1"
        assert machines[1].id == "mach-2"

    def test_nodes_within_machines(self, hierarchical_canvas):
        """Nodes should be nested within their machines."""
        machines = hierarchical_canvas.networks[0].factories[0].machines
        m1_node_ids = [n.id for n in machines[0].nodes]
        m2_node_ids = [n.id for n in machines[1].nodes]
        assert "a" in m1_node_ids
        assert "b" in m1_node_ids
        assert "c" in m2_node_ids
        assert "d" in m2_node_ids

    def test_cross_machine_connections(self, hierarchical_canvas):
        """Connections across machines should be tracked."""
        conns = set(hierarchical_canvas.all_connections())
        # b→c is a cross-machine connection (b in mach-1, c in mach-2)
        assert ("b", "c") in conns

    def test_multi_network(self):
        """Multiple networks should parse correctly."""
        yaml_str = """\
canvas:
  title: Multi Network
  networks:
    - id: net-a
      label: Network A
      factories:
        - id: fac-a
          machines:
            - id: mach-a
              nodes:
                - id: node-a
                  type: input
                  content: "In network A"
    - id: net-b
      label: Network B
      factories:
        - id: fac-b
          machines:
            - id: mach-b
              nodes:
                - id: node-b
                  type: output
                  content: "In network B"
"""
        canvas = parse_yaml(yaml_str)
        assert len(canvas.networks) == 2
        assert canvas.networks[0].id == "net-a"
        assert canvas.networks[1].id == "net-b"
        assert len(canvas.all_nodes()) == 2

    def test_cross_network_connections(self):
        """Connections across networks should work."""
        yaml_str = """\
canvas:
  title: Cross Network
  networks:
    - id: net-1
      factories:
        - id: fac-1
          machines:
            - id: mach-1
              nodes:
                - id: src
                  type: input
                  content: "Source"
                  outputs: [dst]
    - id: net-2
      factories:
        - id: fac-2
          machines:
            - id: mach-2
              nodes:
                - id: dst
                  type: output
                  content: "Destination"
                  inputs: [src]
"""
        canvas = parse_yaml(yaml_str)
        conns = set(canvas.all_connections())
        assert ("src", "dst") in conns

    def test_empty_machine(self):
        """An empty machine (no nodes) should not crash."""
        yaml_str = """\
canvas:
  title: Empty Machine
  networks:
    - id: net
      factories:
        - id: fac
          machines:
            - id: empty-machine
              nodes: []
            - id: has-nodes
              nodes:
                - id: n1
                  type: default
                  content: "test"
"""
        canvas = parse_yaml(yaml_str)
        assert len(canvas.all_nodes()) == 1

    def test_empty_factory(self):
        """An empty factory (no machines) should not crash."""
        yaml_str = """\
canvas:
  title: Empty Factory
  networks:
    - id: net
      factories:
        - id: empty-factory
          machines: []
        - id: has-machines
          machines:
            - id: m1
              nodes:
                - id: n1
                  type: default
                  content: "test"
"""
        canvas = parse_yaml(yaml_str)
        assert len(canvas.all_nodes()) == 1

    def test_empty_network(self):
        """An empty network (no factories) should not crash."""
        yaml_str = """\
canvas:
  title: Empty Network
  networks:
    - id: empty-net
      factories: []
    - id: has-factories
      factories:
        - id: f1
          machines:
            - id: m1
              nodes:
                - id: n1
                  type: default
                  content: "test"
"""
        canvas = parse_yaml(yaml_str)
        assert len(canvas.all_nodes()) == 1

    def test_get_label_fallback(self):
        """Entities without labels should use their id."""
        yaml_str = """\
canvas:
  title: Label Test
  networks:
    - id: my-network
      factories:
        - id: my-factory
          machines:
            - id: my-machine
              nodes:
                - id: my-node
                  type: default
                  content: "test"
"""
        canvas = parse_yaml(yaml_str)
        net = canvas.networks[0]
        fac = net.factories[0]
        mach = fac.machines[0]

        assert net.get_label() == "my-network"
        assert fac.get_label() == "my-factory"
        assert mach.get_label() == "my-machine"


# ===================================================================
# Hierarchical rendering
# ===================================================================

class TestHierarchyRendering:
    """Test rendering of hierarchical canvases."""

    @pytest.fixture
    def renderer(self):
        return CanvasRenderer(scale=1.0)

    def test_hierarchical_renders(self, renderer, hierarchical_canvas):
        """A hierarchical canvas should render without error."""
        png_bytes = renderer.render(hierarchical_canvas)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"

    def test_hierarchical_with_organize(self, renderer, hierarchical_canvas):
        """Hierarchical canvas should render with organize enabled."""
        png_bytes = renderer.render(hierarchical_canvas, organize=True)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"

    def test_multi_factory_renders(self, renderer, multi_factory_canvas):
        """Multi-factory canvas should render without error."""
        png_bytes = renderer.render(multi_factory_canvas, organize=True)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"

    def test_multi_network_renders(self, renderer):
        """Multi-network canvas should render without error."""
        yaml_str = """\
canvas:
  title: Multi Net Render
  networks:
    - id: net-1
      factories:
        - id: f1
          machines:
            - id: m1
              nodes:
                - id: a
                  type: input
                  content: "A"
                  outputs: [c]
    - id: net-2
      factories:
        - id: f2
          machines:
            - id: m2
              nodes:
                - id: b
                  type: process
                  content: "B"
                - id: c
                  type: output
                  content: "C"
                  inputs: [a, b]
"""
        canvas = parse_yaml(yaml_str)
        png_bytes = renderer.render(canvas, organize=True)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"

    def test_empty_canvas_renders(self, renderer):
        """A canvas with no nodes should still produce a valid PNG."""
        yaml_str = """\
canvas:
  title: Empty Canvas
  networks: []
"""
        canvas = parse_yaml(yaml_str)
        png_bytes = renderer.render(canvas)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"

    def test_styled_factory_renders(self, renderer):
        """Factory with custom container style should render."""
        yaml_str = """\
canvas:
  title: Styled Factory
  networks:
    - id: net
      factories:
        - id: fac
          label: "Styled Factory"
          style:
            border_color: "#ff0000"
            fill_color: "#330000"
            alpha: 80
            label_color: "#ff5555"
          machines:
            - id: m1
              nodes:
                - id: n1
                  type: input
                  content: "test"
"""
        canvas = parse_yaml(yaml_str)
        png_bytes = renderer.render(canvas, organize=True)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"

    def test_styled_machine_renders(self, renderer):
        """Machine with custom container style should render."""
        yaml_str = """\
canvas:
  title: Styled Machine
  networks:
    - id: net
      factories:
        - id: fac
          machines:
            - id: m1
              label: "Custom Machine"
              style:
                fill_color: "#003300"
                border_color: "#00ff00"
                alpha: 150
                corner_radius: 20
                border_width: 3
              nodes:
                - id: n1
                  type: process
                  content: "test"
"""
        canvas = parse_yaml(yaml_str)
        png_bytes = renderer.render(canvas, organize=True)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"


# ===================================================================
# Hierarchical organize
# ===================================================================

class TestHierarchyOrganize:
    """Test the organize algorithm on hierarchical canvases."""

    def test_organize_separates_machines(self):
        """Machines within a factory should be separated after organize."""
        m1_node = CanvasNode(id="m1-a", type="input", content="A")
        m2_node = CanvasNode(id="m2-a", type="output", content="B")
        machine1 = CanvasMachine(id="m1", nodes=[m1_node])
        machine2 = CanvasMachine(id="m2", nodes=[m2_node])
        factory = CanvasFactory(id="f", machines=[machine1, machine2])
        network = CanvasNetwork(id="n", factories=[factory])
        canvas = Canvas(title="Sep Test", networks=[network])
        canvas.model_post_init(None)

        renderer = CanvasRenderer(scale=1.0)
        renderer.auto_size_nodes(canvas)
        organize_canvas(canvas)

        # The two nodes should not overlap
        n1, n2 = m1_node, m2_node
        no_overlap = (
            n1.x + n1.width <= n2.x or
            n2.x + n2.width <= n1.x or
            n1.y + n1.height <= n2.y or
            n2.y + n2.height <= n1.y
        )
        assert no_overlap, f"Nodes overlap: {n1.id} at ({n1.x},{n1.y}) vs {n2.id} at ({n2.x},{n2.y})"

    def test_organize_multi_factory_flow(self):
        """Multi-factory with cross-factory connections should maintain flow order."""
        # factory-1 has src, factory-2 has proc, factory-3 has out
        # src → proc → out (cross-factory flow)
        src = CanvasNode(id="src", type="source", content="Source", outputs=["proc"])
        proc = CanvasNode(id="proc", type="process", content="Process", inputs=["src"], outputs=["out"])
        out = CanvasNode(id="out", type="output", content="Output", inputs=["proc"])

        f1 = CanvasFactory(id="f1", machines=[CanvasMachine(id="m1", nodes=[src])])
        f2 = CanvasFactory(id="f2", machines=[CanvasMachine(id="m2", nodes=[proc])])
        f3 = CanvasFactory(id="f3", machines=[CanvasMachine(id="m3", nodes=[out])])

        network = CanvasNetwork(id="net", factories=[f1, f2, f3])
        canvas = Canvas(title="Flow", networks=[network])
        canvas.model_post_init(None)

        renderer = CanvasRenderer(scale=1.0)
        renderer.auto_size_nodes(canvas)
        organize_canvas(canvas, orientation="horizontal")

        # In horizontal mode: src.x < proc.x < out.x
        assert src.x < proc.x, f"src.x={src.x} should be < proc.x={proc.x}"
        assert proc.x < out.x, f"proc.x={proc.x} should be < out.x={out.x}"

    def test_organize_complex_hierarchy(self, renderer):
        """A complex hierarchy (like the Rhode architecture test) should render."""
        # Build a mini version of the Rhode architecture
        tg = CanvasNode(id="tg", type="input", content="Telegram", outputs=["tq"])
        bm = CanvasNode(id="bm", type="input", content="Bus Monitor", outputs=["tq"])
        tq = CanvasNode(id="tq", type="process", content="Task Queue", inputs=["tg", "bm"], outputs=["agent"])
        ingestion = CanvasMachine(id="ingestion", nodes=[tg, bm, tq])

        agent = CanvasNode(id="agent", type="ai", content="Agent", inputs=["tq", "mem"])
        mem = CanvasNode(id="mem", type="static", content="Memory", outputs=["agent"])
        processing = CanvasMachine(id="processing", nodes=[agent])
        memory = CanvasMachine(id="memory", nodes=[mem])

        tool = CanvasNode(id="tool", type="source", content="Tools", inputs=["agent"], outputs=["out"])
        out = CanvasNode(id="out", type="output", content="Output", inputs=["tool"])
        tools = CanvasMachine(id="tools", nodes=[tool])
        outputs = CanvasMachine(id="outputs", nodes=[out])

        f1 = CanvasFactory(id="ingestion-f", label="Ingestion", machines=[ingestion])
        f2 = CanvasFactory(id="core-f", label="Core", machines=[processing, memory])
        f3 = CanvasFactory(id="output-f", label="Output", machines=[tools, outputs])

        network = CanvasNetwork(id="system", label="System", factories=[f1, f2, f3])
        canvas = Canvas(title="Complex Hierarchy", networks=[network])
        canvas.model_post_init(None)

        png_bytes = renderer.render(canvas, organize=True)
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"
        assert len(png_bytes) > 100

    @pytest.mark.parametrize("orientation", ["horizontal", "vertical"])
    def test_hierarchical_both_orientations(self, renderer, hierarchical_canvas, orientation):
        """Hierarchical canvas should render in both orientations."""
        png_bytes = renderer.render(
            hierarchical_canvas,
            organize=True,
            orientation=orientation,
        )
        assert isinstance(png_bytes, bytes)
        assert png_bytes[:4] == b"\x89PNG"


# ===================================================================
# Serialization of hierarchical canvases
# ===================================================================

class TestHierarchySerialization:
    """Test round-trip serialization of hierarchical canvases."""

    def test_round_trip_structure(self, hierarchical_canvas):
        """Serialization should preserve the full hierarchy structure."""
        yaml_out = canvas_to_yaml(hierarchical_canvas)
        canvas2 = parse_yaml(yaml_out)

        assert len(canvas2.networks) == len(hierarchical_canvas.networks)
        for net_orig, net_new in zip(hierarchical_canvas.networks, canvas2.networks):
            assert net_orig.id == net_new.id
            assert len(net_orig.factories) == len(net_new.factories)
            for fac_orig, fac_new in zip(net_orig.factories, net_new.factories):
                assert fac_orig.id == fac_new.id
                assert len(fac_orig.machines) == len(fac_new.machines)
                for mach_orig, mach_new in zip(fac_orig.machines, fac_new.machines):
                    assert mach_orig.id == mach_new.id
                    assert len(mach_orig.nodes) == len(mach_new.nodes)

    def test_round_trip_labels(self, hierarchical_canvas):
        """Labels should survive serialization round-trip."""
        yaml_out = canvas_to_yaml(hierarchical_canvas)
        canvas2 = parse_yaml(yaml_out)
        net = canvas2.networks[0]
        assert net.label == "Test Network"
        fac = net.factories[0]
        assert fac.label == "Factory One"

    def test_round_trip_factory_style(self):
        """Factory container styles should survive serialization round-trip."""
        yaml_str = """\
canvas:
  title: Style Roundtrip
  networks:
    - id: net
      factories:
        - id: fac
          style:
            border_color: "#ff0000"
            label_color: "#00ff00"
          machines:
            - id: m
              nodes:
                - id: n
                  type: default
                  content: "test"
"""
        canvas = parse_yaml(yaml_str)
        yaml_out = canvas_to_yaml(canvas)
        canvas2 = parse_yaml(yaml_out)
        fac = canvas2.networks[0].factories[0]
        assert fac.style is not None
        assert fac.style.border_color == "#ff0000"
        assert fac.style.label_color == "#00ff00"
