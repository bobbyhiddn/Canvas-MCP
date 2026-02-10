"""Architecture icon library for Canvas-MCP.

Draws recognizable infrastructure symbols using PIL primitives —
no external assets, no new dependencies. Icons are drawn into a
square bounding box at the specified position and scale.

Each icon function has the signature:

    draw_<name>(draw, cx, cy, size, color)

where (cx, cy) is the center point, size is the icon's bounding
dimension (width=height), and color is the accent hex color.

Icon Categories:
    Cloud       — cloud, aws, gcp, azure
    Compute     — server, vm, container, pod, lambda
    Networking  — loadbalancer, gateway, firewall, cdn, dns
    Storage     — database, objectstore, filesystem, cache
    Services    — api, queue, monitoring, logs, search
    Agent       — brain, oracle, worker, bus
    General     — lock, key, globe, user, users, gear, bell, mail
"""

from __future__ import annotations

import math
from typing import Callable

from PIL import ImageDraw


# ─── Type alias ──────────────────────────────────────────────────────
IconDrawFn = Callable[[ImageDraw.ImageDraw, float, float, float, str], None]


# ─── Helpers ─────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = hex_color[0]*2 + hex_color[1]*2 + hex_color[2]*2
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _with_alpha(hex_color: str, alpha: int) -> tuple[int, int, int, int]:
    r, g, b = _hex_to_rgb(hex_color)
    return (r, g, b, alpha)


def _lighten(hex_color: str, factor: float = 0.4) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def _darken(hex_color: str, factor: float = 0.5) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"


# ─── Cloud Icons ─────────────────────────────────────────────────────

def draw_cloud(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Generic cloud shape — three overlapping circles + base rect."""
    s = size * 0.45
    # Base ellipse (wide)
    draw.ellipse(
        [cx - s, cy - s*0.3, cx + s, cy + s*0.5],
        outline=color, width=max(2, int(size/18))
    )
    # Left bump
    draw.ellipse(
        [cx - s*0.8, cy - s*0.7, cx - s*0.05, cy + s*0.1],
        outline=color, fill=_with_alpha(color, 30), width=max(2, int(size/18))
    )
    # Right bump
    draw.ellipse(
        [cx + s*0.05, cy - s*0.55, cx + s*0.7, cy + s*0.15],
        outline=color, fill=_with_alpha(color, 30), width=max(2, int(size/18))
    )
    # Center top bump (tallest)
    draw.ellipse(
        [cx - s*0.45, cy - s*0.9, cx + s*0.35, cy - s*0.05],
        outline=color, fill=_with_alpha(color, 30), width=max(2, int(size/18))
    )


def draw_aws(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """AWS-style icon — cloud with 'AWS' text."""
    draw_cloud(draw, cx, cy - size*0.05, size * 0.85, color)
    # Small 'A' indicator — draw a simple arrow/smile
    s = size * 0.15
    w = max(2, int(size/16))
    # Arrow pointing right (the AWS smile)
    draw.line([(cx - s, cy + size*0.25), (cx + s, cy + size*0.25)], fill=color, width=w)
    draw.line([(cx + s*0.4, cy + size*0.18), (cx + s, cy + size*0.25)], fill=color, width=w)
    draw.line([(cx + s*0.4, cy + size*0.32), (cx + s, cy + size*0.25)], fill=color, width=w)


def draw_gcp(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """GCP-style icon — hexagon shape."""
    s = size * 0.38
    w = max(2, int(size/16))
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = cx + s * math.cos(angle)
        py = cy + s * math.sin(angle)
        points.append((px, py))
    draw.polygon(points, outline=color, fill=_with_alpha(color, 25))
    # Inner smaller hexagon
    s2 = s * 0.55
    points2 = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = cx + s2 * math.cos(angle)
        py = cy + s2 * math.sin(angle)
        points2.append((px, py))
    draw.polygon(points2, outline=color, width=w)


def draw_azure(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Azure-style icon — diamond/rhombus shape."""
    s = size * 0.38
    w = max(2, int(size/16))
    points = [
        (cx, cy - s),       # top
        (cx + s, cy),       # right
        (cx, cy + s),       # bottom
        (cx - s, cy),       # left
    ]
    draw.polygon(points, outline=color, fill=_with_alpha(color, 25))
    # Inner cross
    draw.line([(cx, cy - s*0.4), (cx, cy + s*0.4)], fill=color, width=w)
    draw.line([(cx - s*0.4, cy), (cx + s*0.4, cy)], fill=color, width=w)


# ─── Compute Icons ───────────────────────────────────────────────────

def draw_server(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Server rack unit — stacked rectangles."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Three stacked rack units
    for i, yoff in enumerate([-s*0.7, -s*0.1, s*0.5]):
        y1 = cy + yoff
        y2 = y1 + s * 0.5
        draw.rounded_rectangle(
            [cx - s, y1, cx + s, y2],
            radius=max(2, int(size/20)),
            outline=color, width=w,
            fill=_with_alpha(color, 20) if i == 1 else None,
        )
        # Status LED (small circle on the right)
        led_r = max(2, size * 0.04)
        draw.ellipse(
            [cx + s*0.65 - led_r, y1 + (y2-y1)/2 - led_r,
             cx + s*0.65 + led_r, y1 + (y2-y1)/2 + led_r],
            fill=color,
        )


def draw_vm(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Virtual Machine — monitor/screen shape."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Screen
    draw.rounded_rectangle(
        [cx - s, cy - s*0.7, cx + s, cy + s*0.3],
        radius=max(2, int(size/18)),
        outline=color, width=w,
        fill=_with_alpha(color, 20),
    )
    # Stand
    draw.line([(cx, cy + s*0.3), (cx, cy + s*0.6)], fill=color, width=w)
    # Base
    draw.line([(cx - s*0.5, cy + s*0.6), (cx + s*0.5, cy + s*0.6)], fill=color, width=w)
    # VM label — small diamond inside screen
    ds = s * 0.2
    draw.polygon([
        (cx, cy - s*0.35),
        (cx + ds, cy - s*0.15),
        (cx, cy + s*0.05),
        (cx - ds, cy - s*0.15),
    ], outline=color, width=max(1, w-1))


def draw_container(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Container / Docker — shipping container / whale."""
    s = size * 0.38
    w = max(2, int(size/18))
    # Container body
    draw.rounded_rectangle(
        [cx - s, cy - s*0.4, cx + s, cy + s*0.5],
        radius=max(2, int(size/22)),
        outline=color, width=w,
        fill=_with_alpha(color, 20),
    )
    # Container grid lines (horizontal)
    draw.line([(cx - s*0.8, cy), (cx + s*0.8, cy)], fill=color, width=max(1, w-1))
    # Container grid lines (vertical sections)
    for xoff in [-0.4, 0.0, 0.4]:
        x = cx + s * xoff
        draw.line([(x, cy - s*0.3), (x, cy + s*0.4)], fill=color, width=max(1, w-1))
    # Handle on top
    draw.arc(
        [cx - s*0.25, cy - s*0.7, cx + s*0.25, cy - s*0.3],
        start=180, end=0, fill=color, width=w,
    )


def draw_pod(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Kubernetes Pod — wheel/helm icon."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Outer circle
    draw.ellipse(
        [cx - s, cy - s, cx + s, cy + s],
        outline=color, width=w,
    )
    # Inner circle
    inner = s * 0.35
    draw.ellipse(
        [cx - inner, cy - inner, cx + inner, cy + inner],
        outline=color, width=w,
        fill=_with_alpha(color, 30),
    )
    # Spokes (7 spokes like K8s wheel)
    for i in range(7):
        angle = math.radians(360 / 7 * i - 90)
        x1 = cx + inner * math.cos(angle)
        y1 = cy + inner * math.sin(angle)
        x2 = cx + s * 0.85 * math.cos(angle)
        y2 = cy + s * 0.85 * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=max(1, w-1))


def draw_lambda(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Lambda / serverless function — lambda symbol."""
    s = size * 0.35
    w = max(2, int(size/16))
    # Lambda shape: /\ with left leg descending
    draw.line([(cx - s*0.5, cy + s*0.6), (cx, cy - s*0.6)], fill=color, width=w)
    draw.line([(cx, cy - s*0.6), (cx + s*0.5, cy + s*0.6)], fill=color, width=w)
    # Horizontal bar on top-left
    draw.line([(cx - s*0.7, cy - s*0.6), (cx + s*0.1, cy - s*0.6)], fill=color, width=w)


# ─── Networking Icons ────────────────────────────────────────────────

def draw_loadbalancer(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Load Balancer — input splitting to multiple outputs."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Input circle on left
    cr = s * 0.25
    draw.ellipse(
        [cx - s - cr, cy - cr, cx - s + cr, cy + cr],
        outline=color, width=w, fill=_with_alpha(color, 30),
    )
    # Three output circles on right
    for yoff in [-s*0.6, 0, s*0.6]:
        draw.ellipse(
            [cx + s*0.6 - cr, cy + yoff - cr, cx + s*0.6 + cr, cy + yoff + cr],
            outline=color, width=w,
        )
        # Connecting line
        draw.line([(cx - s + cr, cy), (cx + s*0.6 - cr, cy + yoff)], fill=color, width=max(1, w-1))


def draw_gateway(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """API Gateway — gate/door shape."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Two pillars
    pw = s * 0.2
    draw.rounded_rectangle(
        [cx - s, cy - s*0.6, cx - s + pw, cy + s*0.5],
        radius=max(1, int(size/30)),
        outline=color, width=w,
        fill=_with_alpha(color, 25),
    )
    draw.rounded_rectangle(
        [cx + s - pw, cy - s*0.6, cx + s, cy + s*0.5],
        radius=max(1, int(size/30)),
        outline=color, width=w,
        fill=_with_alpha(color, 25),
    )
    # Arch on top connecting pillars
    draw.arc(
        [cx - s, cy - s, cx + s, cy + s*0.2],
        start=180, end=0, fill=color, width=w,
    )
    # Arrow passing through
    aw = s * 0.5
    draw.line([(cx - aw, cy + s*0.1), (cx + aw, cy + s*0.1)], fill=color, width=w)
    draw.line([(cx + aw*0.5, cy - s*0.05), (cx + aw, cy + s*0.1)], fill=color, width=w)
    draw.line([(cx + aw*0.5, cy + s*0.25), (cx + aw, cy + s*0.1)], fill=color, width=w)


def draw_firewall(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Firewall — brick wall / shield shape."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Shield outline
    points = [
        (cx, cy - s*0.8),       # top
        (cx + s*0.8, cy - s*0.3),  # top-right
        (cx + s*0.6, cy + s*0.5),  # bottom-right
        (cx, cy + s*0.8),       # bottom
        (cx - s*0.6, cy + s*0.5),  # bottom-left
        (cx - s*0.8, cy - s*0.3),  # top-left
    ]
    draw.polygon(points, outline=color, fill=_with_alpha(color, 20))
    # Horizontal brick lines
    draw.line([(cx - s*0.65, cy - s*0.15), (cx + s*0.65, cy - s*0.15)], fill=color, width=max(1, w-1))
    draw.line([(cx - s*0.55, cy + s*0.2), (cx + s*0.55, cy + s*0.2)], fill=color, width=max(1, w-1))
    # Vertical brick offsets
    draw.line([(cx, cy - s*0.5), (cx, cy - s*0.15)], fill=color, width=max(1, w-1))
    draw.line([(cx - s*0.35, cy - s*0.15), (cx - s*0.35, cy + s*0.2)], fill=color, width=max(1, w-1))
    draw.line([(cx + s*0.35, cy - s*0.15), (cx + s*0.35, cy + s*0.2)], fill=color, width=max(1, w-1))


def draw_cdn(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """CDN — globe with speed lines."""
    s = size * 0.33
    w = max(2, int(size/18))
    draw_globe(draw, cx - s*0.15, cy, size * 0.75, color)
    # Speed lines on right
    for yoff in [-s*0.3, 0, s*0.3]:
        draw.line(
            [(cx + s*0.5, cy + yoff), (cx + s*0.9, cy + yoff)],
            fill=color, width=max(1, w-1)
        )


def draw_dns(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """DNS — address book / lookup icon."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Book shape
    draw.rounded_rectangle(
        [cx - s, cy - s*0.6, cx + s, cy + s*0.6],
        radius=max(2, int(size/22)),
        outline=color, width=w,
        fill=_with_alpha(color, 15),
    )
    # Spine on left
    draw.line([(cx - s*0.7, cy - s*0.5), (cx - s*0.7, cy + s*0.5)], fill=color, width=w)
    # Horizontal lines (entries)
    for yoff in [-0.25, 0, 0.25]:
        draw.line(
            [(cx - s*0.4, cy + s*yoff), (cx + s*0.7, cy + s*yoff)],
            fill=color, width=max(1, w-1)
        )


# ─── Storage Icons ───────────────────────────────────────────────────

def draw_database(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Database — cylinder (ellipse + rect + bottom ellipse)."""
    s = size * 0.35
    w = max(2, int(size/18))
    ew = s * 0.9   # ellipse half-width
    eh = s * 0.25  # ellipse half-height
    # Body rectangle
    draw.rectangle(
        [cx - ew, cy - s*0.4, cx + ew, cy + s*0.5],
        fill=_with_alpha(color, 20),
    )
    draw.line([(cx - ew, cy - s*0.4), (cx - ew, cy + s*0.5)], fill=color, width=w)
    draw.line([(cx + ew, cy - s*0.4), (cx + ew, cy + s*0.5)], fill=color, width=w)
    # Top ellipse
    draw.ellipse(
        [cx - ew, cy - s*0.4 - eh, cx + ew, cy - s*0.4 + eh],
        outline=color, width=w, fill=_with_alpha(color, 30),
    )
    # Bottom ellipse (arc only — bottom half)
    draw.arc(
        [cx - ew, cy + s*0.5 - eh, cx + ew, cy + s*0.5 + eh],
        start=0, end=180, fill=color, width=w,
    )
    # Middle separator ellipse
    draw.arc(
        [cx - ew, cy - eh*0.6, cx + ew, cy + eh*0.6],
        start=0, end=180, fill=color, width=max(1, w-1),
    )


def draw_objectstore(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Object Store / S3 — bucket shape."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Bucket — trapezoid shape (wider at top)
    points = [
        (cx - s*0.7, cy - s*0.5),   # top-left
        (cx + s*0.7, cy - s*0.5),   # top-right
        (cx + s*0.5, cy + s*0.6),   # bottom-right
        (cx - s*0.5, cy + s*0.6),   # bottom-left
    ]
    draw.polygon(points, outline=color, fill=_with_alpha(color, 20))
    # Handle
    draw.arc(
        [cx - s*0.3, cy - s*0.8, cx + s*0.3, cy - s*0.3],
        start=180, end=0, fill=color, width=w,
    )
    # Small circles inside (objects)
    or_ = s * 0.12
    for xo, yo in [(-0.2, 0.05), (0.15, -0.1), (0.0, 0.25)]:
        draw.ellipse(
            [cx + s*xo - or_, cy + s*yo - or_,
             cx + s*xo + or_, cy + s*yo + or_],
            outline=color, width=max(1, w-1),
        )


def draw_filesystem(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Filesystem — folder icon."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Folder tab
    draw.polygon([
        (cx - s, cy - s*0.4),
        (cx - s*0.3, cy - s*0.4),
        (cx - s*0.1, cy - s*0.65),
        (cx - s*0.7, cy - s*0.65),
    ], outline=color, fill=_with_alpha(color, 30))
    # Folder body
    draw.rounded_rectangle(
        [cx - s, cy - s*0.4, cx + s, cy + s*0.5],
        radius=max(2, int(size/25)),
        outline=color, width=w,
        fill=_with_alpha(color, 20),
    )


def draw_cache(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Cache — lightning bolt / fast storage."""
    s = size * 0.35
    w = max(2, int(size/16))
    # Lightning bolt shape
    points = [
        (cx + s*0.1, cy - s*0.8),    # top
        (cx - s*0.3, cy - s*0.05),   # mid-left
        (cx + s*0.05, cy - s*0.05),  # mid-center
        (cx - s*0.1, cy + s*0.8),    # bottom
        (cx + s*0.3, cy + s*0.05),   # mid-right
        (cx - s*0.05, cy + s*0.05),  # mid-center
    ]
    draw.polygon(points, outline=color, fill=_with_alpha(color, 40))


# ─── Service Icons ───────────────────────────────────────────────────

def draw_api(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """API — curly braces { }."""
    s = size * 0.35
    w = max(2, int(size/16))
    # Left brace {
    draw.arc(
        [cx - s*0.8, cy - s*0.7, cx - s*0.2, cy - s*0.05],
        start=270, end=0, fill=color, width=w,
    )
    draw.arc(
        [cx - s*0.8, cy + s*0.05, cx - s*0.2, cy + s*0.7],
        start=0, end=90, fill=color, width=w,
    )
    # Left point
    draw.line([(cx - s*0.8, cy - s*0.05), (cx - s*0.95, cy)], fill=color, width=w)
    draw.line([(cx - s*0.95, cy), (cx - s*0.8, cy + s*0.05)], fill=color, width=w)

    # Right brace }
    draw.arc(
        [cx + s*0.2, cy - s*0.7, cx + s*0.8, cy - s*0.05],
        start=180, end=270, fill=color, width=w,
    )
    draw.arc(
        [cx + s*0.2, cy + s*0.05, cx + s*0.8, cy + s*0.7],
        start=90, end=180, fill=color, width=w,
    )
    # Right point
    draw.line([(cx + s*0.8, cy - s*0.05), (cx + s*0.95, cy)], fill=color, width=w)
    draw.line([(cx + s*0.95, cy), (cx + s*0.8, cy + s*0.05)], fill=color, width=w)

    # Dot in center
    dr = max(2, size * 0.04)
    draw.ellipse([cx-dr, cy-dr, cx+dr, cy+dr], fill=color)


def draw_queue(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Message Queue — stacked envelopes / horizontal pipe with items."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Pipe outline
    draw.rounded_rectangle(
        [cx - s, cy - s*0.35, cx + s, cy + s*0.35],
        radius=max(3, int(s*0.35)),
        outline=color, width=w,
        fill=_with_alpha(color, 15),
    )
    # Items in queue (small squares)
    sq = s * 0.22
    for xoff in [-0.55, -0.15, 0.25, 0.65]:
        alpha = 50 + int(40 * (xoff + 0.55))  # gradient: older items fainter
        draw.rounded_rectangle(
            [cx + s*xoff - sq/2, cy - sq/2,
             cx + s*xoff + sq/2, cy + sq/2],
            radius=max(1, int(size/30)),
            outline=color, width=max(1, w-1),
            fill=_with_alpha(color, min(alpha, 100)),
        )
    # Arrow pointing right at exit
    draw.line([(cx + s*0.85, cy - s*0.15), (cx + s*1.05, cy)], fill=color, width=w)
    draw.line([(cx + s*0.85, cy + s*0.15), (cx + s*1.05, cy)], fill=color, width=w)


def draw_monitoring(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Monitoring — heartbeat/pulse line in a screen."""
    s = size * 0.38
    w = max(2, int(size/18))
    # Screen outline
    draw.rounded_rectangle(
        [cx - s, cy - s*0.6, cx + s, cy + s*0.45],
        radius=max(2, int(size/20)),
        outline=color, width=w,
        fill=_with_alpha(color, 15),
    )
    # Pulse / heartbeat line
    pw = max(2, int(size/20))
    points = [
        (cx - s*0.7, cy),
        (cx - s*0.35, cy),
        (cx - s*0.2, cy - s*0.35),
        (cx - s*0.05, cy + s*0.2),
        (cx + s*0.15, cy - s*0.25),
        (cx + s*0.3, cy + s*0.1),
        (cx + s*0.45, cy),
        (cx + s*0.7, cy),
    ]
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=color, width=pw)


def draw_logs(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Logs — scroll / document with lines."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Document
    draw.rounded_rectangle(
        [cx - s*0.7, cy - s*0.7, cx + s*0.7, cy + s*0.7],
        radius=max(2, int(size/25)),
        outline=color, width=w,
        fill=_with_alpha(color, 15),
    )
    # Lines of text
    for yoff in [-0.35, -0.1, 0.15, 0.4]:
        length = 0.8 if yoff != 0.4 else 0.5  # last line shorter
        draw.line(
            [(cx - s*0.4, cy + s*yoff), (cx + s*(length - 0.4), cy + s*yoff)],
            fill=color, width=max(1, w-1)
        )


def draw_search(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Search — magnifying glass."""
    s = size * 0.32
    w = max(2, int(size/16))
    # Circle (lens)
    draw.ellipse(
        [cx - s*0.6, cy - s*0.8, cx + s*0.5, cy + s*0.3],
        outline=color, width=w,
    )
    # Handle
    draw.line(
        [(cx + s*0.3, cy + s*0.15), (cx + s*0.8, cy + s*0.7)],
        fill=color, width=max(3, int(w*1.5)),
    )


# ─── Agent / AI Icons ───────────────────────────────────────────────

def draw_brain(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Brain / AI — brain lobes shape."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Left hemisphere
    draw.arc(
        [cx - s*0.9, cy - s*0.7, cx + s*0.1, cy + s*0.7],
        start=90, end=270, fill=color, width=w,
    )
    # Right hemisphere
    draw.arc(
        [cx - s*0.1, cy - s*0.7, cx + s*0.9, cy + s*0.7],
        start=270, end=90, fill=color, width=w,
    )
    # Center line
    draw.line([(cx, cy - s*0.5), (cx, cy + s*0.5)], fill=color, width=max(1, w-1))
    # Neural bumps (top)
    draw.arc(
        [cx - s*0.6, cy - s*0.9, cx, cy - s*0.2],
        start=200, end=340, fill=color, width=max(1, w-1),
    )
    draw.arc(
        [cx, cy - s*0.85, cx + s*0.6, cy - s*0.15],
        start=200, end=340, fill=color, width=max(1, w-1),
    )
    # Sparkle / AI indicator — small dots
    dr = max(2, size * 0.03)
    for xo, yo in [(-0.3, -0.15), (0.3, 0.0), (-0.1, 0.25)]:
        draw.ellipse(
            [cx + s*xo - dr, cy + s*yo - dr,
             cx + s*xo + dr, cy + s*yo + dr],
            fill=color,
        )


def draw_oracle(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Oracle — all-seeing eye."""
    s = size * 0.38
    w = max(2, int(size/16))
    # Eye outline (almond shape using arcs)
    draw.arc(
        [cx - s, cy - s*0.6, cx + s, cy + s*0.6],
        start=200, end=340, fill=color, width=w,
    )
    draw.arc(
        [cx - s, cy - s*0.6, cx + s, cy + s*0.6],
        start=20, end=160, fill=color, width=w,
    )
    # Iris (circle)
    ir = s * 0.3
    draw.ellipse(
        [cx - ir, cy - ir, cx + ir, cy + ir],
        outline=color, width=w,
        fill=_with_alpha(color, 40),
    )
    # Pupil (filled circle)
    pr = s * 0.14
    draw.ellipse(
        [cx - pr, cy - pr, cx + pr, cy + pr],
        fill=color,
    )


def draw_worker(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Worker — wrench / gear + hand."""
    s = size * 0.33
    w = max(2, int(size/16))
    # Gear (outer)
    draw.ellipse(
        [cx - s*0.5, cy - s*0.5, cx + s*0.5, cy + s*0.5],
        outline=color, width=w,
    )
    # Inner circle
    ir = s * 0.2
    draw.ellipse(
        [cx - ir, cy - ir, cx + ir, cy + ir],
        outline=color, width=max(1, w-1),
        fill=_with_alpha(color, 30),
    )
    # Gear teeth (8 teeth)
    for i in range(8):
        angle = math.radians(45 * i)
        x1 = cx + s*0.42 * math.cos(angle)
        y1 = cy + s*0.42 * math.sin(angle)
        x2 = cx + s*0.65 * math.cos(angle)
        y2 = cy + s*0.65 * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=max(2, w))
    # Handle extending down-right
    draw.line(
        [(cx + s*0.35, cy + s*0.35), (cx + s*0.85, cy + s*0.85)],
        fill=color, width=max(2, w),
    )


def draw_bus(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Message Bus — horizontal bar with vertical connectors."""
    s = size * 0.4
    w = max(2, int(size/16))
    # Main bus line (horizontal)
    draw.line(
        [(cx - s, cy), (cx + s, cy)],
        fill=color, width=max(3, int(w * 1.5)),
    )
    # Vertical connectors (taps)
    for xoff in [-0.6, -0.2, 0.2, 0.6]:
        x = cx + s * xoff
        draw.line([(x, cy - s*0.5), (x, cy)], fill=color, width=w)
        draw.line([(x, cy), (x, cy + s*0.5)], fill=color, width=w)
        # Small circles at ends
        cr = max(2, size * 0.04)
        draw.ellipse([x-cr, cy-s*0.5-cr, x+cr, cy-s*0.5+cr], fill=color)
        draw.ellipse([x-cr, cy+s*0.5-cr, x+cr, cy+s*0.5+cr], fill=color)


# ─── General Icons ───────────────────────────────────────────────────

def draw_lock(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Lock / security."""
    s = size * 0.32
    w = max(2, int(size/18))
    # Lock body
    draw.rounded_rectangle(
        [cx - s*0.6, cy - s*0.1, cx + s*0.6, cy + s*0.7],
        radius=max(2, int(size/25)),
        outline=color, width=w,
        fill=_with_alpha(color, 25),
    )
    # Shackle
    draw.arc(
        [cx - s*0.4, cy - s*0.7, cx + s*0.4, cy + s*0.1],
        start=180, end=0, fill=color, width=w,
    )
    # Keyhole
    kr = max(2, size * 0.04)
    draw.ellipse([cx-kr, cy+s*0.15-kr, cx+kr, cy+s*0.15+kr], fill=color)
    draw.line([(cx, cy+s*0.15), (cx, cy+s*0.4)], fill=color, width=max(1, w-1))


def draw_key(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Key."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Key head (circle)
    kr = s * 0.3
    draw.ellipse(
        [cx - s*0.6 - kr, cy - kr, cx - s*0.6 + kr, cy + kr],
        outline=color, width=w,
    )
    # Key shaft
    draw.line([(cx - s*0.6 + kr, cy), (cx + s*0.7, cy)], fill=color, width=w)
    # Key teeth
    for xoff in [0.35, 0.55]:
        draw.line(
            [(cx + s*xoff, cy), (cx + s*xoff, cy + s*0.3)],
            fill=color, width=max(1, w-1)
        )


def draw_globe(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Globe / internet."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Outer circle
    draw.ellipse(
        [cx - s, cy - s, cx + s, cy + s],
        outline=color, width=w,
    )
    # Meridian (vertical ellipse)
    draw.ellipse(
        [cx - s*0.35, cy - s, cx + s*0.35, cy + s],
        outline=color, width=max(1, w-1),
    )
    # Equator
    draw.line([(cx - s, cy), (cx + s, cy)], fill=color, width=max(1, w-1))
    # Tropic lines
    draw.arc(
        [cx - s, cy - s*0.7, cx + s, cy - s*0.1],
        start=10, end=170, fill=color, width=max(1, w-1),
    )
    draw.arc(
        [cx - s, cy + s*0.1, cx + s, cy + s*0.7],
        start=190, end=350, fill=color, width=max(1, w-1),
    )


def draw_user(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Single user."""
    s = size * 0.32
    w = max(2, int(size/18))
    # Head
    hr = s * 0.3
    draw.ellipse(
        [cx - hr, cy - s*0.6 - hr, cx + hr, cy - s*0.6 + hr],
        outline=color, width=w,
    )
    # Body (arc)
    draw.arc(
        [cx - s*0.6, cy - s*0.1, cx + s*0.6, cy + s*0.8],
        start=200, end=340, fill=color, width=w,
    )


def draw_users(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Multiple users / team."""
    # Front user
    draw_user(draw, cx + size*0.05, cy, size * 0.85, color)
    # Back user (offset, slightly transparent)
    lighter = _lighten(color, 0.3)
    draw_user(draw, cx - size*0.1, cy - size*0.02, size * 0.75, lighter)


def draw_gear(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Gear / settings — same as worker but standalone."""
    s = size * 0.35
    w = max(2, int(size/16))
    # Outer circle with teeth
    draw.ellipse(
        [cx - s*0.5, cy - s*0.5, cx + s*0.5, cy + s*0.5],
        outline=color, width=w,
    )
    ir = s * 0.22
    draw.ellipse(
        [cx - ir, cy - ir, cx + ir, cy + ir],
        outline=color, width=max(1, w-1),
        fill=_with_alpha(color, 30),
    )
    for i in range(8):
        angle = math.radians(45 * i + 22.5)
        x1 = cx + s*0.42 * math.cos(angle)
        y1 = cy + s*0.42 * math.sin(angle)
        x2 = cx + s*0.65 * math.cos(angle)
        y2 = cy + s*0.65 * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=max(2, w))


def draw_bell(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Notification bell."""
    s = size * 0.35
    w = max(2, int(size/18))
    # Bell body
    draw.arc(
        [cx - s*0.6, cy - s*0.8, cx + s*0.6, cy + s*0.2],
        start=180, end=0, fill=color, width=w,
    )
    # Sides
    draw.line([(cx - s*0.6, cy + s*0.2), (cx - s*0.8, cy + s*0.5)], fill=color, width=w)
    draw.line([(cx + s*0.6, cy + s*0.2), (cx + s*0.8, cy + s*0.5)], fill=color, width=w)
    # Bottom rim
    draw.line([(cx - s*0.8, cy + s*0.5), (cx + s*0.8, cy + s*0.5)], fill=color, width=w)
    # Clapper
    cr = max(2, size * 0.05)
    draw.ellipse([cx-cr, cy+s*0.5, cx+cr, cy+s*0.5+cr*2], fill=color)
    # Top knob
    draw.ellipse([cx-cr, cy-s*0.85, cx+cr, cy-s*0.85+cr*2], fill=color)


def draw_mail(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Email / message."""
    s = size * 0.38
    w = max(2, int(size/18))
    # Envelope body
    draw.rounded_rectangle(
        [cx - s, cy - s*0.4, cx + s, cy + s*0.4],
        radius=max(2, int(size/25)),
        outline=color, width=w,
        fill=_with_alpha(color, 15),
    )
    # Envelope flap (V shape)
    draw.line([(cx - s, cy - s*0.4), (cx, cy + s*0.1)], fill=color, width=w)
    draw.line([(cx + s, cy - s*0.4), (cx, cy + s*0.1)], fill=color, width=w)


def draw_network(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color: str):
    """Network topology — nodes connected by lines."""
    s = size * 0.35
    w = max(2, int(size/18))
    cr = max(3, size * 0.06)
    # Three interconnected nodes
    positions = [
        (cx, cy - s*0.5),       # top
        (cx - s*0.5, cy + s*0.4),  # bottom-left
        (cx + s*0.5, cy + s*0.4),  # bottom-right
    ]
    # Lines between all nodes
    for i in range(3):
        for j in range(i+1, 3):
            draw.line([positions[i], positions[j]], fill=color, width=max(1, w-1))
    # Nodes
    for px, py in positions:
        draw.ellipse(
            [px-cr, py-cr, px+cr, py+cr],
            outline=color, fill=_with_alpha(color, 60), width=max(1, w-1),
        )
    # Center node
    draw.ellipse(
        [cx-cr*0.8, cy-cr*0.8+s*0.1, cx+cr*0.8, cy+cr*0.8+s*0.1],
        fill=color,
    )


# ─── Registry ───────────────────────────────────────────────────────

ICON_REGISTRY: dict[str, IconDrawFn] = {
    # Cloud
    "cloud": draw_cloud,
    "aws": draw_aws,
    "gcp": draw_gcp,
    "azure": draw_azure,

    # Compute
    "server": draw_server,
    "vm": draw_vm,
    "container": draw_container,
    "docker": draw_container,
    "pod": draw_pod,
    "k8s": draw_pod,
    "kubernetes": draw_pod,
    "lambda": draw_lambda,
    "serverless": draw_lambda,
    "function": draw_lambda,

    # Networking
    "loadbalancer": draw_loadbalancer,
    "lb": draw_loadbalancer,
    "gateway": draw_gateway,
    "firewall": draw_firewall,
    "cdn": draw_cdn,
    "dns": draw_dns,

    # Storage
    "database": draw_database,
    "db": draw_database,
    "objectstore": draw_objectstore,
    "s3": draw_objectstore,
    "bucket": draw_objectstore,
    "filesystem": draw_filesystem,
    "folder": draw_filesystem,
    "cache": draw_cache,
    "redis": draw_cache,

    # Services
    "api": draw_api,
    "queue": draw_queue,
    "mq": draw_queue,
    "sqs": draw_queue,
    "kafka": draw_queue,
    "monitoring": draw_monitoring,
    "metrics": draw_monitoring,
    "grafana": draw_monitoring,
    "logs": draw_logs,
    "search": draw_search,

    # Agent / AI
    "brain": draw_brain,
    "ai": draw_brain,
    "oracle": draw_oracle,
    "eye": draw_oracle,
    "worker": draw_worker,
    "bus": draw_bus,

    # General
    "lock": draw_lock,
    "security": draw_lock,
    "key": draw_key,
    "globe": draw_globe,
    "internet": draw_globe,
    "web": draw_globe,
    "user": draw_user,
    "users": draw_users,
    "team": draw_users,
    "gear": draw_gear,
    "settings": draw_gear,
    "bell": draw_bell,
    "notification": draw_bell,
    "alert": draw_bell,
    "mail": draw_mail,
    "email": draw_mail,
    "network": draw_network,
    "topology": draw_network,
}


def get_icon_names() -> list[str]:
    """Return sorted list of available icon names."""
    return sorted(ICON_REGISTRY.keys())


def draw_icon(
    draw: ImageDraw.ImageDraw,
    icon_name: str,
    cx: float,
    cy: float,
    size: float,
    color: str,
) -> bool:
    """Draw a named icon. Returns True if icon was found and drawn."""
    fn = ICON_REGISTRY.get(icon_name.lower().strip())
    if fn is None:
        return False
    fn(draw, cx, cy, size, color)
    return True
