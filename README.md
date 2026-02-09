# Canvas-MCP

**Hierarchical canvas diagram renderer for the Model Context Protocol.**

Define your system as a hierarchy of networks, factories, machines, and nodes — Canvas-MCP handles layout, styling, and rendering to crisp PNG diagrams.

Built with Python, Pillow, and the [Model Context Protocol](https://modelcontextprotocol.io).

## Quick Start

### 1. Add to your MCP client

Add Canvas-MCP to your MCP client configuration (e.g., `.mcp.json`):

```json
{
  "mcpServers": {
    "canvas-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/Canvas-MCP", "canvas-mcp"]
    }
  }
}
```

### 2. Create your first diagram

Use the `render_canvas` tool with a simple YAML recipe:

```yaml
title: My First Diagram

nodes:
  - id: start
    type: input
    content: "Data comes in"
    outputs: [process]

  - id: process
    type: process
    content: "Transform it"
    inputs: [start]
    outputs: [result]

  - id: result
    type: output
    content: "Results go out"
    inputs: [process]
```

That's it. Canvas-MCP handles layout, styling, and rendering automatically.

### 3. Or use structured input

Use the `create_canvas` tool for code-driven diagrams — pass a title and node list directly without writing YAML:

```json
{
  "title": "ETL Pipeline",
  "nodes": [
    {"id": "extract", "type": "source", "content": "Pull from DB"},
    {"id": "transform", "type": "process", "content": "Clean data", "inputs": ["extract"]},
    {"id": "load", "type": "output", "content": "Write to warehouse", "inputs": ["transform"]}
  ]
}
```

## Features

- **Four-level hierarchy** — Canvas > Network > Factory > Machine > Node. Express both micro operations and macro architecture in one diagram.
- **Eight semantic node types** — `input`, `output`, `process`, `decision`, `ai`, `source`, `static`, `default` — each color-coded with the Catppuccin Mocha palette.
- **Intelligent auto-layout** — Topological sort with parent-center alignment, overlap prevention, cycle handling, and connector avoidance.
- **Two YAML formats** — Simplified (flat node list) for quick diagrams, hierarchical (networks/factories/machines) for complex architectures.
- **Smart port selection** — Connections automatically use horizontal or vertical ports based on node geometry.
- **Bezier curve connections** — Smooth S-bend curves with arrowheads, colored by source node type.
- **Auto-sizing nodes** — Node dimensions automatically calculated from text content.
- **Container styling** — Customize machine and factory containers with colors, opacity, border radius.
- **Custom node styles** — Override any node's border, fill, text, and corner radius.
- **Template system** — Starter recipes for common diagram patterns.
- **Dual output** — `create_canvas` saves both PNG and YAML for later editing.

## MCP Tools

| Tool | Description |
|------|-------------|
| `render_canvas` | Render a YAML recipe string to PNG |
| `create_canvas` | Create a diagram from structured input (title + nodes + optional machines) |
| `list_templates` | List available starter templates |
| `get_template` | Retrieve template YAML content by name |

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** — How to use each MCP tool with examples, parameter references, and common patterns
- **[YAML Reference](docs/YAML_REFERENCE.md)** — Complete reference for the YAML recipe format: node types, connections, hierarchy, container styling, and layout options

## The Ontology

Canvas-MCP uses a four-level hierarchical ontology. Every diagram is a tree of nested containers:

```
Canvas
└── Network       ← system boundary
    └── Factory   ← functional domain
        └── Machine   ← pipeline
            └── Node      ← atomic operation
```

- **Network** — the broadest boundary. A service, deployment, or subsystem.
- **Factory** — a functional domain. "Data Ingestion", "Analysis", "Output Generation".
- **Machine** — a pipeline. A connected chain of operations.
- **Node** — the atomic unit. A single operation, decision, or data source.

## Node Types

| Type | Color | Meaning |
|------|-------|---------|
| `input` | Blue | User-provided data entering the system |
| `output` | Amber | Final results leaving the system |
| `process` | Cyan | A transformation or computation step |
| `decision` | Red | A branching point or conditional gate |
| `ai` | Purple | An AI/LLM processing step |
| `source` | Orange | An external data source (API, database, file) |
| `static` | Green | Immutable seed content or constants |
| `default` | Gray | Generic / unspecified |

## YAML Formats

### Simplified (flat list)

```yaml
title: My Pipeline
nodes:
  - id: start
    type: input
    content: "Begin"
    outputs: [next]
  - id: next
    type: process
    content: "Process"
    inputs: [start]
```

### Hierarchical (full control)

```yaml
canvas:
  title: My Architecture
  networks:
    - id: system
      factories:
        - id: data-layer
          label: "Data Layer"
          machines:
            - id: pipeline
              label: "ETL Pipeline"
              nodes:
                - id: extract
                  type: source
                  content: "Pull data"
                  outputs: [transform]
                - id: transform
                  type: process
                  content: "Clean data"
                  inputs: [extract]
```

See the [YAML Reference](docs/YAML_REFERENCE.md) for the complete format specification.

## Layout System

Canvas-MCP includes a built-in topological layout engine with hierarchical organization:

1. **Topological sort** (Kahn's algorithm) assigns flow-based levels
2. **Parent-center alignment** vertically centers children on their parents
3. **Overlap prevention** enforces minimum spacing between nodes
4. **Connector avoidance** nudges nodes away from bezier paths
5. **Grid fallback** arranges disconnected components

### Layout Options

| Option | Values | Description |
|--------|--------|-------------|
| `organize` | `true`/`false` | Enable intelligent layout (default: `true`) |
| `spacing_level` | `node`, `container`, `network` | Breathing room preset |
| `orientation` | `horizontal`, `vertical` | Flow direction |

## Templates

Canvas-MCP ships with starter templates for common diagram patterns:

| Template | Description |
|----------|-------------|
| `simple-flow` | 3-node linear pipeline |
| `ai-pipeline` | Full hierarchical AI processing example |
| `decision-tree` | Branching decision flow |
| `ci-cd-pipeline` | Build/test/deploy stages |
| `microservice-architecture` | Services, APIs, and data stores |
| `issue-triage-decision-tree` | Multi-level triage decisions |

Use `list_templates` and `get_template` to browse and retrieve them.

## Examples

The `examples/` directory contains real-world recipes at scale:

- **`rhode-architecture.yaml`** — Full system architecture (4 networks, 7 factories, 20+ nodes, custom styling)
- **`concurrency-test.yaml`** — Fan-out/fan-in risk analysis pipeline
- **`etymology-factory.yaml`** — Parallel analysis branches converging into a study
- **`risk-chain.yaml`** — Sequential machines with parallel decision tracks
- **`network-container-spacing-demo.yaml`** — Multi-factory spacing demo
- **`color-codes.yaml`** — Context propagation across container boundaries

See [`examples/README.md`](examples/README.md) for full descriptions.

## Installation

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### As an MCP Server

```json
{
  "mcpServers": {
    "canvas-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/Canvas-MCP", "canvas-mcp"]
    }
  }
}
```

### Running Directly

```bash
uv run canvas-mcp   # Starts the MCP stdio server
```

### Running Tests

```bash
uv run pytest        # Run the test suite
```

## Output

PNGs are saved to `~/.rhode/canvas/` by default. Set the `CANVAS_OUTPUT_DIR` environment variable to change the output directory.

## Project Structure

```
Canvas-MCP/
├── src/canvas_mcp/
│   ├── models.py       # Ontology: Canvas > Network > Factory > Machine > Node
│   ├── parser.py       # YAML parser (simplified + hierarchical formats)
│   ├── renderer.py     # Pillow-based PNG renderer
│   ├── organize.py     # Hierarchical layout algorithm (topological sort)
│   └── server.py       # MCP server with 4 tools
├── docs/
│   ├── USER_GUIDE.md   # Tool usage guide with examples
│   └── YAML_REFERENCE.md  # Complete YAML format reference
├── templates/          # Starter recipe templates
├── examples/           # Real-world example recipes
├── tests/              # Test suite
└── pyproject.toml
```

## Visual Theme

Canvas-MCP uses the **Catppuccin Mocha** dark theme throughout:

| Element | Color |
|---------|-------|
| Canvas background | `#11111b` |
| Node fill | `#1e1e2e` |
| Node labels | `#cdd6f4` |
| Node content | `#a6adc8` |
| Machine containers | `#181825` (semi-transparent) |
| Factory containers | `#45475a` (outline only) |

## License

MIT
