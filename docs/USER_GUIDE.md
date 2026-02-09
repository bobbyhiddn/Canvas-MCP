# Canvas-MCP User Guide

This guide covers every MCP tool exposed by Canvas-MCP, with practical examples and parameter references.

## Overview

Canvas-MCP provides four tools through the [Model Context Protocol](https://modelcontextprotocol.io):

| Tool | Purpose |
|------|---------|
| [`render_canvas`](#render_canvas) | Render a YAML recipe string to a PNG diagram |
| [`create_canvas`](#create_canvas) | Create a diagram from structured input (title + nodes + optional machines) |
| [`list_templates`](#list_templates) | List available starter templates |
| [`get_template`](#get_template) | Retrieve the YAML content of a specific template |

All tools communicate over MCP's stdio transport. Output PNGs are saved to `~/.rhode/canvas/` by default (configurable via the `CANVAS_OUTPUT_DIR` environment variable).

---

## render_canvas

Render a YAML recipe string directly to a PNG image. This is the most flexible tool — you provide the full YAML and control every aspect of the diagram.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `yaml_recipe` | string | **Yes** | — | YAML string in either [simplified](YAML_REFERENCE.md#simplified-format) or [hierarchical](YAML_REFERENCE.md#hierarchical-format) format |
| `scale` | number | No | `2.0` | Render scale factor. `2.0` produces crisp retina-quality output. Use `1.0` for smaller files. |
| `filename` | string | No | Auto-generated UUID | Output filename (without `.png` extension) |
| `organize` | boolean | No | `true` | Apply the hierarchical organize algorithm for automatic layout |
| `spacing_level` | string | No | `"container"` | Spacing preset: `"node"`, `"container"`, or `"network"` |
| `orientation` | string | No | `"horizontal"` | Layout direction: `"horizontal"` (left-to-right) or `"vertical"` (top-to-bottom) |

### Returns

A JSON object with:

```json
{
  "status": "success",
  "path": "/home/user/.rhode/canvas/my-diagram.png",
  "title": "My Diagram",
  "nodes": 5,
  "connections": 4,
  "organized": true,
  "spacing_level": "container",
  "orientation": "horizontal"
}
```

### Example: Simple Pipeline

```yaml
# Pass this as the yaml_recipe parameter
title: Data Pipeline

nodes:
  - id: ingest
    type: input
    label: "Data Ingest"
    content: "Accept incoming data from external sources"

  - id: clean
    type: process
    label: "Clean & Validate"
    content: "Normalize formats, remove duplicates"
    inputs: [ingest]

  - id: analyze
    type: ai
    label: "AI Analysis"
    content: "Run LLM inference on cleaned data"
    inputs: [clean]

  - id: report
    type: output
    label: "Report"
    content: "Generated summary document"
    inputs: [analyze]
```

With `organize: true` and `orientation: "horizontal"`, this produces a left-to-right flow diagram with four nodes connected by bezier curves.

### Example: Hierarchical Architecture

```yaml
# Pass this as the yaml_recipe parameter
canvas:
  version: "2.0"
  title: Microservice Architecture

  networks:
    - id: production
      label: "Production System"

      factories:
        - id: ingestion
          label: "Data Ingestion"
          machines:
            - id: api-layer
              label: "API Layer"
              nodes:
                - id: rest-api
                  type: input
                  label: "REST API"
                  content: "Public-facing endpoint"
                  outputs: [validator]

                - id: validator
                  type: process
                  label: "Validator"
                  content: "Schema validation"
                  inputs: [rest-api]
                  outputs: [queue]

            - id: messaging
              label: "Message Queue"
              nodes:
                - id: queue
                  type: process
                  label: "Queue"
                  content: "Async message buffer"
                  inputs: [validator]
                  outputs: [worker]

        - id: processing
          label: "Processing"
          machines:
            - id: workers
              label: "Workers"
              nodes:
                - id: worker
                  type: process
                  label: "Worker"
                  content: "Process queued items"
                  inputs: [queue]
                  outputs: [result]

                - id: result
                  type: output
                  label: "Result"
                  content: "Processed output"
                  inputs: [worker]
```

### Example: Vertical Tree Layout

Use `orientation: "vertical"` for top-to-bottom diagrams, ideal for decision trees or organizational charts:

```yaml
title: Decision Tree

nodes:
  - id: start
    type: decision
    label: "Is it urgent?"
    content: "Check priority level"

  - id: yes-path
    type: process
    label: "Escalate"
    content: "Route to on-call team"
    inputs: [start]

  - id: no-path
    type: process
    label: "Queue"
    content: "Add to backlog"
    inputs: [start]

  - id: resolve
    type: output
    label: "Resolved"
    content: "Issue closed"
    inputs: [yes-path, no-path]
```

### Spacing Levels

The `spacing_level` parameter controls how much breathing room the layout algorithm applies:

| Level | Horizontal Gap | Vertical Gap | Best For |
|-------|---------------|-------------|----------|
| `"node"` | 90px | 140px | Small, tight diagrams (3-6 nodes) |
| `"container"` | 200px | 240px | Architecture diagrams (default) |
| `"network"` | 260px | 320px | Large system overviews with many containers |

These values are applied at the **container level** (machines within factories, factories within networks). Node-level spacing within machines is always tight (90px/140px) to keep pipelines compact.

---

## create_canvas

Create a diagram from structured input without writing YAML. You provide a title and a list of node objects — Canvas-MCP builds the hierarchy, renders the PNG, and also saves the generated YAML recipe for future editing.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `title` | string | **Yes** | — | Title displayed at the top of the diagram |
| `nodes` | array | **Yes** | — | List of node definitions (see below) |
| `machines` | array | No | Auto-detected | Optional: manually group nodes into named machines |
| `scale` | number | No | `2.0` | Render scale factor |
| `organize` | boolean | No | `true` | Apply hierarchical layout algorithm |
| `spacing_level` | string | No | `"container"` | Spacing preset |
| `orientation` | string | No | `"horizontal"` | Layout direction |

#### Node Definition

Each node in the `nodes` array is an object:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | **Yes** | — | Unique identifier (used for connections) |
| `type` | string | **Yes** | — | One of: `input`, `output`, `process`, `decision`, `ai`, `source`, `static`, `default` |
| `content` | string | **Yes** | — | Body text describing what the node does |
| `label` | string | No | Uses `id` | Human-readable display name |
| `inputs` | array of strings | No | `[]` | IDs of nodes that feed into this one |

#### Machine Definition

Each machine in the optional `machines` array:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | **Yes** | — | Unique machine identifier |
| `label` | string | No | Uses `id` | Display name for the machine container |
| `node_ids` | array of strings | **Yes** | — | IDs of nodes that belong to this machine |

### Returns

A JSON object with:

```json
{
  "status": "success",
  "png_path": "/home/user/.rhode/canvas/my-diagram-a1b2.png",
  "yaml_path": "/home/user/.rhode/canvas/my-diagram-a1b2.yaml",
  "title": "My Diagram",
  "nodes": 5,
  "connections": 4,
  "machines": 2
}
```

Note that `create_canvas` returns **both** a PNG path and a YAML path. The saved YAML can be loaded later with `render_canvas` for modifications.

### Example: Basic Nodes

```json
{
  "title": "ETL Pipeline",
  "nodes": [
    {
      "id": "extract",
      "type": "source",
      "content": "Pull data from PostgreSQL",
      "label": "Extract"
    },
    {
      "id": "transform",
      "type": "process",
      "content": "Clean, normalize, and deduplicate records",
      "label": "Transform",
      "inputs": ["extract"]
    },
    {
      "id": "load",
      "type": "output",
      "content": "Write to data warehouse",
      "label": "Load",
      "inputs": ["transform"]
    }
  ]
}
```

### Example: With Manual Machine Grouping

```json
{
  "title": "Data Processing System",
  "nodes": [
    {"id": "api", "type": "input", "content": "REST API endpoint", "label": "API"},
    {"id": "validate", "type": "process", "content": "Schema validation", "inputs": ["api"]},
    {"id": "enrich", "type": "ai", "content": "AI enrichment", "inputs": ["validate"]},
    {"id": "store", "type": "output", "content": "Write to database", "inputs": ["enrich"]},
    {"id": "notify", "type": "output", "content": "Send notifications", "inputs": ["enrich"]}
  ],
  "machines": [
    {"id": "ingestion", "label": "Ingestion", "node_ids": ["api", "validate"]},
    {"id": "processing", "label": "Processing", "node_ids": ["enrich"]},
    {"id": "output", "label": "Output", "node_ids": ["store", "notify"]}
  ]
}
```

When `machines` is omitted, Canvas-MCP automatically detects machines from node connectivity — each connected component of nodes becomes its own machine.

When `machines` is provided, any nodes not listed in any machine are placed in an auto-generated catch-all machine.

---

## list_templates

List all available YAML recipe templates. Templates are starter recipes you can use as-is or modify for your own diagrams.

### Parameters

None.

### Returns

A JSON object with a list of templates:

```json
{
  "templates": [
    {"name": "simple-flow", "path": "/path/to/templates/simple-flow.yaml"},
    {"name": "ai-pipeline", "path": "/path/to/templates/ai-pipeline.yaml"},
    {"name": "decision-tree", "path": "/path/to/templates/decision-tree.yaml"},
    {"name": "ci-cd-pipeline", "path": "/path/to/templates/ci-cd-pipeline.yaml"},
    {"name": "microservice-architecture", "path": "/path/to/templates/microservice-architecture.yaml"},
    {"name": "issue-triage-decision-tree", "path": "/path/to/templates/issue-triage-decision-tree.yaml"}
  ]
}
```

### Available Templates

| Template | Format | Description |
|----------|--------|-------------|
| `simple-flow` | Simplified | A 3-node linear pipeline (input -> process -> output) |
| `ai-pipeline` | Hierarchical | Full hierarchical example with 2 factories, 3 machines, and cross-machine connections |
| `decision-tree` | Simplified | Branching decision flow with multiple paths |
| `ci-cd-pipeline` | Hierarchical | Build/test/deploy stages with parallel jobs |
| `microservice-architecture` | Hierarchical | Services, APIs, data stores across multiple factories |
| `issue-triage-decision-tree` | Simplified | Multi-level triage decision flow |

---

## get_template

Retrieve the full YAML content of a specific template by name. Use the name from `list_templates` output (without the file extension).

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | **Yes** | Template name (e.g., `"simple-flow"`, `"ai-pipeline"`) |

### Returns

The raw YAML content as a text string. You can then:
1. Pass it directly to `render_canvas` to render it as-is
2. Modify it and pass the modified version to `render_canvas`
3. Use it as a reference for building your own recipes

### Example Workflow

A typical workflow using templates:

1. **List available templates:**
   ```
   list_templates → see what's available
   ```

2. **Get a template to start from:**
   ```
   get_template(name="ai-pipeline") → get the YAML content
   ```

3. **Modify and render:**
   ```
   render_canvas(yaml_recipe=<modified YAML>, organize=true) → get PNG
   ```

---

## Common Patterns

### Rendering a Quick Diagram

For the fastest path from idea to PNG, use `create_canvas` with just a title and nodes:

```json
{
  "title": "My Idea",
  "nodes": [
    {"id": "a", "type": "input", "content": "Step 1"},
    {"id": "b", "type": "process", "content": "Step 2", "inputs": ["a"]},
    {"id": "c", "type": "output", "content": "Step 3", "inputs": ["b"]}
  ]
}
```

### Iterating on a Diagram

1. Use `create_canvas` to get an initial diagram + saved YAML
2. Read the saved YAML file
3. Edit the YAML (add nodes, change labels, adjust hierarchy)
4. Use `render_canvas` with the modified YAML to re-render

### Using Templates as Starting Points

1. `list_templates` to see what's available
2. `get_template` to fetch the YAML
3. Modify the YAML for your use case
4. `render_canvas` to produce the diagram

### Controlling Layout Quality

- **`organize: true`** (default) — uses the topological sort algorithm for intelligent flow-based layout. This is almost always what you want.
- **`organize: false`** — uses raw node coordinates from the YAML. Only useful if you've manually positioned every node.
- **`spacing_level: "node"`** — tight layout for small diagrams
- **`spacing_level: "network"`** — spacious layout for complex multi-factory diagrams
- **`orientation: "vertical"`** — top-to-bottom flow, good for trees and decision flows

### Node Type Selection Guide

Choose the right node type based on what the node represents:

| If the node... | Use type |
|----------------|----------|
| Receives external input / user data | `input` |
| Produces the final result | `output` |
| Transforms or processes data | `process` |
| Makes a decision or branches | `decision` |
| Involves AI/LLM processing | `ai` |
| Fetches from an external source (API, DB) | `source` |
| Holds constant/seed data | `static` |
| Doesn't fit the above | `default` |

---

## Error Handling

Both `render_canvas` and `create_canvas` return error messages as text if something goes wrong:

- **YAML parse errors:** `"Failed to parse YAML recipe: <details>"`
- **Rendering errors:** `"Rendering failed: <details>"`
- **Template not found:** `"Template not found: <name>"`

Common issues:
- **Missing `id` field** on a node — every node must have a unique `id`
- **Invalid `inputs` reference** — referencing a node ID that doesn't exist (the connection is silently skipped)
- **Malformed YAML** — check indentation and quoting
