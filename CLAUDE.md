# Canvas-MCP

MCP server for creating Thoughtorio-style canvas diagrams as PNGs.

## Architecture

- **`src/canvas_mcp/models.py`** — Pydantic data models (Canvas, Network, Factory, Machine, Node)
- **`src/canvas_mcp/parser.py`** — YAML recipe parser (supports Thoughtorio format + simplified format)
- **`src/canvas_mcp/renderer.py`** — Pillow-based PNG renderer with Catppuccin dark theme
- **`src/canvas_mcp/server.py`** — MCP server with tools: `render_canvas`, `create_canvas`, `list_templates`, `get_template`
- **`templates/`** — Starter recipe templates

## Running

```bash
uv run canvas-mcp   # Starts MCP stdio server
```

## Node Types & Colors

| Type | Color | Use |
|------|-------|-----|
| `input` | Blue (#2196F3) | User input / prompts |
| `ai` | Purple (#9C27B0) | AI processing nodes |
| `static` | Green (#4CAF50) | Immutable seed content |
| `source` | Orange (#FF9800) | External data sources |
| `output` | Amber (#FFC107) | Final outputs |
| `decision` | Red (#F44336) | Decision points |
| `process` | Cyan (#00BCD4) | Processing steps |
| `default` | Gray (#999) | Generic nodes |

## YAML Formats

### Simplified (auto-layout)
```yaml
title: My Diagram
nodes:
  - id: start
    type: input
    content: "Begin"
    outputs: [next]
  - id: next
    type: process
    content: "Do work"
    inputs: [start]
```

### Thoughtorio-compatible (explicit coordinates)
```yaml
canvas:
  version: "2.0"
  title: My Canvas
  networks:
    - id: network-1
      factories:
        - id: factory-1
          machines:
            - id: machine-1
              nodes:
                - id: node-1
                  type: input
                  x: 100
                  y: 100
                  content: "Hello"
```

## Testing

```bash
uv run python test_render.py  # Renders test PNGs to output/
```
