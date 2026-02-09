"""Shared fixtures for Canvas-MCP test suite."""

import pytest

from canvas_mcp.models import (
    Canvas,
    CanvasFactory,
    CanvasMachine,
    CanvasNetwork,
    CanvasNode,
    ContainerStyle,
    NodeStyle,
    NODE_STYLES,
)
from canvas_mcp.parser import parse_yaml
from canvas_mcp.renderer import CanvasRenderer


# ---------------------------------------------------------------------------
# YAML recipe fixtures
# ---------------------------------------------------------------------------

SIMPLE_RECIPE = """\
title: Simple Test
nodes:
  - id: start
    type: input
    content: "Begin here"
  - id: process
    type: process
    content: "Do work"
    inputs: [start]
  - id: end
    type: output
    content: "Done"
    inputs: [process]
"""

HIERARCHICAL_RECIPE = """\
canvas:
  version: "2.0"
  title: Hierarchical Test
  networks:
    - id: net-1
      label: Test Network
      factories:
        - id: fac-1
          label: Factory One
          machines:
            - id: mach-1
              label: Machine One
              nodes:
                - id: a
                  type: input
                  content: "Node A"
                - id: b
                  type: process
                  content: "Node B"
                  inputs: [a]
            - id: mach-2
              label: Machine Two
              nodes:
                - id: c
                  type: ai
                  content: "Node C"
                  inputs: [b]
                - id: d
                  type: output
                  content: "Node D"
                  inputs: [c]
"""

MULTI_FACTORY_RECIPE = """\
canvas:
  version: "2.0"
  title: Multi-Factory Test
  networks:
    - id: net-1
      label: System
      factories:
        - id: fac-input
          label: Input Stage
          machines:
            - id: mach-in
              nodes:
                - id: src
                  type: source
                  content: "Data source"
                  outputs: [proc]
        - id: fac-process
          label: Processing Stage
          machines:
            - id: mach-proc
              nodes:
                - id: proc
                  type: process
                  content: "Process data"
                  inputs: [src]
                  outputs: [out]
        - id: fac-output
          label: Output Stage
          machines:
            - id: mach-out
              nodes:
                - id: out
                  type: output
                  content: "Final output"
                  inputs: [proc]
"""

ALL_NODE_TYPES_RECIPE = """\
title: All Node Types
nodes:
  - id: n-input
    type: input
    content: "Input node"
  - id: n-output
    type: output
    content: "Output node"
  - id: n-process
    type: process
    content: "Process node"
  - id: n-decision
    type: decision
    content: "Decision node"
  - id: n-ai
    type: ai
    content: "AI node"
  - id: n-source
    type: source
    content: "Source node"
  - id: n-static
    type: static
    content: "Static node"
  - id: n-default
    type: default
    content: "Default node"
"""


@pytest.fixture
def simple_canvas():
    """Parse and return a simple 3-node canvas."""
    return parse_yaml(SIMPLE_RECIPE)


@pytest.fixture
def hierarchical_canvas():
    """Parse and return a hierarchical canvas with machines/factories."""
    return parse_yaml(HIERARCHICAL_RECIPE)


@pytest.fixture
def multi_factory_canvas():
    """Parse and return a canvas with multiple factories."""
    return parse_yaml(MULTI_FACTORY_RECIPE)


@pytest.fixture
def all_types_canvas():
    """Parse and return a canvas with all 8 node types."""
    return parse_yaml(ALL_NODE_TYPES_RECIPE)


@pytest.fixture
def renderer():
    """Create a CanvasRenderer at 1x scale (faster for tests)."""
    return CanvasRenderer(scale=1.0)
