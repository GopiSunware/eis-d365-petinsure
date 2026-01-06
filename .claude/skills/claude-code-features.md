# Claude Code Features Guide

Master guide for understanding and using Claude Code's extensibility features. Use this when deciding how to customize Claude for your project.

## Feature Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE EXTENSIBILITY                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │    SKILLS    │  │  SUB-AGENTS  │  │    HOOKS     │                  │
│  │  Auto-apply  │  │  Delegated   │  │  Event-based │                  │
│  │  knowledge   │  │  tasks       │  │  automation  │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   PLUGINS    │  │     MCP      │  │   HEADLESS   │                  │
│  │  Distribute  │  │  External    │  │  CI/CD &     │                  │
│  │  extensions  │  │  tools/APIs  │  │  automation  │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                          │
│  ┌──────────────┐                                                       │
│  │OUTPUT STYLES │                                                       │
│  │  Customize   │                                                       │
│  │  behavior    │                                                       │
│  └──────────────┘                                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Quick Decision Guide

| I want to... | Use |
|-------------|-----|
| Teach Claude domain knowledge | **Skills** |
| Delegate tasks to specialized AI | **Sub-agents** |
| Auto-run scripts on events | **Hooks** |
| Connect to external APIs/DBs | **MCP** |
| Share tools with team | **Plugins** |
| Use Claude in CI/CD | **Headless Mode** |
| Change Claude's tone/behavior | **Output Styles** |
| Add project context | **CLAUDE.md** |

---

## 1. Skills - Automatic Knowledge Application

**What**: Markdown files that teach Claude specialized knowledge, automatically applied when requests match.

**When to use**:
- Domain-specific procedures (code review, testing, deployment)
- Project standards and conventions
- Recurring task guidance
- API/library usage patterns

**Location**:
```
~/.claude/skills/my-skill/SKILL.md    # Personal (all projects)
.claude/skills/my-skill/SKILL.md      # Project (shared with team)
```

**Basic structure**:
```markdown
---
name: code-review
description: Review code for quality and security. Use when reviewing PRs or code changes.
allowed-tools: Read, Grep, Glob
---

# Code Review Standards

When reviewing code:

1. **Check for security issues**
   - SQL injection
   - XSS vulnerabilities
   - Hardcoded secrets

2. **Verify best practices**
   - Error handling
   - Input validation
   - Logging

## Examples
[Include concrete examples]
```

**Key points**:
- `description` is critical - Claude matches requests semantically
- Use subdirectories for multi-file skills
- `allowed-tools` restricts what tools the skill can use
- Skills auto-activate when context matches

**Commands**:
```bash
/skills              # List available skills
/skill:my-skill      # Manually invoke a skill
```

---

## 2. Sub-agents - Delegated Specialized Tasks

**What**: Pre-configured AI personalities with separate context windows, custom prompts, and specific tool permissions.

**When to use**:
- Different tool access needed (read-only reviewer vs full editor)
- Context isolation (large codebase exploration)
- Specialized expertise (security auditor, performance analyst)
- Parallel task execution

**Location**:
```
~/.claude/agents/my-agent.md    # Personal
.claude/agents/my-agent.md      # Project (shared)
```

**Basic structure**:
```markdown
---
name: security-reviewer
description: Security expert for code audits. Use after implementing auth or sensitive features.
tools: Read, Grep, Glob, Bash
model: sonnet
skills: security-checklist
---

You are a senior security engineer specializing in application security.

## Your Focus
- Authentication/authorization flaws
- Injection vulnerabilities
- Data exposure risks
- Cryptographic weaknesses

## Review Process
1. Scan for hardcoded secrets
2. Check input validation
3. Review authentication logic
4. Verify authorization checks
```

**Configuration fields**:
| Field | Purpose |
|-------|---------|
| `name` | Unique identifier (lowercase, hyphens) |
| `description` | When to use (Claude matches semantically) |
| `tools` | Comma-separated tool list |
| `model` | sonnet/opus/haiku/inherit |
| `skills` | Auto-load these skills |
| `permissionMode` | default/acceptEdits/bypassPermissions |

**Built-in agents**:
- **Explore** - Fast read-only codebase search (uses Haiku)
- **Plan** - Research during planning mode
- **General-purpose** - Complex multi-step tasks

**Commands**:
```bash
/agents              # Manage agents
# Or just describe task - Claude auto-delegates
```

---

## 3. Hooks - Event-Based Automation

**What**: Shell commands that execute automatically at specific Claude Code events.

**When to use**:
- Auto-format code after edits
- Validate changes before applying
- Log commands for audit
- Protect sensitive files
- Custom notifications
- Initialize environment on session start

**Location**:
```json
// ~/.claude/settings.json (user) or .claude/settings.json (project)
{
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Stop": [...]
  }
}
```

**Hook events**:
| Event | When | Common Use |
|-------|------|------------|
| `PreToolUse` | Before tool call | Block dangerous actions |
| `PostToolUse` | After tool completes | Auto-format, validate |
| `Stop` | Claude finishes | Summary, cleanup |
| `SessionStart` | Session begins | Load environment |
| `Notification` | Claude notifies | Desktop alerts |

**Basic structure**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write $(jq -r '.tool_input.file_path')",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**Hook types**:
- `command` - Run shell command (input via stdin as JSON)
- `prompt` - LLM evaluates condition

**Exit codes**:
- `0` = success (allow)
- `2` = block action
- Other = error

**Example hooks**:

Auto-format TypeScript:
```json
{
  "matcher": "Edit|Write",
  "hooks": [{
    "type": "command",
    "command": "jq -r '.tool_input.file_path' | xargs -I {} sh -c '[[ {} == *.ts ]] && prettier --write {}'"
  }]
}
```

Protect sensitive files:
```json
{
  "matcher": "Edit|Write",
  "hooks": [{
    "type": "command",
    "command": "python3 -c \"import json,sys; d=json.load(sys.stdin); sys.exit(2 if '.env' in d.get('tool_input',{}).get('file_path','') else 0)\""
  }]
}
```

**Commands**:
```bash
/hooks               # Interactive hook management
```

---

## 4. MCP - Model Context Protocol

**What**: Connect Claude to external tools, databases, and APIs via a standard protocol.

**When to use**:
- Query databases (PostgreSQL, MongoDB)
- Access issue trackers (GitHub, Jira, Linear)
- Monitor errors (Sentry, DataDog)
- Connect to internal tools
- Team-wide integrations

**Adding servers**:
```bash
# HTTP server (recommended)
claude mcp add --transport http github https://api.githubcopilot.com/mcp/

# With authentication
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp \
  --header "Authorization: Bearer $TOKEN"

# Stdio server (local process)
claude mcp add --transport stdio db \
  --env DB_URL="postgresql://..." \
  -- npx -y @bytebase/dbhub
```

**Scopes**:
| Scope | Flag | Stored | Shared |
|-------|------|--------|--------|
| Local | (default) | ~/.claude.json | No |
| Project | `--scope project` | .mcp.json | Yes (team) |
| User | `--scope user` | ~/.claude.json | No |

**Project configuration** (`.mcp.json`):
```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "database": {
      "type": "stdio",
      "command": "python",
      "args": ["./scripts/db-mcp.py"],
      "env": {
        "DATABASE_URL": "${DB_URL}"
      }
    }
  }
}
```

**Commands**:
```bash
claude mcp list      # List servers
claude mcp get NAME  # Server details
claude mcp remove NAME
/mcp                 # In-session management
```

**Usage**:
```
# Natural language
> What errors happened in Sentry today?
> Show me open GitHub PRs
> Query the users table for inactive accounts

# Resource references
> Analyze @github:issue://123
```

---

## 5. Plugins - Distributable Extensions

**What**: Packaged bundles of commands, agents, skills, hooks, and MCP servers for distribution.

**When to use**:
- Share tools with team
- Distribute via marketplace
- Version and release extensions
- Cross-project reuse

**Structure**:
```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # REQUIRED manifest
├── commands/                 # Slash commands
│   └── review.md
├── agents/                   # Sub-agents
│   └── reviewer.md
├── skills/                   # Skills
│   └── code-review/
│       └── SKILL.md
├── hooks/
│   └── hooks.json
└── .mcp.json                # MCP servers
```

**Manifest** (`.claude-plugin/plugin.json`):
```json
{
  "name": "code-quality",
  "description": "Code quality tools for teams",
  "version": "1.0.0",
  "author": {"name": "Your Name"},
  "repository": "https://github.com/user/plugin"
}
```

**Command naming**:
- Standalone: `/review`
- Plugin: `/code-quality:review`

**Commands**:
```bash
/plugin list              # List installed
/plugin install NAME      # Install
/plugin uninstall NAME    # Remove

# Test locally
claude --plugin-dir ./my-plugin
```

---

## 6. Headless Mode - CI/CD & Automation

**What**: Non-interactive Claude usage via CLI for scripts and pipelines.

**When to use**:
- CI/CD pipelines
- Automated scripts
- Batch processing
- Integration with other tools

**Basic usage**:
```bash
# Simple prompt
claude -p "Fix the failing tests"

# With tool permissions
claude -p "Run tests and fix failures" \
  --allowedTools "Bash,Read,Edit"

# Continue conversation
claude -p "Now optimize performance" --continue

# Resume specific session
claude -p "Continue work" --resume $SESSION_ID
```

**Output formats**:
```bash
# Plain text (default)
claude -p "Summarize the project"

# JSON output
claude -p "Analyze code" --output-format json

# Structured output (schema)
claude -p "List functions in auth.py" \
  --output-format json \
  --json-schema '{"type":"object","properties":{"functions":{"type":"array","items":{"type":"string"}}}}'
```

**CI/CD example**:
```yaml
# GitHub Actions
- name: Code Review
  run: |
    gh pr diff $PR_NUMBER | claude -p \
      --append-system-prompt "Review for security" \
      --output-format json | jq '.result'
```

---

## 7. Output Styles - Customize Behavior

**What**: Replace Claude's default system prompt to change behavior/tone.

**When to use**:
- Non-engineering tasks (legal, support, writing)
- Different team needs
- Specialized workflows

**Built-in styles**:
- **Default** - Software engineering optimized
- **Explanatory** - Adds educational insights
- **Learning** - Collaborative with `TODO(human)` markers

**Custom style**:
```markdown
# ~/.claude/output-styles/support-agent.md
---
name: Support Agent
description: Customer support specialist
keep-coding-instructions: false
---

# Customer Support Agent

You are a friendly support specialist.

## Approach
1. Empathize with the issue
2. Ask clarifying questions
3. Provide clear solutions
4. Confirm resolution
```

**Commands**:
```bash
/output-style           # Change style
/output-style NAME      # Select specific
```

---

## CLAUDE.md - Project Context

**What**: Project-wide instructions loaded into every conversation.

**When to use**:
- Project standards everyone should follow
- Architecture context
- Coding conventions
- Important caveats

**Location**: Project root as `CLAUDE.md`

**Example**:
```markdown
# Project: PetInsure360

## Architecture
- Frontend: React + Tailwind
- Backend: FastAPI
- Database: PostgreSQL

## Conventions
- Use TypeScript for all new code
- Follow existing patterns in /src/components
- Run `npm run lint` before committing

## Important
- Never modify files in /config/production
- All API changes need migration scripts
```

---

## Feature Comparison Matrix

| Feature | Auto-applies | Separate Context | Distributable | Event-driven |
|---------|--------------|------------------|---------------|--------------|
| Skills | Yes | No | Via plugins | No |
| Sub-agents | Sometimes | Yes | Via plugins | No |
| Hooks | N/A | N/A | Via plugins | Yes |
| MCP | N/A | No | Via .mcp.json | No |
| Plugins | N/A | N/A | Yes | N/A |
| Output Styles | Yes | No | Manual | No |
| CLAUDE.md | Yes | No | Via repo | No |

---

## Recommended Setups

### Personal Developer
```
~/.claude/
├── skills/
│   └── my-standards/SKILL.md
├── agents/
│   └── code-reviewer.md
└── settings.json              # Hooks for auto-format
```

### Team Project
```
project/
├── .claude/
│   ├── skills/
│   │   └── team-standards/SKILL.md
│   ├── agents/
│   │   └── security-reviewer.md
│   └── settings.json          # Shared hooks
├── .mcp.json                  # Shared MCP servers
└── CLAUDE.md                  # Project context
```

### Enterprise
```
/etc/claude-code/
├── managed-settings.json      # Enforced settings
└── managed-mcp.json          # Required MCP servers

# Plus team plugins via marketplace
```

### CI/CD Pipeline
```bash
claude -p "Run tests and fix failures" \
  --allowedTools "Bash,Read,Edit" \
  --output-format json
```

---

## Feature Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│                     HOW FEATURES WORK TOGETHER                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Request                                                   │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────┐                                               │
│   │ CLAUDE.md   │ ──── Always loaded as context                 │
│   └─────────────┘                                               │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────┐                                               │
│   │Output Style │ ──── Shapes Claude's behavior                 │
│   └─────────────┘                                               │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────┐     ┌─────────────┐                          │
│   │   Skills    │ ←── │ Sub-agents  │ ← Can load skills        │
│   │(auto-match) │     │(delegation) │                          │
│   └─────────────┘     └─────────────┘                          │
│        │                    │                                    │
│        └────────┬───────────┘                                    │
│                 ▼                                                 │
│   ┌─────────────┐     ┌─────────────┐                          │
│   │    Tools    │ ←── │    MCP      │ ← External tools         │
│   │   (built-in)│     │  (servers)  │                          │
│   └─────────────┘     └─────────────┘                          │
│        │                    │                                    │
│        └────────┬───────────┘                                    │
│                 ▼                                                 │
│   ┌─────────────┐                                               │
│   │    Hooks    │ ──── Pre/Post tool automation                 │
│   └─────────────┘                                               │
│        │                                                         │
│        ▼                                                         │
│   Response to User                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference Commands

```bash
# Skills
/skills                    # List skills
/skill:name               # Invoke skill

# Agents
/agents                   # Manage agents

# Hooks
/hooks                    # Manage hooks

# MCP
/mcp                      # In-session management
claude mcp list           # List servers
claude mcp add ...        # Add server

# Plugins
/plugin list              # List plugins
/plugin install NAME      # Install

# Output Style
/output-style             # Change style

# Headless
claude -p "prompt"        # Non-interactive
claude -p "..." --continue # Continue session
```
