"""Test the hierarchical organize system with a Rhode architecture diagram."""

import sys
sys.path.insert(0, "src")

from canvas_mcp.models import (
    Canvas, CanvasNetwork, CanvasFactory, CanvasMachine, CanvasNode, ContainerStyle,
)
from canvas_mcp.renderer import CanvasRenderer


def build_rhode_canvas() -> Canvas:
    """Build a multi-machine, multi-factory Rhode architecture diagram."""

    # --- Factory 1: Input Layer ---
    telegram_node = CanvasNode(
        id="telegram", type="input", label="Telegram Bot",
        content="Receives messages, photos, files from Micah",
    )
    bus_monitor = CanvasNode(
        id="bus-monitor", type="process", label="Bus Monitor",
        content="Polls oracle bus for requests, routes by ordinal level",
    )
    input_machine = CanvasMachine(
        id="input-pipeline", label="Input Pipeline",
        nodes=[telegram_node, bus_monitor],
    )
    input_factory = CanvasFactory(
        id="input-layer", label="Input Layer",
        machines=[input_machine],
        style=ContainerStyle(border_color="#2196F3"),
    )

    # --- Factory 2: Core Processing ---
    task_queue = CanvasNode(
        id="task-queue", type="process", label="Task Queue",
        content="Async task queue with priority handling",
        inputs=["telegram", "bus-monitor"],
    )
    agent = CanvasNode(
        id="agent", type="ai", label="Claude Agent",
        content="Opus 4.6 with MCP tools, memory injection, multi-turn",
        inputs=["task-queue"],
    )
    processing_machine = CanvasMachine(
        id="processing", label="Core Processing",
        nodes=[task_queue, agent],
    )

    memory = CanvasNode(
        id="memory", type="static", label="Memory Store",
        content="Persistent lessons, preferences, patterns in memory.md",
        outputs=["agent"],
    )
    memory_machine = CanvasMachine(
        id="memory-system", label="Memory System",
        nodes=[memory],
    )

    core_factory = CanvasFactory(
        id="core-layer", label="Core Engine",
        machines=[processing_machine, memory_machine],
        style=ContainerStyle(border_color="#9C27B0"),
    )

    # --- Factory 3: Tool Layer ---
    canvas_mcp = CanvasNode(
        id="canvas-mcp", type="source", label="Canvas MCP",
        content="Thoughtorio-style diagram renderer",
        inputs=["agent"],
    )
    ordinal_mcp = CanvasNode(
        id="ordinal-mcp", type="source", label="Ordinal MCP",
        content="Oracle bus for human-in-the-loop decisions",
        inputs=["agent"],
    )
    tool_machine = CanvasMachine(
        id="mcp-tools", label="MCP Tools",
        nodes=[canvas_mcp, ordinal_mcp],
    )

    git_node = CanvasNode(
        id="git", type="source", label="Git / GitHub",
        content="Code operations, PR creation, branch management",
        inputs=["agent"],
    )
    shell_node = CanvasNode(
        id="shell", type="source", label="Shell Access",
        content="Full system access, uv, podman, systemd",
        inputs=["agent"],
    )
    system_machine = CanvasMachine(
        id="system-tools", label="System Tools",
        nodes=[git_node, shell_node],
    )

    tools_factory = CanvasFactory(
        id="tools-layer", label="Tool Layer",
        machines=[tool_machine, system_machine],
        style=ContainerStyle(border_color="#FF9800"),
    )

    # --- Factory 4: Output Layer ---
    send_photo = CanvasNode(
        id="send-photo", type="output", label="Photo/File Send",
        content="Send diagrams, files to Telegram",
        inputs=["canvas-mcp", "agent"],
    )
    send_text = CanvasNode(
        id="send-text", type="output", label="Text Response",
        content="Send formatted messages to Telegram",
        inputs=["agent"],
    )
    output_machine = CanvasMachine(
        id="output-pipeline", label="Output Pipeline",
        nodes=[send_photo, send_text],
    )

    oracle_response = CanvasNode(
        id="oracle-response", type="output", label="Oracle Response",
        content="Write responses to ordinal bus",
        inputs=["ordinal-mcp"],
    )
    oracle_machine = CanvasMachine(
        id="oracle-output", label="Oracle Output",
        nodes=[oracle_response],
    )

    output_factory = CanvasFactory(
        id="output-layer", label="Output Layer",
        machines=[output_machine, oracle_machine],
        style=ContainerStyle(border_color="#FFC107"),
    )

    # --- Assemble ---
    network = CanvasNetwork(
        id="rhode-system", label="Rhode System",
        factories=[input_factory, core_factory, tools_factory, output_factory],
    )

    canvas = Canvas(
        title="Rhode System Architecture",
        networks=[network],
    )
    canvas.model_post_init(None)
    return canvas


def main():
    canvas = build_rhode_canvas()

    print(f"Nodes: {len(canvas.all_nodes())}")
    print(f"Connections: {len(canvas.all_connections())}")
    print(f"Factories: {sum(len(n.factories) for n in canvas.networks)}")
    print(f"Machines: {sum(len(f.machines) for n in canvas.networks for f in n.factories)}")

    renderer = CanvasRenderer(scale=2.0)
    output_path = "/home/bobbyhiddn/.rhode/canvas/rhode-architecture-hierarchical.png"

    try:
        renderer.render(
            canvas,
            output_path=output_path,
            organize=True,
        )
        print(f"\nRendered to: {output_path}")

        # Print node positions to verify layout
        print("\nNode positions after organize:")
        for node in canvas.all_nodes():
            print(f"  {node.get_label():25s} x={node.x:6.0f}  y={node.y:6.0f}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nFailed: {e}")


if __name__ == "__main__":
    main()
