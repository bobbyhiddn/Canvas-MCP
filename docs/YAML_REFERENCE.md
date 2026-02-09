# Canvas-MCP YAML Reference

Complete reference for the Canvas-MCP YAML recipe format. This document covers both the simplified and hierarchical formats, all node types, connection syntax, container styling, and layout options.

## Table of Contents

- [Two Formats](#two-formats)
- [Simplified Format](#simplified-format)
- [Hierarchical Format](#hierarchical-format)
- [Nodes](#nodes)
  - [Node Fields](#node-fields)
  - [Node Types](#node-types)
  - [Custom Node Styling](#custom-node-styling)
- [Connections](#connections)
  - [Declaring Connections](#declaring-connections)
  - [Bidirectional Deduplication](#bidirectional-deduplication)
  - [Smart Port Selection](#smart-port-selection)
- [The Hierarchy](#the-hierarchy)
  - [Canvas (Root)](#canvas-root)
  - [Network](#network)
  - [Factory](#factory)
  - [Machine](#machine)
- [Container Styling](#container-styling)
- [Layout & Auto-Organization](#layout--auto-organization)
  - [Auto-Layout (Basic)](#auto-layout-basic)
  - [Organize Algorithm](#organize-algorithm)
  - [Spacing Levels](#spacing-levels)
  - [Orientation](#orientation)
  - [Connector Avoidance](#connector-avoidance)
- [Complete Examples](#complete-examples)

---

## Two Formats

Canvas-MCP accepts YAML in two formats. The parser auto-detects which format you're using based on whether the top-level key is `canvas` (hierarchical) or not (simplified).

| Format | Key | Hierarchy | Best For |
|--------|-----|-----------|----------|
| Simplified | `title` + `nodes` | Auto-generated (1 network > 1 factory > 1 machine) | Quick diagrams, flat pipelines |
| Hierarchical | `canvas` | Explicit (networks > factories > machines > nodes) | Complex architectures, multi-domain systems |

---

## Simplified Format

The simplest way to define a diagram. Provide a `title` and a flat list of `nodes`. Canvas-MCP wraps them in a single network > factory > machine automatically.

### Structure

```yaml
title: "My Diagram"                # Required. Displayed at top of canvas.
background: "#11111b"              # Optional. Canvas background color. Default: "#11111b"

nodes:                             # Required. List of node definitions.
  - id: node-1                     # Required. Globally unique identifier.
    type: input                    # Optional. Node type. Default: "default"
    label: "Display Name"          # Optional. Display name. Default: uses id.
    content: "Description text"    # Optional. Body text.
    x: 0                           # Optional. X position. Default: 0 (auto-layout)
    y: 0                           # Optional. Y position. Default: 0 (auto-layout)
    width: 250                     # Optional. Width in pixels. Default: 250
    height: 120                    # Optional. Height in pixels. Default: 120
    inputs: [other-node-id]        # Optional. IDs of upstream nodes.
    outputs: [another-node-id]     # Optional. IDs of downstream nodes.
    style:                         # Optional. Custom NodeStyle override.
      border_color: "#FF00FF"
      fill_color: "#1e1e2e"
      text_color: "#cdd6f4"

  - id: node-2
    type: process
    content: "Next step"
    inputs: [node-1]
```

### Minimal Example

```yaml
title: Hello World

nodes:
  - id: start
    type: input
    content: "Begin"
    outputs: [end]

  - id: end
    type: output
    content: "Done"
    inputs: [start]
```

### Notes

- When all nodes have coordinates `(0, 0)` — or coordinates are omitted — auto-layout is applied.
- The simplified format always creates one machine containing all nodes. To split nodes across multiple machines or factories, use the [hierarchical format](#hierarchical-format).
- The `background` key is only available in the simplified format. In the hierarchical format, the background is always `#11111b`.

---

## Hierarchical Format

The full format gives you explicit control over the four-level hierarchy. It is detected by the presence of a top-level `canvas` key.

### Structure

```yaml
canvas:
  version: "2.0"                   # Optional. Format version. Default: "2.0"
  title: "My Architecture"         # Optional. Diagram title. Default: "Untitled Canvas"

  networks:                        # List of networks (system boundaries)
    - id: network-1                # Required. Unique network identifier.
      label: "My System"           # Optional. Display name.
      description: "..."           # Optional. Documentation text.

      factories:                   # List of factories (functional domains)
        - id: factory-1
          label: "Data Layer"
          description: "..."
          style:                   # Optional. ContainerStyle override.
            border_color: "#89b4fa"
            fill_color: "#1e1e2e"
            label_color: "#89b4fa"
            alpha: 80
            corner_radius: 12
            border_width: 2

          machines:                # List of machines (pipelines)
            - id: machine-1
              label: "ETL Pipeline"
              description: "..."
              style:               # Optional. ContainerStyle override.
                border_color: "#fab387"
                fill_color: "#181825"
                label_color: "#fab387"
                alpha: 100

              nodes:               # List of nodes (operations)
                - id: extract
                  type: source
                  label: "Extract"
                  content: "Pull from database"
                  outputs: [transform]

                - id: transform
                  type: process
                  label: "Transform"
                  content: "Clean and normalize"
                  inputs: [extract]
                  outputs: [load]

            - id: machine-2
              label: "Output"
              nodes:
                - id: load
                  type: output
                  label: "Load"
                  content: "Write to warehouse"
                  inputs: [transform]
```

### Key Differences from Simplified

- Nodes are nested inside `machines`, which are inside `factories`, which are inside `networks`.
- Connections can cross machine and factory boundaries (node A in machine-1 can connect to node B in machine-2).
- Each container level (machine, factory) is rendered as a visual grouping with its own label.
- Container styling is available for machines and factories.

---

## Nodes

### Node Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | **Yes** | — | Globally unique identifier. Used for connections and lookups. |
| `type` | string | No | `"default"` | Semantic type — determines color. See [Node Types](#node-types). |
| `label` | string | No | Uses `id` | Human-readable display name. |
| `content` | string | No | `""` | Body text. Word-wrapped to fit the node width. |
| `x` | number | No | `0` | Horizontal position in canvas pixels. `0` triggers auto-layout. |
| `y` | number | No | `0` | Vertical position in canvas pixels. `0` triggers auto-layout. |
| `width` | number | No | `250` | Node width in pixels. Overridden by auto-sizing if content is present. |
| `height` | number | No | `120` | Node height in pixels. Overridden by auto-sizing if content is present. |
| `inputs` | list of strings | No | `[]` | IDs of nodes that feed into this one. |
| `outputs` | list of strings | No | `[]` | IDs of nodes this one feeds into. |
| `style` | NodeStyle object | No | — | Custom visual style override. |

### Auto-Sizing

When the renderer runs, it automatically measures each node's text content and resizes the node to fit. The `width` and `height` fields serve as starting hints but are overridden by auto-sizing. Key sizing parameters:

- **Minimum width:** 180px
- **Maximum width:** 600px
- **Minimum height:** 80px
- **Line height:** 24px per line of body text

### Node Types

Eight semantic types are available. Each has a distinct border/accent color from the Catppuccin Mocha palette:

| Type | Color | Hex Code | Semantic Meaning |
|------|-------|----------|------------------|
| `input` | Blue | `#2196F3` | User-provided data entering the system |
| `output` | Amber | `#FFC107` | Final results leaving the system |
| `process` | Cyan | `#00BCD4` | A transformation or computation step |
| `decision` | Red | `#F44336` | A branching point or conditional gate |
| `ai` | Purple | `#9C27B0` | An AI/LLM processing step |
| `source` | Orange | `#FF9800` | An external data source (API, database, file) |
| `static` | Green | `#4CAF50` | Immutable seed content or constants |
| `default` | Gray | `#999999` | Generic / unspecified |

Each node renders with:
1. A **colored top bar** in the type's accent color
2. A **bold label** (from `label` or `id`)
3. **Word-wrapped content text**
4. A **type badge** in the bottom-right corner

### Custom Node Styling

Override any aspect of a node's visual appearance with the `style` field:

```yaml
- id: special-node
  type: process
  content: "Custom styled node"
  style:
    border_color: "#f38ba8"       # Accent color for border and top bar
    fill_color: "#302030"         # Interior background
    text_color: "#f5e0dc"         # Content text color
    label_color: "#f38ba8"        # Label text color (defaults to text_color)
    corner_radius: 16             # Border radius in pixels
    border_width: 4               # Border thickness in pixels
```

All `style` fields are optional. Unset fields inherit from the node type's default style.

---

## Connections

### Declaring Connections

Connections link nodes together. Declare them using `inputs` and/or `outputs` on each node:

```yaml
# Method 1: Using outputs (forward declaration)
- id: source
  type: input
  outputs: [processor]

# Method 2: Using inputs (backward declaration)
- id: processor
  type: process
  inputs: [source]

# Method 3: Both (redundant but clear)
- id: source
  type: input
  outputs: [processor]
- id: processor
  type: process
  inputs: [source]
```

All three methods produce the same connection: `source -> processor`.

### Bidirectional Deduplication

Canvas-MCP deduplicates connections automatically. If node A lists B in its `outputs` AND node B lists A in its `inputs`, only one connection line is drawn. Declaring a connection on both ends is harmless — it just makes the YAML more readable.

### Cross-Container Connections

Connections can cross machine and factory boundaries. A node in one machine can connect to a node in a different machine or even a different factory:

```yaml
canvas:
  title: Cross-Factory Flow
  networks:
    - id: net-1
      factories:
        - id: factory-a
          machines:
            - id: machine-a
              nodes:
                - id: producer
                  type: process
                  outputs: [consumer]     # Connects to a node in factory-b

        - id: factory-b
          machines:
            - id: machine-b
              nodes:
                - id: consumer
                  type: output
                  inputs: [producer]      # Receives from factory-a
```

Cross-container connections inform the layout algorithm — the organize system resolves them upward to position related containers near each other.

### Smart Port Selection

You don't configure which side of a node connections attach to. Canvas-MCP automatically selects connection ports based on the spatial relationship between nodes:

- **Horizontal flow** (default): Connections exit from the **right edge** and enter from the **left edge**. This produces left-to-right diagrams.
- **Vertical flow** (automatic): When a target node sits significantly below or above its source (beyond a "horizon" threshold of 1.5x the source node's height), the connection switches to **bottom/top** ports. This produces vertical tree structures.
- **Reverse flow**: When a target is to the left of its source, ports flip accordingly.

This switching is **emergent from geometry** — you don't configure it. Place nodes side-by-side for horizontal flow, stack them for vertical flow.

### Connection Rendering

Connections are drawn as smooth **cubic bezier curves** with:
- **S-bend control points** that follow the connection direction
- **Color** derived from the source node's type color (lightened 25% for visibility against the dark background)
- **Arrowhead** at the target endpoint
- **4px line width** at scale 1.0

---

## The Hierarchy

Canvas-MCP uses a four-level hierarchy that models visual computation as nested containers:

```
Canvas (root)
└── Network       — system boundary (broadest scope)
    └── Factory   — functional domain
        └── Machine   — pipeline (connected chain)
            └── Node      — atomic operation
```

### Canvas (Root)

The top-level container. Holds global settings and all networks.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | string | `"2.0"` | Format version |
| `title` | string | `"Untitled Canvas"` | Diagram title (rendered centered at top) |
| `width` | integer | `1920` | Canvas width (used internally; auto-calculated from content) |
| `height` | integer | `1080` | Canvas height (used internally; auto-calculated from content) |
| `background_color` | string | `"#11111b"` | Background color (hex) |
| `networks` | list | `[]` | List of Network objects |

### Network

The broadest organizational unit. A network represents a system boundary — a service, a deployment, or an entire subsystem.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | **Yes** | — | Unique identifier |
| `label` | string | No | Uses `id` | Display name |
| `description` | string | No | — | Documentation text |
| `factories` | list | No | `[]` | List of Factory objects |

Networks are **not currently rendered as visible containers** — they are transparent groupings. Their primary role is organizational: when multiple networks exist, the layout algorithm positions them as separate systems with generous spacing between them.

### Factory

A functional domain within a network. Groups related pipelines (machines) that serve a common purpose.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | **Yes** | — | Unique identifier |
| `label` | string | No | Uses `id` | Display name |
| `description` | string | No | — | Documentation text |
| `machines` | list | No | `[]` | List of Machine objects |
| `style` | ContainerStyle | No | — | Custom visual style |

**Rendered as:** An outline container (no fill by default) with a label in the top-left corner. Border color: `#45475a`, label color: `#a6adc8`.

### Machine

A pipeline — a connected chain of operations. The most commonly used container level.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | **Yes** | — | Unique identifier |
| `label` | string | No | Uses `id` | Display name |
| `description` | string | No | — | Documentation text |
| `nodes` | list | No | `[]` | List of Node objects |
| `style` | ContainerStyle | No | — | Custom visual style |

**Rendered as:** A semi-transparent background container with a label in the top-left corner. Fill: `#181825` at 120 alpha, border: `#313244`, label: `#6c7086`.

---

## Container Styling

Machines and factories can have custom visual styles using the `style` field. All fields are optional — unset fields use defaults.

```yaml
style:
  border_color: "#89b4fa"      # Outline color (hex)
  fill_color: "#1e1e2e"        # Background fill color (hex)
  label_color: "#89b4fa"       # Label text color (hex)
  alpha: 100                   # Fill opacity: 0 (transparent) to 255 (opaque)
  corner_radius: 12            # Border radius in pixels
  border_width: 2              # Outline thickness in pixels
```

### Default Styles

| Field | Machine Default | Factory Default |
|-------|-----------------|-----------------|
| `border_color` | `#313244` | `#45475a` |
| `fill_color` | `#181825` | none (transparent) |
| `label_color` | `#6c7086` | `#a6adc8` |
| `alpha` | `120` | `0` (transparent) |
| `corner_radius` | `8` | `12` |
| `border_width` | `1` | `1` |

### Example: Colored Containers

```yaml
machines:
  - id: critical-pipeline
    label: "Critical Path"
    style:
      border_color: "#f38ba8"
      fill_color: "#302030"
      label_color: "#f38ba8"
      alpha: 80
      border_width: 2
    nodes:
      - id: step-1
        type: process
        content: "Critical processing"
```

---

## Layout & Auto-Organization

Canvas-MCP provides multiple layout strategies, from basic auto-placement to intelligent hierarchical organization.

### Auto-Layout (Basic)

When all nodes have coordinates `(0, 0)` (or coordinates are omitted) and `organize` is `false`, a basic auto-layout arranges nodes:

- **Left-to-right** within each machine (120px horizontal spacing)
- **Top-to-bottom** between machines (280px vertical spacing)
- **Extra gap** between factories (80px additional)

This is a simple grid-like layout. For intelligent flow-based layout, use the organize algorithm.

### Organize Algorithm

Enable with `organize: true` (the default for both MCP tools). The organize algorithm uses **Kahn's topological sort** to arrange nodes in a flow-based layout.

The algorithm works **bottom-up through the hierarchy**:

1. **Node level:** Nodes within each machine are organized based on their connections. Source nodes (no inputs) go on the left; downstream nodes flow to the right.

2. **Machine level:** Machines within each factory are positioned based on cross-machine connections. If machine A has nodes that connect to machine B, machine A is positioned before machine B.

3. **Factory level:** Factories within each network are positioned based on cross-factory connections, using the same flow logic.

4. **Network level:** Networks are positioned relative to each other with generous spacing.

At each level, the algorithm:
- Computes a **topological ordering** of items
- Uses **parent-center alignment** to vertically center children on their parents
- Applies **overlap prevention** to ensure minimum spacing
- Falls back to a **grid layout** for disconnected components (items with no connections)
- Handles **cycles** gracefully by assigning levels based on incoming edges

### Spacing Levels

The `spacing_level` parameter is advisory — the hierarchical system always uses the correct spacing for each level of the hierarchy. The three presets primarily affect container-level spacing:

| Level | Node H/V | Container H/V | Network H/V | Best For |
|-------|----------|--------------|-------------|----------|
| `"node"` | 90/140 | 200/240 | 260/320 | Tight, compact diagrams |
| `"container"` | 90/140 | 200/240 | 260/320 | Most diagrams (default) |
| `"network"` | 90/140 | 200/240 | 260/320 | Large multi-network systems |

Internal padding per container level:
- **Machine padding:** 55px around contained nodes
- **Factory padding:** 75px around contained machines
- **Network padding:** 100px around contained factories

### Orientation

| Value | Direction | Description |
|-------|-----------|-------------|
| `"horizontal"` | Left to right | Source nodes on the left, outputs on the right. Default. |
| `"vertical"` | Top to bottom | Source nodes at the top, outputs at the bottom. |

Orientation is applied at **all hierarchy levels** — nodes within machines, machines within factories, and factories within networks all follow the same direction.

### Connector Avoidance

After layout, a **post-processing pass** checks whether any node's bounding box overlaps with a bezier connector path that doesn't involve that node. Overlapping nodes are nudged vertically to keep connector paths unobstructed.

Key behaviors:
- Nodes are nudged **vertically** (up or down) to clear the connector
- **Machine cohesion** is preserved — when a node is nudged, its siblings in the same machine are nudged together
- A **clearance margin** of 20px is maintained between connectors and node edges
- Maximum **6 iterations** of the nudge loop (nudging one node can create new overlaps)
- Maximum **400px total displacement** per node from its original position

---

## Complete Examples

### Example 1: Simple Linear Pipeline (Simplified Format)

```yaml
title: Document Processing

nodes:
  - id: upload
    type: input
    label: "Upload"
    content: "User uploads a document"

  - id: parse
    type: process
    label: "Parse"
    content: "Extract text from PDF/DOCX"
    inputs: [upload]

  - id: analyze
    type: ai
    label: "AI Analysis"
    content: "Summarize content with LLM"
    inputs: [parse]

  - id: report
    type: output
    label: "Summary"
    content: "Generated summary document"
    inputs: [analyze]
```

### Example 2: Fan-Out / Fan-In Pattern (Simplified Format)

```yaml
title: Parallel Analysis

nodes:
  - id: ingest
    type: input
    label: "Data Ingest"
    content: "Raw data stream"

  - id: sentiment
    type: ai
    label: "Sentiment Analysis"
    content: "Detect emotional tone"
    inputs: [ingest]

  - id: entities
    type: ai
    label: "Entity Extraction"
    content: "Identify people, places, orgs"
    inputs: [ingest]

  - id: topics
    type: ai
    label: "Topic Classification"
    content: "Categorize by subject"
    inputs: [ingest]

  - id: merge
    type: process
    label: "Merge Results"
    content: "Combine all analysis outputs"
    inputs: [sentiment, entities, topics]

  - id: dashboard
    type: output
    label: "Dashboard"
    content: "Live analytics display"
    inputs: [merge]
```

### Example 3: Full Hierarchical Architecture

```yaml
canvas:
  version: "2.0"
  title: AI-Powered Content Pipeline

  networks:
    - id: content-system
      label: "Content System"

      factories:
        - id: ingestion
          label: "Content Ingestion"
          machines:
            - id: sources
              label: "Data Sources"
              nodes:
                - id: web-scraper
                  type: source
                  label: "Web Scraper"
                  content: "Crawl target websites"
                  outputs: [normalizer]

                - id: rss-feed
                  type: source
                  label: "RSS Feeds"
                  content: "Subscribe to content feeds"
                  outputs: [normalizer]

                - id: api-ingest
                  type: input
                  label: "API Upload"
                  content: "Manual content submission"
                  outputs: [normalizer]

            - id: preprocessing
              label: "Preprocessing"
              nodes:
                - id: normalizer
                  type: process
                  label: "Normalizer"
                  content: "Standardize formats, clean HTML"
                  inputs: [web-scraper, rss-feed, api-ingest]
                  outputs: [dedup]

                - id: dedup
                  type: process
                  label: "Deduplication"
                  content: "Remove duplicate content"
                  inputs: [normalizer]
                  outputs: [classifier]

        - id: analysis
          label: "AI Analysis"
          style:
            border_color: "#cba6f7"
            label_color: "#cba6f7"
          machines:
            - id: classification
              label: "Classification"
              nodes:
                - id: classifier
                  type: ai
                  label: "Topic Classifier"
                  content: "Categorize content by domain"
                  inputs: [dedup]
                  outputs: [summarizer, tagger]

                - id: tagger
                  type: ai
                  label: "Entity Tagger"
                  content: "Extract named entities"
                  inputs: [classifier]
                  outputs: [enriched-store]

            - id: summarization
              label: "Summarization"
              nodes:
                - id: summarizer
                  type: ai
                  label: "Summarizer"
                  content: "Generate executive summaries"
                  inputs: [classifier]
                  outputs: [enriched-store]

        - id: output
          label: "Output & Storage"
          machines:
            - id: storage
              label: "Storage"
              nodes:
                - id: enriched-store
                  type: output
                  label: "Content Store"
                  content: "Enriched content database"
                  inputs: [tagger, summarizer]
                  outputs: [api-serve]

                - id: api-serve
                  type: output
                  label: "API"
                  content: "Serve enriched content"
                  inputs: [enriched-store]
```

### Example 4: Decision Flow with Custom Styling

```yaml
title: Incident Response

nodes:
  - id: alert
    type: input
    label: "Alert Received"
    content: "Monitoring system triggers alert"
    style:
      border_color: "#f38ba8"

  - id: severity-check
    type: decision
    label: "Severity?"
    content: "Assess impact level"
    inputs: [alert]

  - id: critical-path
    type: process
    label: "Page On-Call"
    content: "Immediate escalation to on-call engineer"
    inputs: [severity-check]
    style:
      border_color: "#f38ba8"
      fill_color: "#302020"

  - id: normal-path
    type: process
    label: "Create Ticket"
    content: "Log in issue tracker for next business day"
    inputs: [severity-check]

  - id: investigate
    type: ai
    label: "AI Triage"
    content: "Automated root cause analysis"
    inputs: [critical-path]

  - id: resolve
    type: output
    label: "Resolution"
    content: "Incident resolved and documented"
    inputs: [investigate, normal-path]
```
