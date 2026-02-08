"""
Thoughtorio-style organize algorithm for Canvas-MCP.

Ported from Thoughtorio's organize.js — topological layout with intelligent
parent-child alignment, overlap prevention, and hierarchical spacing.

The key feature that distinguishes this from a flat layout is **hierarchical
application**: the organize algorithm runs at three levels:

  1. Machine level — nodes within each machine (tight spacing)
  2. Factory level — machines within each factory (medium spacing)
  3. Network level — factories within each network (spacious spacing)

At each level, child containers are treated as single items whose bounds
are computed from their contents. Connections between nodes in different
containers are resolved upward to container-level edges, so downstream
flow relationships inform the layout at every level of the hierarchy.

Spacing constants scaled up from Thoughtorio for larger, more legible nodes:
  - Nodes within machines: 90px horizontal, 140px vertical
  - Containers (machines/factories): 200px horizontal, 240px vertical
  - Networks: 260px horizontal, 320px vertical
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from .models import Canvas, CanvasNode, CanvasMachine, CanvasFactory, CanvasNetwork


# --- Spacing constants (from Thoughtorio) ---

NODE_HORIZONTAL_SPACING = 90
NODE_VERTICAL_SPACING = 140

CONTAINER_HORIZONTAL_SPACING = 200
CONTAINER_VERTICAL_SPACING = 240

NETWORK_HORIZONTAL_SPACING = 260  # CONTAINER + 60
NETWORK_VERTICAL_SPACING = 320    # CONTAINER + 80

# Internal padding for containers (space between container edge and first node)
MACHINE_PADDING = 55
FACTORY_PADDING = 75
NETWORK_PADDING = 100

GRID_COLUMNS_NODE = 4
GRID_COLUMNS_CONTAINER = 3


@dataclass
class OrganizeItem:
    """An item to be organized (node or container)."""
    id: str
    item_type: str  # 'node', 'machine', 'factory', 'network'
    width: float
    height: float
    x: float
    y: float
    node_ids: list[str] = field(default_factory=list)


@dataclass
class OrganizeEdge:
    """A directed edge between organize items."""
    from_id: str
    to_id: str


@dataclass
class OrganizeOptions:
    """Layout options matching Thoughtorio's OrganizeOptions."""
    orientation: str = "horizontal"  # 'horizontal' or 'vertical'
    horizontal_spacing: float = NODE_HORIZONTAL_SPACING
    vertical_spacing: float = NODE_VERTICAL_SPACING
    start_x: float = 0.0
    start_y: float = 0.0
    reference_center_x: float = 0.0
    reference_center_y: float = 0.0
    grid_columns: int = GRID_COLUMNS_NODE


@dataclass
class LayoutPosition:
    """Computed position for an item."""
    x: float
    y: float


@dataclass
class ContainerBounds:
    """Bounding box for a container, computed from its children."""
    x: float
    y: float
    width: float
    height: float


# ---------------------------------------------------------------------------
# Core layout algorithm (unchanged from Thoughtorio port)
# ---------------------------------------------------------------------------

def compute_organized_layout(
    items: list[OrganizeItem],
    edges: list[OrganizeEdge],
    options: Optional[OrganizeOptions] = None,
) -> dict[str, LayoutPosition]:
    """
    Core organize algorithm -- port of Thoughtorio's computeOrganizedLayout().

    Steps:
    1. Build adjacency and indegree maps
    2. Kahn's topological sort to assign levels
    3. Handle cycles (unresolved nodes)
    4. Normalize levels (compress gaps)
    5. Grid fallback for disconnected graphs
    6. Position items using parent-center alignment with overlap prevention
    """
    if not items:
        return {}

    opts = options or OrganizeOptions()
    item_map: dict[str, OrganizeItem] = {item.id: item for item in items}

    # --- Step 1: Build adjacency and indegree ---
    adjacency: dict[str, list[str]] = {item.id: [] for item in items}
    indegree: dict[str, int] = {item.id: 0 for item in items}

    for edge in edges:
        if edge.from_id in adjacency and edge.to_id in indegree:
            adjacency[edge.from_id].append(edge.to_id)
            indegree[edge.to_id] = indegree.get(edge.to_id, 0) + 1

    # --- Step 2: Kahn's topological sort ---
    levels: dict[str, int] = {}
    queue: list[str] = []

    # Sources sorted by position (top-left first)
    sorted_items = sorted(items, key=lambda it: (it.x, it.y))
    for item in sorted_items:
        if indegree.get(item.id, 0) == 0:
            levels[item.id] = 0
            queue.append(item.id)

    while queue:
        current = queue.pop(0)
        current_level = levels.get(current, 0)
        for target in adjacency.get(current, []):
            candidate = current_level + 1
            existing = levels.get(target)
            if existing is None or candidate > existing:
                levels[target] = candidate
            new_degree = indegree.get(target, 0) - 1
            indegree[target] = new_degree
            if new_degree == 0:
                queue.append(target)

    # --- Step 3: Handle unresolved (cyclic) nodes ---
    unresolved = [item for item in items if item.id not in levels]
    if unresolved:
        unresolved.sort(key=lambda it: (it.y, it.x))
        for item in unresolved:
            incoming_levels = [
                levels[e.from_id]
                for e in edges
                if e.to_id == item.id and e.from_id in levels
            ]
            if incoming_levels:
                levels[item.id] = max(incoming_levels) + 1
            else:
                levels[item.id] = 0

    # --- Step 4: Normalize levels (compress gaps) ---
    unique_levels = sorted(set(levels.values()))
    level_remap = {lvl: idx for idx, lvl in enumerate(unique_levels)}
    normalized: dict[str, int] = {
        item_id: level_remap.get(lvl, lvl)
        for item_id, lvl in levels.items()
    }

    effective_levels = normalized if normalized else dict(levels)

    # --- Step 5: Grid fallback for disconnected graphs ---
    total_edges = len(edges)
    orientation = opts.orientation

    if total_edges == 0 and len(items) > 1:
        grid_columns = opts.grid_columns
        ordered = sorted(items, key=lambda it: (it.y, it.x))
        for idx, item in enumerate(ordered):
            if orientation == "horizontal":
                col = idx // grid_columns
                effective_levels[item.id] = col
            else:
                row = idx // grid_columns
                effective_levels[item.id] = row

    # --- Step 6: Group items by level ---
    grouped: dict[int, list[OrganizeItem]] = {}
    for item_id, lvl in effective_levels.items():
        if lvl not in grouped:
            grouped[lvl] = []
        item = item_map.get(item_id)
        if item:
            grouped[lvl].append(item)

    ordered_levels = sorted(grouped.keys())

    h_spacing = opts.horizontal_spacing
    v_spacing = opts.vertical_spacing

    # Compute bounds for defaults
    min_x = min(it.x for it in items)
    max_x = max(it.x + it.width for it in items)
    min_y = min(it.y for it in items)
    max_y = max(it.y + it.height for it in items)

    default_start_x = opts.start_x if opts.start_x != 0 else min_x
    default_start_y = opts.start_y if opts.start_y != 0 else min_y
    default_center_x = (min_x + max_x) / 2
    default_center_y = (min_y + max_y) / 2

    layout: dict[str, LayoutPosition] = {}

    # --- Position items ---
    if orientation == "horizontal":
        reference_center_y = opts.reference_center_y if opts.reference_center_y != 0 else default_center_y
        current_x = default_start_x

        def get_parent_centers(item_id: str) -> list[float]:
            centers = []
            for edge in edges:
                if edge.to_id == item_id and edge.from_id in layout:
                    parent_item = item_map.get(edge.from_id)
                    parent_pos = layout.get(edge.from_id)
                    if parent_item and parent_pos:
                        centers.append(parent_pos.y + parent_item.height / 2)
            return centers

        for level in ordered_levels:
            column_items = list(grouped.get(level, []))
            if not column_items:
                continue

            column_width = max(it.width for it in column_items)

            # Build entries with target centers for smart alignment
            entries = []
            for item in column_items:
                parent_centers = get_parent_centers(item.id)
                fallback_center = item.y + item.height / 2
                if parent_centers:
                    target_center = sum(parent_centers) / len(parent_centers)
                    if not math.isfinite(target_center):
                        target_center = fallback_center
                else:
                    target_center = fallback_center
                entries.append({
                    "item": item,
                    "target_center": target_center,
                    "fallback_center": fallback_center,
                })

            # Sort by target center (smart vertical ordering)
            entries.sort(key=lambda e: (e["target_center"], e["fallback_center"], e["item"].id))

            previous_bottom = float("-inf")

            for entry in entries:
                item = entry["item"]
                desired_top = entry["target_center"] - item.height / 2

                if not math.isfinite(desired_top):
                    desired_top = entry["fallback_center"] - item.height / 2

                if not math.isfinite(desired_top):
                    desired_top = reference_center_y - item.height / 2

                # Overlap prevention
                if previous_bottom != float("-inf"):
                    min_top = previous_bottom + v_spacing
                    if desired_top < min_top:
                        desired_top = min_top

                final_y = round(desired_top)
                layout[item.id] = LayoutPosition(x=round(current_x), y=final_y)
                previous_bottom = final_y + item.height

            current_x += column_width + h_spacing

    else:  # vertical orientation
        reference_center_x = opts.reference_center_x if opts.reference_center_x != 0 else default_center_x
        current_y = default_start_y

        for level in ordered_levels:
            row_items = sorted(grouped.get(level, []), key=lambda it: (it.x, it.id))
            if not row_items:
                continue

            total_width = sum(it.width for it in row_items) + (len(row_items) - 1) * h_spacing
            cursor_x = reference_center_x - total_width / 2
            row_height = 0

            for item in row_items:
                layout[item.id] = LayoutPosition(x=round(cursor_x), y=round(current_y))
                cursor_x += item.width + h_spacing
                row_height = max(row_height, item.height)

            current_y += row_height + v_spacing

    # Fallback for any unpositioned items
    for item in items:
        if item.id not in layout:
            layout[item.id] = LayoutPosition(x=round(item.x), y=round(item.y))

    return layout


# ---------------------------------------------------------------------------
# Bounds computation (from Thoughtorio's computeBoundsFromNodeIds)
# ---------------------------------------------------------------------------

def compute_bounds_from_nodes(nodes: list[CanvasNode]) -> Optional[ContainerBounds]:
    """Compute the bounding box of a set of nodes.

    Returns None if there are no nodes or coordinates are not finite.
    Matches Thoughtorio's computeBoundsFromNodeIds().
    """
    if not nodes:
        return None

    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    for node in nodes:
        w = node.width or 360
        h = node.height or 180
        if not math.isfinite(node.x) or not math.isfinite(node.y):
            continue
        min_x = min(min_x, node.x)
        min_y = min(min_y, node.y)
        max_x = max(max_x, node.x + w)
        max_y = max(max_y, node.y + h)

    if not math.isfinite(min_x):
        return None

    return ContainerBounds(
        x=min_x,
        y=min_y,
        width=max(1, max_x - min_x),
        height=max(1, max_y - min_y),
    )


# ---------------------------------------------------------------------------
# Edge resolution for container-level organize
# ---------------------------------------------------------------------------

def _resolve_edges_for_containers(
    connections: list[tuple[str, str]],
    node_to_container: dict[str, str],
    container_ids: set[str],
) -> list[OrganizeEdge]:
    """Resolve node-level connections to container-level edges.

    If node A (in machine-1) connects to node B (in machine-2), this
    produces an edge machine-1 -> machine-2. Self-edges (same container)
    are excluded. Duplicates are deduplicated.

    Matches Thoughtorio's buildEdgesForOrganize() + resolveOrganizeEntity().
    """
    seen: set[tuple[str, str]] = set()
    edges: list[OrganizeEdge] = []

    for src_node, dst_node in connections:
        src_container = node_to_container.get(src_node)
        dst_container = node_to_container.get(dst_node)

        if not src_container or not dst_container:
            continue
        if src_container == dst_container:
            continue
        if src_container not in container_ids or dst_container not in container_ids:
            continue

        pair = (src_container, dst_container)
        if pair in seen:
            continue
        seen.add(pair)
        edges.append(OrganizeEdge(from_id=src_container, to_id=dst_container))

    return edges


# ---------------------------------------------------------------------------
# Hierarchical organize (the real Thoughtorio approach)
# ---------------------------------------------------------------------------

def _organize_machine(
    machine: CanvasMachine,
    all_connections: list[tuple[str, str]],
    start_x: float,
    start_y: float,
    orientation: str = "horizontal",
) -> Optional[ContainerBounds]:
    """Organize nodes within a single machine.

    Matches Thoughtorio's buildMachineOrganizeContext() + layout application.

    Returns the computed bounds of the machine after layout, or None if empty.
    """
    if not machine.nodes:
        return None

    node_ids = {n.id for n in machine.nodes}

    # Build items from this machine's nodes
    items = [
        OrganizeItem(
            id=node.id,
            item_type="node",
            width=node.width,
            height=node.height,
            x=node.x,
            y=node.y,
            node_ids=[node.id],
        )
        for node in machine.nodes
    ]

    # Build edges — only connections between nodes WITHIN this machine
    edges = [
        OrganizeEdge(from_id=src, to_id=dst)
        for src, dst in all_connections
        if src in node_ids and dst in node_ids
    ]

    options = OrganizeOptions(
        orientation=orientation,
        horizontal_spacing=NODE_HORIZONTAL_SPACING,
        vertical_spacing=NODE_VERTICAL_SPACING,
        start_x=start_x + MACHINE_PADDING,
        start_y=start_y + MACHINE_PADDING,
        grid_columns=GRID_COLUMNS_NODE,
    )

    layout = compute_organized_layout(items, edges, options)

    # Apply positions to nodes
    for node in machine.nodes:
        pos = layout.get(node.id)
        if pos:
            node.x = pos.x
            node.y = pos.y

    return compute_bounds_from_nodes(machine.nodes)


def _organize_factory(
    factory: CanvasFactory,
    all_connections: list[tuple[str, str]],
    start_x: float,
    start_y: float,
    orientation: str = "horizontal",
) -> Optional[ContainerBounds]:
    """Organize machines within a single factory.

    First organizes nodes within each machine (bottom-up), then positions
    machines relative to each other using container-level edges.

    Matches Thoughtorio's buildFactoryOrganizeContext().

    Returns the computed bounds of the factory after layout, or None if empty.
    """
    if not factory.machines:
        return None

    # --- Step 1: Organize each machine's internal nodes ---
    machine_bounds: dict[str, ContainerBounds] = {}
    for machine in factory.machines:
        # Use (0, 0) as temporary origin — we'll move the whole machine later
        bounds = _organize_machine(machine, all_connections, 0, 0, orientation=orientation)
        if bounds:
            machine_bounds[machine.id] = bounds

    if not machine_bounds:
        return None

    # --- Step 2: Build node-to-machine map for edge resolution ---
    node_to_machine: dict[str, str] = {}
    for machine in factory.machines:
        for node in machine.nodes:
            node_to_machine[node.id] = machine.id

    machine_ids = {m.id for m in factory.machines}

    # --- Step 3: Resolve cross-machine edges ---
    container_edges = _resolve_edges_for_containers(
        all_connections, node_to_machine, machine_ids
    )

    # --- Step 4: Build machine-level organize items ---
    items = []
    for machine in factory.machines:
        bounds = machine_bounds.get(machine.id)
        if not bounds:
            continue
        # Add padding to bounds for the container chrome
        padded_width = bounds.width + MACHINE_PADDING * 2
        padded_height = bounds.height + MACHINE_PADDING * 2 + 40  # 40 for label
        items.append(OrganizeItem(
            id=machine.id,
            item_type="machine",
            width=padded_width,
            height=padded_height,
            x=bounds.x,
            y=bounds.y,
            node_ids=[n.id for n in machine.nodes],
        ))

    if not items:
        return None

    # --- Step 5: Layout machines within the factory ---
    # When machines have no cross-machine edges, stack them all in a single
    # column (horizontal) or row (vertical) instead of using a grid.
    # This prevents disconnected machines from being split across
    # multiple columns/rows, which looks like stacking/overlapping.
    effective_grid_columns = (
        len(items) if not container_edges else GRID_COLUMNS_CONTAINER
    )

    options = OrganizeOptions(
        orientation=orientation,
        horizontal_spacing=CONTAINER_HORIZONTAL_SPACING,
        vertical_spacing=CONTAINER_VERTICAL_SPACING,
        start_x=start_x + FACTORY_PADDING,
        start_y=start_y + FACTORY_PADDING,
        grid_columns=effective_grid_columns,
    )

    layout = compute_organized_layout(items, container_edges, options)

    # --- Step 6: Apply machine positions (translate all child nodes) ---
    for machine in factory.machines:
        pos = layout.get(machine.id)
        bounds = machine_bounds.get(machine.id)
        if not pos or not bounds:
            continue

        # The layout gives us where the machine container should go.
        # We need to translate all nodes so they sit inside that position.
        # Currently, nodes were organized relative to (0, 0).
        # We shift them to the machine's new position + padding.
        dx = pos.x + MACHINE_PADDING - bounds.x
        dy = pos.y + MACHINE_PADDING + 40 - bounds.y  # 40 for label header

        for node in machine.nodes:
            node.x += dx
            node.y += dy

    # Compute final bounds of everything in this factory
    all_factory_nodes = []
    for machine in factory.machines:
        all_factory_nodes.extend(machine.nodes)
    return compute_bounds_from_nodes(all_factory_nodes)


def _organize_network(
    network: CanvasNetwork,
    all_connections: list[tuple[str, str]],
    start_x: float,
    start_y: float,
    orientation: str = "horizontal",
) -> Optional[ContainerBounds]:
    """Organize factories within a single network.

    First organizes machines within each factory (which in turn organizes
    nodes within each machine), then positions factories relative to each
    other using container-level edges.

    Matches Thoughtorio's buildNetworkOrganizeContext().

    Returns the computed bounds of the network after layout, or None if empty.
    """
    if not network.factories:
        return None

    # --- Step 1: Organize each factory's internal structure ---
    factory_bounds: dict[str, ContainerBounds] = {}
    for factory in network.factories:
        bounds = _organize_factory(factory, all_connections, 0, 0, orientation=orientation)
        if bounds:
            factory_bounds[factory.id] = bounds

    if not factory_bounds:
        return None

    # If there's only one factory, just position it at the start point
    if len(factory_bounds) == 1:
        factory = network.factories[0]
        bounds = factory_bounds[factory.id]
        if bounds:
            dx = start_x + NETWORK_PADDING - bounds.x
            dy = start_y + NETWORK_PADDING - bounds.y
            for machine in factory.machines:
                for node in machine.nodes:
                    node.x += dx
                    node.y += dy
        all_nodes = []
        for f in network.factories:
            for m in f.machines:
                all_nodes.extend(m.nodes)
        return compute_bounds_from_nodes(all_nodes)

    # --- Step 2: Build node-to-factory map for edge resolution ---
    node_to_factory: dict[str, str] = {}
    for factory in network.factories:
        for machine in factory.machines:
            for node in machine.nodes:
                node_to_factory[node.id] = factory.id

    factory_ids = {f.id for f in network.factories}

    # --- Step 3: Resolve cross-factory edges ---
    container_edges = _resolve_edges_for_containers(
        all_connections, node_to_factory, factory_ids
    )

    # --- Step 4: Build factory-level organize items ---
    items = []
    for factory in network.factories:
        bounds = factory_bounds.get(factory.id)
        if not bounds:
            continue
        padded_width = bounds.width + FACTORY_PADDING * 2
        padded_height = bounds.height + FACTORY_PADDING * 2 + 40  # 40 for label
        items.append(OrganizeItem(
            id=factory.id,
            item_type="factory",
            width=padded_width,
            height=padded_height,
            x=bounds.x,
            y=bounds.y,
            node_ids=[n.id for m in factory.machines for n in m.nodes],
        ))

    if not items:
        return None

    # --- Step 5: Layout factories within the network ---
    # Same grid-column logic as _organize_factory: when factories have no
    # cross-factory edges, keep them all in a single column/row.
    effective_grid_columns = (
        len(items) if not container_edges else GRID_COLUMNS_CONTAINER
    )

    options = OrganizeOptions(
        orientation=orientation,
        horizontal_spacing=NETWORK_HORIZONTAL_SPACING,
        vertical_spacing=NETWORK_VERTICAL_SPACING,
        start_x=start_x + NETWORK_PADDING,
        start_y=start_y + NETWORK_PADDING,
        grid_columns=effective_grid_columns,
    )

    layout = compute_organized_layout(items, container_edges, options)

    # --- Step 6: Apply factory positions (translate all child nodes) ---
    for factory in network.factories:
        pos = layout.get(factory.id)
        bounds = factory_bounds.get(factory.id)
        if not pos or not bounds:
            continue

        dx = pos.x + FACTORY_PADDING - bounds.x
        dy = pos.y + FACTORY_PADDING + 40 - bounds.y  # 40 for label header

        for machine in factory.machines:
            for node in machine.nodes:
                node.x += dx
                node.y += dy

    # Compute final bounds
    all_nodes = []
    for factory in network.factories:
        for machine in factory.machines:
            all_nodes.extend(machine.nodes)
    return compute_bounds_from_nodes(all_nodes)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _get_all_network_nodes(network: CanvasNetwork) -> list[CanvasNode]:
    """Collect all nodes from a network."""
    nodes = []
    for factory in network.factories:
        for machine in factory.machines:
            nodes.extend(machine.nodes)
    return nodes


# Spacing between networks at the top level (generous to separate systems)
INTER_NETWORK_HORIZONTAL_SPACING = 320
INTER_NETWORK_VERTICAL_SPACING = 380


def organize_canvas(
    canvas: Canvas,
    spacing_level: str = "container",
    orientation: str = "horizontal",
) -> None:
    """
    Apply Thoughtorio's hierarchical organize algorithm to an entire Canvas,
    repositioning nodes in-place.

    This is the HIERARCHICAL version that matches Thoughtorio's actual behavior:
    1. Nodes are organized within each machine (node-level spacing)
    2. Machines are organized within each factory (container-level spacing)
    3. Factories are organized within each network (network-level spacing)
    4. Networks are positioned relative to each other (inter-network spacing)

    At each level, child containers are treated as single items with bounds
    computed from their contents. Cross-container connections are resolved
    upward so downstream flow informs layout at every level.

    Args:
        canvas: The canvas to organize.
        spacing_level: Advisory spacing level ("node", "container", "network").
        orientation: Layout direction — "horizontal" (left→right) or "vertical"
                     (top→bottom). Applied at all hierarchy levels.

    The spacing_level parameter is now advisory — the hierarchical system
    always uses the correct spacing for each level. For single-machine
    diagrams, it falls through to node-level spacing naturally.
    """
    all_nodes = canvas.all_nodes()
    if not all_nodes:
        return

    all_connections = canvas.all_connections()

    # Start position (top-left margin, leaving room for title)
    start_x = 80
    start_y = 100

    # --- Step 1: Organize each network internally at origin (0, 0) ---
    # We organize each network at a temporary origin first, then position
    # them relative to each other in Step 2.
    network_bounds: dict[str, ContainerBounds] = {}
    for network in canvas.networks:
        _organize_network(network, all_connections, 0, 0, orientation=orientation)
        net_nodes = _get_all_network_nodes(network)
        if net_nodes:
            bounds = compute_bounds_from_nodes(net_nodes)
            if bounds:
                network_bounds[network.id] = bounds

    # --- Step 2: Position networks relative to each other ---
    if len(canvas.networks) <= 1:
        # Single network — just translate to start position
        if canvas.networks:
            net = canvas.networks[0]
            net_nodes = _get_all_network_nodes(net)
            if net_nodes:
                bounds = network_bounds.get(net.id)
                if bounds:
                    dx = start_x - bounds.x
                    dy = start_y - bounds.y
                    for node in net_nodes:
                        node.x += dx
                        node.y += dy
        return

    # Multiple networks: build network-level organize items and use the
    # same topological layout algorithm to position them.
    node_to_network: dict[str, str] = {}
    for network in canvas.networks:
        for factory in network.factories:
            for machine in factory.machines:
                for node in machine.nodes:
                    node_to_network[node.id] = network.id

    network_ids = {n.id for n in canvas.networks}

    # Resolve cross-network edges
    container_edges = _resolve_edges_for_containers(
        all_connections, node_to_network, network_ids
    )

    # Build network-level organize items
    items = []
    for network in canvas.networks:
        bounds = network_bounds.get(network.id)
        if not bounds:
            continue
        # Add generous padding around each network's bounds
        padded_width = bounds.width + NETWORK_PADDING * 2
        padded_height = bounds.height + NETWORK_PADDING * 2
        items.append(OrganizeItem(
            id=network.id,
            item_type="network",
            width=padded_width,
            height=padded_height,
            x=bounds.x,
            y=bounds.y,
            node_ids=[n.id for n in _get_all_network_nodes(network)],
        ))

    if not items:
        return

    # Layout networks using the core algorithm
    options = OrganizeOptions(
        orientation=orientation,
        horizontal_spacing=INTER_NETWORK_HORIZONTAL_SPACING,
        vertical_spacing=INTER_NETWORK_VERTICAL_SPACING,
        start_x=start_x,
        start_y=start_y,
        grid_columns=GRID_COLUMNS_CONTAINER,
    )

    layout = compute_organized_layout(items, container_edges, options)

    # Apply network positions (translate all child nodes)
    for network in canvas.networks:
        pos = layout.get(network.id)
        bounds = network_bounds.get(network.id)
        if not pos or not bounds:
            continue

        dx = pos.x + NETWORK_PADDING - bounds.x
        dy = pos.y + NETWORK_PADDING - bounds.y

        for factory in network.factories:
            for machine in factory.machines:
                for node in machine.nodes:
                    node.x += dx
                    node.y += dy
