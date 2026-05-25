# 🚀 foundational-agents

Async orchestration hub for specialized AI agent personas, powered by the [Google Antigravity SDK](https://github.com/google/antigravity) and served via [FastMCP](https://modelcontextprotocol.io/).

---

## 📐 Architecture & Multi-SDK Compatibility

This library is designed for maximum compatibility across AI assistants and development environments (including Claude Desktop, Claude Code, Cursor, VS Code, and GitHub Copilot). It achieves this via two distinct runtime modes:

```
┌────────────────────────────────────────────────────────────────────────┐
│                              RUNTIME MODES                             │
├────────────────────────────────────────┬───────────────────────────────┤
│          1. MCP Server Mode            │    2. Native Template Mode    │
│  (For Cursor, Claude, Copilot, etc.)   │   (Direct IDE System Prompts) │
│                                        │                               │
│  ┌──────────────────────────────────┐  │   ┌────────────────────────┐  │
│  │      FastMCP Server (stdio)      │  │   │  Claude Code / Copilot │  │
│  │  ┌────────────────────────────┐  │  │   │  (Runs natively using  │  │
│  │  │     ProjectCoordinator     │  │  │   │   default host LLMs)   │  │
│  │  │ ┌─────────┐ ┌────────────┐ │  │  │   └───────────┬────────────┘  │
│  │  │ │Workers  │ │Shared State│ │  │  │               │               │
│  │  │ └─────────┘ └────────────┘ │  │  │               ▼               │
│  │  └────────────────────────────┘  │  │   - .claude/agents/*.SKILL.md │
│  └──────────────────────────────────┘  │   - .github/agents/*.agent.md │
└────────────────────────────────────────┴───────────────────────────────┘
```

1. **MCP Server Mode**: Exposes a multi-agent team and individual workers as standard Model Context Protocol (MCP) tools. Host IDEs call these tools via standard JSON-RPC. Tool execution runs inside your Python environment using the `google-antigravity` SDK.
2. **Native Template Mode**: Bundled agent persona instructions can be unpacked directly into your local workspace. They run locally within Claude Code or GitHub Copilot using the host's selected default model (e.g. Claude 3.5 Sonnet or Copilot default models), bypassing the Python runtime entirely.

---

## ⚡ Quick Start

### Prerequisites

- Python **3.11** or higher.
- A `GEMINI_API_KEY` environment variable. *(Note: This is **optional** when running under hosts that support MCP Sampling like Claude Desktop or Claude Code, but required for local python usage or fallback mode).* Get a key from [Google AI Studio](https://aistudio.google.com/app/api-keys).

### Installation

You can install the package directly from GitHub via `pip`:

```bash
# Create a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install the package from GitHub
pip install git+https://github.com/catlikeflyer/foundational-agents.git
```

> [!NOTE]
> Installing this package registers the global CLI tool `fd-agents` and exposes the MCP server modules on your python path.

---

## ⚙️ Model Configuration & Selection

To ensure the library remains flexible, it uses native host LLMs when possible and provides fallbacks for programmatic usage:

* **MCP Client Native Sampling (Standard Integration)**: When running as an MCP server, the server dynamically queries the client/host via **MCP Sampling** (`create_message`). This means if you run the server under Claude Desktop, it will natively use Claude (e.g. `claude-sonnet-4.6` or whichever model you have active in your Claude Desktop/Claude Code session) without requiring any local Gemini setup or API keys!
* **Graceful Fallback**: If the host client does not support or permit sampling, the server automatically falls back to local execution using the `google-antigravity` (Gemini) SDK (which requires the `GEMINI_API_KEY` to be set).
* **Environment Variable Override**: You can override the fallback model or specify a Gemini model for execution by setting the `FOUNDATIONAL_AGENTS_MODEL` environment variable:
  ```bash
  export FOUNDATIONAL_AGENTS_MODEL="gemini-2.5-flash"
  ```
* **Programmatic Specification**: When using the library in raw Python code, pass the model identifier directly during class construction:
  ```python
  coordinator = ProjectCoordinator(model="gemini-1.5-pro")
  ```

---

## 🛠️ Usage Guide

### 1. As an MCP Server

Once installed, the server can be run with:
```bash
python -m foundational_agents.mcp.server
```

#### Claude Desktop Configuration
Add the server definition to your `claude_desktop_config.json` (typically located at `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS).

Since the server automatically utilizes native Claude sampling, the `GEMINI_API_KEY` is **not required** unless you want to configure a fallback for when sampling is disabled:

```json
{
  "mcpServers": {
    "foundational-agents": {
      "command": "python",
      "args": ["-m", "foundational_agents.mcp.server"]
    }
  }
}
```

*(If you want to configure fallback support, pass `"env": { "GEMINI_API_KEY": "your-key", "FOUNDATIONAL_AGENTS_MODEL": "gemini-2.5-flash" }` inside the server configuration.)*

#### Cursor Integration
1. Go to **Settings** > **Features** > **MCP**.
2. Click **+ Add New MCP Server**.
3. Set the details:
   - **Name**: `foundational-agents`
   - **Type**: `command`
   - **Command**: `python -m foundational_agents.mcp.server` (ensure your environment path has Python available).
   *(Note: Cursor supports MCP Sampling, so no API keys are required for standard tool use!)*

---

### 2. Native IDE Agent Templates (CLI)

Use the built-in CLI command `fd-agents` to unpack optimized persona profiles directly into your projects. This allows tools like Claude Code and Copilot to use the exact same agent guidelines natively.

```bash
# Install templates in your current project directory
fd-agents install

# Install templates globally to your $HOME folder
fd-agents install --global

# Preview changes before writing files
fd-agents install --dry-run
```

This commands copies:
* 📝 **Claude Code Skills** (`.SKILL.md`) $\rightarrow$ `.claude/agents/`
* 🤖 **Copilot Agent Prompts** (`.agent.md`) $\rightarrow$ `.github/agents/`

---

### 3. Programmatic Usage in Python

You can integrate the coordination matrix directly into your custom Python tools and automated pipelines:

```python
import asyncio
from foundational_agents.core.coordinator import ProjectCoordinator

async def main():
    # Instantiate the coordinator. It will automatically delegate
    # to individual specialists based on the complexity of your request.
    coordinator = ProjectCoordinator()
    
    request = (
        "Design a high-throughput notifications service, create a timeline "
        "for its implementation, and propose a launch campaign outline."
    )
    
    print("🚀 Running Project Coordinator...")
    response = await coordinator.run(request)
    print("\n📝 Result:")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🧪 Testing the Server Locally

You can interactively debug the server and test tools using the official Model Context Protocol inspector:

```bash
# Export your API key
export GEMINI_API_KEY="your-gemini-api-key"

# Launch the inspector tool
npx -y @modelcontextprotocol/inspector python -m foundational_agents.mcp.server
```

Open the URL printed in the terminal (usually `http://localhost:5173`) to view and execute all the tools (`coordinate_project`, `create_presentation`, `manage_project`, `design_system`, `analyze_market`, and `document_code`).

---

## 👥 Agent Personas

The system includes the following five core personas, each with comprehensive rulesets and structured markdown formatting outputs:

| Persona | Purpose / Use Case | Output Artifacts |
| :--- | :--- | :--- |
| **Presentation Maker** | Designs high-impact slide structures and pitch narratives. | Numbered slide outlines with layout rules, slide tags, and speaker notes. |
| **Project Manager** | Decomposes initiatives, coordinates resources, and manages risk. | Task tables, milestones, timeline graphs, RACI matrices, risk registers. |
| **System Design Engineer** | Architects distributed backends, models schemas, and maps APIs. | High-level container structures, API endpoints, schema definitions, trade-offs. |
| **Marketing Analyst** | Evaluates competitors, profiles segments, and sizes market scope. | TAM/SAM/SOM sizing matrices, competitor profiles, SWOT analysis, GTM advice. |
| **Code Documenter** | Writes structured code documentation, docstrings, and API manuals according to custom tones. | Inline docstrings (Google/NumPy/JSDoc), markdown API guides, technical summaries. |

---

## 📁 Repository Structure

```
foundational-agents/
├── pyproject.toml         # Hatch project configuration
├── README.md              # Project documentation
└── src/
    └── foundational_agents/
        ├── __init__.py    # Main library entry exports
        ├── cli.py         # Click command line tool (fd-agents)
        ├── core/          # Orchestration layer logic
        │   ├── state.py   # SharedStateMatrix for worker collaboration
        │   ├── workers.py # Worker agent personas
        │   └── coordinator.py # Main orchestration loop
        ├── mcp/
        │   └── server.py  # FastMCP stdio server setup
        └── templates/     # Persona templates for IDE integration
            ├── claude/    # Custom Claude skills
            └── copilot/   # Custom GitHub Copilot instructions
```

---

## 📄 License

This project is licensed under the Apache-2.0 License.
