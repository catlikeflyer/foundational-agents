# my-foundational-agents

Async orchestration hub for specialized AI agent personas, powered by the [Google Antigravity SDK](https://github.com/google/antigravity) and served via [FastMCP](https://modelcontextprotocol.io/).

## Architecture

```
┌────────────────────────────────────────────────┐
│              FastMCP Server (stdio)             │
│  ┌──────────────────────────────────────────┐  │
│  │          ProjectCoordinator              │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐       │  │
│  │  │Present.│ │Project │ │System  │ ...   │  │
│  │  │Maker   │ │Manager │ │Design  │       │  │
│  │  └────────┘ └────────┘ └────────┘       │  │
│  │         SharedStateMatrix                │  │
│  └──────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
         ▲                          │
    MCP request              MCP response
         │                          ▼
   ┌─────────────────────────────────────┐
   │  Host (Claude Desktop / Claude Code) │
   └─────────────────────────────────────┘
```

## Installation

You can install the package directly from version control using `pip`.

1. **Create a virtual environment** (Optional but recommended):
```bash
python3 -m venv venv
source venv/bin/activate
```

2. **Install the package and its dependencies:**
```bash
pip install git+https://github.com/yourusername/foundational-agents.git
```

*(Note: If you plan to modify the code, you can clone the repository and run `pip install -e .` instead.)*

### Prerequisites

- Python 3.11+
- A `GEMINI_API_KEY` environment variable ([get one here](https://aistudio.google.com/app/api-keys))

## Usage

### As an MCP Server (Claude Desktop)

To run the agents inside Claude Desktop, add the following to your `claude_desktop_config.json` (or equivalent host configuration):

```json
{
  "mcpServers": {
    "foundational-agents": {
      "command": "python",
      "args": ["-m", "my_foundational_agents.mcp.server"],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

By default, the agents are powered by the default model of the underlying SDK. You can override this using the `FOUNDATIONAL_AGENTS_MODEL` environment variable.

### Testing the Server Locally

You can test the MCP server interactively without Claude Desktop by using the official MCP inspector. This is the best way to verify that your API key is working and the agents are responding.

```bash
# Ensure your API key is exported
export GEMINI_API_KEY="your-api-key-here"

# Launch the interactive web inspector
npx -y @modelcontextprotocol/inspector python -m my_foundational_agents.mcp.server
```

This command will output a local URL (usually `http://localhost:5173`). Open it in your browser to interact with the foundational agent tools directly!

### Programmatic Usage

```python
import asyncio
from my_foundational_agents.core.coordinator import ProjectCoordinator

async def main():
    # You can explicitly specify the model when instantiating the coordinator,
    # or leave it empty to use the SDK's default model.
    coordinator = ProjectCoordinator()
    result = await coordinator.run(
        "Design a microservices architecture for an e-commerce platform"
    )
    print(result)

asyncio.run(main())
```

### CLI — Template Installer

Unpack bundled agent templates to your project:

```bash
# Install to current working directory
fd-agents install

# Install to $HOME (global)
fd-agents install --global
```

This copies:
- `claude/*.SKILL.md` → `.claude/agents/`
- `copilot/*.agent.md` → `.github/agents/`

## Agent Personas

| Persona | Description |
|---|---|
| **Presentation Maker** | Builds slide decks, outlines, and visual presentation structures |
| **Project Manager** | Plans timelines, tracks milestones, allocates resources |
| **System Design Engineer** | Architects systems, designs APIs, models data flows |
| **Marketing Analyst** | Analyzes markets, competitive landscapes, and positioning strategies |

## Project Structure

```
src/my_foundational_agents/
├── __init__.py           # Package exports
├── cli.py                # Click CLI (fd-agents)
├── core/
│   ├── state.py          # SharedStateMatrix
│   ├── workers.py        # 4 specialized worker classes
│   └── coordinator.py    # ProjectCoordinator orchestrator
├── mcp/
│   └── server.py         # FastMCP stdio server
└── templates/
    ├── claude/            # SKILL.md templates
    └── copilot/           # .agent.md templates
```

## License

Apache 2.0
