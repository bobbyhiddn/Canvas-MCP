"""Data models for Canvas-MCP, inspired by Thoughtorio's ontology."""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class NodeStyle(BaseModel):
    """Visual styling for a node."""
    border_color: str = "#999"
    fill_color: str = "#1e1e2e"
    text_color: str = "#cdd6f4"
    label_color: Optional[str] = None
    icon: str = ""
    corner_radius: int = 12


# Default styles per node type (Thoughtorio color scheme)
NODE_STYLES: dict[str, NodeStyle] = {
    "static": NodeStyle(border_color="#4CAF50", icon="", fill_color="#1e1e2e"),
    "input": NodeStyle(border_color="#2196F3", icon="", fill_color="#1e1e2e"),
    "ai": NodeStyle(border_color="#9C27B0", icon="", fill_color="#1e1e2e"),
    "source": NodeStyle(border_color="#FF9800", icon="", fill_color="#1e1e2e"),
    "output": NodeStyle(border_color="#FFC107", icon="", fill_color="#1e1e2e"),
    "decision": NodeStyle(border_color="#F44336", icon="", fill_color="#1e1e2e"),
    "process": NodeStyle(border_color="#00BCD4", icon="", fill_color="#1e1e2e"),
    "default": NodeStyle(border_color="#999", icon="", fill_color="#1e1e2e"),
}


class CanvasNode(BaseModel):
    """A node on the canvas."""
    id: str
    type: str = "default"
    content: str = ""
    label: Optional[str] = None
    x: float = 0.0
    y: float = 0.0
    width: float = 250.0
    height: float = 120.0
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    style: Optional[NodeStyle] = None

    def get_style(self) -> NodeStyle:
        """Get the effective style for this node."""
        if self.style:
            return self.style
        return NODE_STYLES.get(self.type, NODE_STYLES["default"])

    def get_label(self) -> str:
        """Get display label for the node."""
        if self.label:
            return self.label
        return self.id


class CanvasMachine(BaseModel):
    """A machine (connected component of nodes)."""
    id: str
    label: Optional[str] = None
    nodes: list[CanvasNode] = Field(default_factory=list)
    style: Optional[NodeStyle] = None


class CanvasFactory(BaseModel):
    """A factory (connected component of machines)."""
    id: str
    label: Optional[str] = None
    machines: list[CanvasMachine] = Field(default_factory=list)
    style: Optional[NodeStyle] = None


class CanvasNetwork(BaseModel):
    """A network (connected component of factories)."""
    id: str
    label: Optional[str] = None
    factories: list[CanvasFactory] = Field(default_factory=list)


class Canvas(BaseModel):
    """Top-level canvas model."""
    version: str = "2.0"
    title: str = "Untitled Canvas"
    width: int = 1920
    height: int = 1080
    background_color: str = "#11111b"
    networks: list[CanvasNetwork] = Field(default_factory=list)

    # Flat access helpers
    _node_map: dict[str, CanvasNode] = {}

    def model_post_init(self, __context):
        """Build lookup maps after initialization."""
        self._node_map = {}
        for network in self.networks:
            for factory in network.factories:
                for machine in factory.machines:
                    for node in machine.nodes:
                        self._node_map[node.id] = node

    def get_node(self, node_id: str) -> Optional[CanvasNode]:
        return self._node_map.get(node_id)

    def all_nodes(self) -> list[CanvasNode]:
        nodes = []
        for network in self.networks:
            for factory in network.factories:
                for machine in factory.machines:
                    nodes.extend(machine.nodes)
        return nodes

    def all_connections(self) -> list[tuple[str, str]]:
        """Return all (source_id, target_id) connections."""
        connections = []
        for node in self.all_nodes():
            for input_id in node.inputs:
                connections.append((input_id, node.id))
            for output_id in node.outputs:
                connections.append((node.id, output_id))
        # Deduplicate
        return list(set(connections))
