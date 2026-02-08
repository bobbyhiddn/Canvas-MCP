"""Canvas renderer using Pillow — produces Thoughtorio-style PNG diagrams."""

from __future__ import annotations

import math
import textwrap
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from .models import Canvas, CanvasNode, CanvasFactory, CanvasMachine, NodeStyle


# --- Font handling ---

def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a font, falling back to default if none available."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def _load_bold_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a bold font, falling back to regular."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    return _load_font(size)


# --- Color helpers ---

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    """Convert hex color to RGBA tuple."""
    r, g, b = _hex_to_rgb(hex_color)
    return (r, g, b, alpha)


def _darken(hex_color: str, factor: float = 0.6) -> str:
    """Darken a hex color."""
    r, g, b = _hex_to_rgb(hex_color)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


# --- Drawing primitives ---

def _draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float, float, float],
    radius: int,
    fill: Optional[str] = None,
    outline: Optional[str] = None,
    width: int = 1,
):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=radius,
        fill=fill,
        outline=outline,
        width=width,
    )


def _draw_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str = "#585b70",
    width: int = 2,
    arrow_size: int = 10,
):
    """Draw a line with an arrowhead."""
    draw.line([start, end], fill=color, width=width)

    # Calculate arrowhead
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return

    # Normalize
    udx = dx / length
    udy = dy / length

    # Arrowhead points
    ax = end[0] - arrow_size * udx + (arrow_size / 2) * udy
    ay = end[1] - arrow_size * udy - (arrow_size / 2) * udx
    bx = end[0] - arrow_size * udx - (arrow_size / 2) * udy
    by = end[1] - arrow_size * udy + (arrow_size / 2) * udx

    draw.polygon([(end[0], end[1]), (ax, ay), (bx, by)], fill=color)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip() if current else word
        bbox = font.getbbox(test)
        tw = bbox[2] - bbox[0]
        if tw <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            # If single word is too long, force-wrap it
            if font.getbbox(word)[2] - font.getbbox(word)[0] > max_width:
                # Character-level wrap
                for chunk in textwrap.wrap(word, width=max(1, max_width // 8)):
                    lines.append(chunk)
                current = ""
            else:
                current = word

    if current:
        lines.append(current)

    return lines if lines else [""]


# --- Main renderer ---

class CanvasRenderer:
    """Renders a Canvas model to a PNG image."""

    # Layout constants
    PADDING = 40
    NODE_PADDING = 16
    LABEL_HEIGHT = 24
    CONTAINER_PADDING = 30
    CONTAINER_LABEL_HEIGHT = 28

    def __init__(self, scale: float = 1.0):
        self.scale = scale
        self.font_body = _load_font(int(13 * scale))
        self.font_label = _load_bold_font(int(14 * scale))
        self.font_title = _load_bold_font(int(20 * scale))
        self.font_container = _load_bold_font(int(12 * scale))
        self.font_small = _load_font(int(10 * scale))

    def render(self, canvas: Canvas, output_path: Optional[str] = None) -> bytes:
        """Render the canvas to PNG bytes. Optionally save to file."""
        # Auto-layout if nodes have no coordinates
        self._auto_layout_if_needed(canvas)

        # Calculate canvas bounds from node positions
        bounds = self._calculate_bounds(canvas)
        img_width = int(bounds["width"] * self.scale)
        img_height = int(bounds["height"] * self.scale)

        # Create image
        img = Image.new("RGBA", (img_width, img_height), _hex_to_rgba(canvas.background_color))
        draw = ImageDraw.Draw(img)

        # Offset for translating node coordinates to image space
        ox = -bounds["min_x"] + self.PADDING
        oy = -bounds["min_y"] + self.PADDING

        # Draw title
        self._draw_title(draw, canvas.title, img_width)

        # Draw containers (machines, factories) as subtle grouped backgrounds
        for network in canvas.networks:
            for factory in network.factories:
                self._draw_factory_container(draw, factory, ox, oy)
                for machine in factory.machines:
                    self._draw_machine_container(draw, machine, ox, oy)

        # Draw connections first (behind nodes)
        self._draw_connections(draw, canvas, ox, oy)

        # Draw nodes
        for node in canvas.all_nodes():
            self._draw_node(draw, node, ox, oy)

        # Convert to bytes
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        png_bytes = buf.getvalue()

        if output_path:
            Path(output_path).write_bytes(png_bytes)

        return png_bytes

    def _auto_layout_if_needed(self, canvas: Canvas):
        """If all nodes are at (0,0), auto-layout them."""
        nodes = canvas.all_nodes()
        if not nodes:
            return

        all_zero = all(n.x == 0 and n.y == 0 for n in nodes)
        if not all_zero:
            return

        # Auto-layout: arrange nodes left-to-right within machines,
        # machines top-to-bottom within factories
        x_offset = self.PADDING * 2
        y_offset = self.PADDING * 2 + 50  # Leave room for title

        for network in canvas.networks:
            for factory in network.factories:
                factory_start_y = y_offset
                for machine in factory.machines:
                    x = x_offset
                    for node in machine.nodes:
                        node.x = x
                        node.y = y_offset
                        x += node.width + 80  # horizontal spacing
                    y_offset += 200  # vertical spacing between machines
                y_offset += 60  # extra gap between factories

    def _calculate_bounds(self, canvas: Canvas) -> dict:
        """Calculate the bounding box of all nodes."""
        nodes = canvas.all_nodes()
        if not nodes:
            return {"min_x": 0, "min_y": 0, "width": 400, "height": 300}

        min_x = min(n.x for n in nodes) - self.PADDING
        min_y = min(n.y for n in nodes) - self.PADDING - 50  # Title space
        max_x = max(n.x + n.width for n in nodes) + self.PADDING
        max_y = max(n.y + n.height for n in nodes) + self.PADDING

        return {
            "min_x": min_x,
            "min_y": min_y,
            "width": max_x - min_x + self.PADDING,
            "height": max_y - min_y + self.PADDING,
        }

    def _draw_title(self, draw: ImageDraw.ImageDraw, title: str, img_width: int):
        """Draw the canvas title centered at the top."""
        bbox = self.font_title.getbbox(title)
        tw = bbox[2] - bbox[0]
        x = (img_width - tw) / 2
        draw.text((x, 15 * self.scale), title, fill="#cdd6f4", font=self.font_title)

    def _get_container_bounds(self, nodes: list[CanvasNode]) -> tuple[float, float, float, float]:
        """Get bounding box for a set of nodes."""
        if not nodes:
            return (0, 0, 0, 0)
        pad = self.CONTAINER_PADDING
        min_x = min(n.x for n in nodes) - pad
        min_y = min(n.y for n in nodes) - pad - self.CONTAINER_LABEL_HEIGHT
        max_x = max(n.x + n.width for n in nodes) + pad
        max_y = max(n.y + n.height for n in nodes) + pad
        return (min_x, min_y, max_x, max_y)

    def _draw_machine_container(self, draw: ImageDraw.ImageDraw, machine: CanvasMachine, ox: float, oy: float):
        """Draw a subtle container around a machine's nodes."""
        if not machine.nodes:
            return
        x1, y1, x2, y2 = self._get_container_bounds(machine.nodes)
        x1 = (x1 + ox) * self.scale
        y1 = (y1 + oy) * self.scale
        x2 = (x2 + ox) * self.scale
        y2 = (y2 + oy) * self.scale

        # Subtle dashed-style container
        _draw_rounded_rect(
            draw, (x1, y1, x2, y2),
            radius=8,
            fill=_hex_to_rgba("#181825", 120),
            outline="#313244",
            width=1,
        )

        # Machine label
        label = machine.label or machine.id
        draw.text(
            (x1 + 10, y1 + 5),
            label,
            fill="#6c7086",
            font=self.font_container,
        )

    def _draw_factory_container(self, draw: ImageDraw.ImageDraw, factory: CanvasFactory, ox: float, oy: float):
        """Draw a container around a factory's machines."""
        all_nodes = []
        for machine in factory.machines:
            all_nodes.extend(machine.nodes)
        if not all_nodes:
            return

        x1, y1, x2, y2 = self._get_container_bounds(all_nodes)
        # Expand a bit beyond machine containers
        expand = 15
        x1 = (x1 - expand + ox) * self.scale
        y1 = (y1 - expand + oy) * self.scale - self.CONTAINER_LABEL_HEIGHT
        x2 = (x2 + expand + ox) * self.scale
        y2 = (y2 + expand + oy) * self.scale

        _draw_rounded_rect(
            draw, (x1, y1, x2, y2),
            radius=12,
            outline="#45475a",
            width=1,
        )

        # Factory label
        label = factory.label or factory.id
        draw.text(
            (x1 + 12, y1 + 6),
            label,
            fill="#a6adc8",
            font=self.font_container,
        )

    def _draw_connections(self, draw: ImageDraw.ImageDraw, canvas: Canvas, ox: float, oy: float):
        """Draw all connections between nodes."""
        for source_id, target_id in canvas.all_connections():
            source = canvas.get_node(source_id)
            target = canvas.get_node(target_id)
            if not source or not target:
                continue

            # Connection from right edge of source to left edge of target
            sx = (source.x + source.width + ox) * self.scale
            sy = (source.y + source.height / 2 + oy) * self.scale
            tx = (target.x + ox) * self.scale
            ty = (target.y + target.height / 2 + oy) * self.scale

            # Determine connection color based on source type
            style = source.get_style()
            conn_color = _darken(style.border_color, 0.7)

            # Draw bezier-like connection using line segments
            self._draw_bezier_connection(draw, (sx, sy), (tx, ty), conn_color)

    def _draw_bezier_connection(
        self,
        draw: ImageDraw.ImageDraw,
        start: tuple[float, float],
        end: tuple[float, float],
        color: str,
        width: int = 2,
    ):
        """Draw a smooth bezier-like connection between two points."""
        sx, sy = start
        ex, ey = end

        # Control points for a horizontal S-curve
        dx = abs(ex - sx)
        cp_offset = max(dx * 0.4, 40 * self.scale)

        # Generate bezier points
        points = []
        steps = 30
        for i in range(steps + 1):
            t = i / steps
            # Cubic bezier
            cp1x = sx + cp_offset
            cp1y = sy
            cp2x = ex - cp_offset
            cp2y = ey

            x = (1-t)**3 * sx + 3*(1-t)**2*t * cp1x + 3*(1-t)*t**2 * cp2x + t**3 * ex
            y = (1-t)**3 * sy + 3*(1-t)**2*t * cp1y + 3*(1-t)*t**2 * cp2y + t**3 * ey
            points.append((x, y))

        # Draw the curve
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=color, width=width)

        # Arrowhead at end
        if len(points) >= 2:
            _draw_arrow(draw, points[-2], points[-1], color=color, width=width, arrow_size=int(8 * self.scale))

    def _draw_node(self, draw: ImageDraw.ImageDraw, node: CanvasNode, ox: float, oy: float):
        """Draw a single node."""
        style = node.get_style()

        x = (node.x + ox) * self.scale
        y = (node.y + oy) * self.scale
        w = node.width * self.scale
        h = node.height * self.scale

        # Node background
        _draw_rounded_rect(
            draw, (x, y, x + w, y + h),
            radius=int(style.corner_radius * self.scale),
            fill=style.fill_color,
            outline=style.border_color,
            width=int(2 * self.scale),
        )

        # Node type indicator bar at top
        bar_height = int(4 * self.scale)
        _draw_rounded_rect(
            draw,
            (x + 2, y + 2, x + w - 2, y + bar_height + 2),
            radius=int(style.corner_radius * self.scale),
            fill=style.border_color,
        )

        # Label
        label = node.get_label()
        label_y = y + bar_height + int(8 * self.scale)
        draw.text(
            (x + int(self.NODE_PADDING * self.scale), label_y),
            label,
            fill=style.label_color or "#cdd6f4",
            font=self.font_label,
        )

        # Content text (wrapped)
        content_y = label_y + int(22 * self.scale)
        max_text_width = int(w - 2 * self.NODE_PADDING * self.scale)
        if node.content:
            lines = _wrap_text(node.content, self.font_body, max_text_width)
            # Limit to what fits in the node
            max_lines = int((h - (content_y - y) - 10 * self.scale) / (16 * self.scale))
            if max_lines < 1:
                max_lines = 1
            display_lines = lines[:max_lines]
            if len(lines) > max_lines:
                display_lines[-1] = display_lines[-1][:20] + "..."

            for i, line in enumerate(display_lines):
                draw.text(
                    (x + int(self.NODE_PADDING * self.scale), content_y + i * int(16 * self.scale)),
                    line,
                    fill="#a6adc8",
                    font=self.font_body,
                )

        # Type badge in bottom-right
        type_text = node.type
        type_bbox = self.font_small.getbbox(type_text)
        type_w = type_bbox[2] - type_bbox[0] + 8
        type_h = type_bbox[3] - type_bbox[1] + 4
        type_x = x + w - type_w - int(8 * self.scale)
        type_y = y + h - type_h - int(8 * self.scale)

        _draw_rounded_rect(
            draw, (type_x, type_y, type_x + type_w, type_y + type_h),
            radius=4,
            fill=_darken(style.border_color, 0.3),
        )
        draw.text(
            (type_x + 4, type_y + 1),
            type_text,
            fill=style.border_color,
            font=self.font_small,
        )
