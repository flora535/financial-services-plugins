# Financial Services Plugins

This repository is a focused plugin suite for personal investors. Each subdirectory is a standalone plugin.

## Repository Structure

```
├── .claude-plugin/      # Marketplace manifest
├── financial-analysis/  # Core analysis workflows
└── wealth-management/   # Planning and advisory workflows
```

## Plugin Structure

Each plugin follows this layout:
```
plugin-name/
├── .claude-plugin/plugin.json   # Plugin manifest (name, description, version)
├── .mcp.json                    # MCP connector definitions (optional)
├── commands/                    # Slash commands (.md files)
├── skills/                      # Knowledge files for specific tasks
├── hooks/                       # Event-driven automation
└── .claude/                     # User settings (*.local.md)
```

## Key Files

- `marketplace.json`: Marketplace manifest - registers all plugins with source paths
- `plugin.json`: Plugin metadata - name, description, version, and component discovery settings
- `.mcp.json`: MCP server configuration (includes local `sec-edgar` wiring)
- `commands/*.md`: Slash commands invoked as `/plugin:command-name`
- `skills/*/SKILL.md`: Detailed knowledge and workflows for specific tasks
- `*.local.md`: User-specific configuration (gitignored)
- `financial-analysis/skills/comps-analysis/SKILL.md`: Explicit fallback hierarchy for comps workflow
- `financial-analysis/skills/dcf-model/SKILL.md`: Explicit fallback hierarchy for DCF workflow
- `financial-analysis/skills/3-statements/SKILL.md`: Template-centric workflow with conditional SEC extraction path

## Development Workflow

1. Edit markdown files directly - changes take effect immediately
2. Test commands with `/plugin:command-name` syntax
3. Skills are invoked automatically when their trigger conditions match
