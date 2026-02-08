"""
Thoughtorio-style organize algorithm for Canvas-MCP.

Ported from Thoughtorio's organize.js — topological layout with intelligent
parent-child alignment, overlap prevention, and hierarchical spacing.

Spacing constants match Thoughtorio exactly:
  - Nodes within machines: 60px horizontal, 110px vertical
  - Containers (machines/factories): 150px horizontal, 190px vertical
  - Networks: 190px horizontal, 250px vertical
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from .models import Canvas, CanvasNode


# --- Spacing constants (from Thoughtorio) ---

NODE_HORIZONTAL_SPACING = 60
NODE_VERTICAL_SPACING = 110

CONTAINER_HORIZONTAL_SPACING = 150
CONTAINER_VERTICAL_SPACING = 190

NETWORK_HORIZONTAL_SPACING = 190  # CONTAINER + 40
NETWORK_VERTICAL_SPACING = 250    # CONTAINER + 60

GRID_COLUMNS = 4


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
    grid_columns: int = GRID_COLUMNS


@dataclass
class LayoutPosition:
    """Computed position for an item."""
    x: float
    y: float


def compute_organized_layout(
    items: list[OrganizeItem],
    edges: list[OrganizeEdge],
    options: Optional[OrganizeOptions] = None,
) -> dict[str, LayoutPosition]:
    """
    Core organize algorithm — port of Thoughtorio's computeOrganizedLayout().

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


def organize_canvas(canvas: Canvas, spacing_level: str = "container") -> None:
    """
    Apply Thoughtorio's organize algorithm to an entire Canvas model,
    repositioning nodes in-place.

    spacing_level controls the breathing room:
      - "node": tight (60h, 110v) — good for small diagrams
      - "container": medium (150h, 190v) — good for architecture diagrams (DEFAULT)
      - "network": spacious (190h, 250v) — good for large system diagrams
    """
    spacing_map = {
        "node": (NODE_HORIZONTAL_SPACING, NODE_VERTICAL_SPACING),
        "container": (CONTAINER_HORIZONTAL_SPACING, CONTAINER_VERTICAL_SPACING),
        "network": (NETWORK_HORIZONTAL_SPACING, NETWORK_VERTICAL_SPACING),
    }
    h_spacing, v_spacing = spacing_map.get(spacing_level, spacing_map["container"])

    all_nodes = canvas.all_nodes()
    if not all_nodes:
        return

    # Build organize items from canvas nodes
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
        for node in all_nodes
    ]

    # Build edges from canvas connections
    connections = canvas.all_connections()
    edges = [
        OrganizeEdge(from_id=src, to_id=dst)
        for src, dst in connections
    ]

    # Compute organized layout
    options = OrganizeOptions(
        orientation="horizontal",
        horizontal_spacing=h_spacing,
        vertical_spacing=v_spacing,
        start_x=80,  # Left margin (Thoughtorio uses 60-80 depending on level)
        start_y=100,  # Top margin (room for title)
    )

    layout = compute_organized_layout(items, edges, options)

    # Apply positions back to canvas nodes
    for node in all_nodes:
        pos = layout.get(node.id)
        if pos:
            node.x = pos.x
            node.y = pos.y
