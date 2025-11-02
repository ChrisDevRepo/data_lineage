# MCP Auto-Approval Configuration Fix

## Problem
Claude Code was prompting for manual approval of MCP Playwright tools despite having permission configuration.

## Root Cause
**MCP permissions do NOT support wildcards (`*`)** according to official Claude Code documentation.

The configuration had:
```json
"mcp__playwright__*"  // ❌ INVALID - wildcards not supported
```

## Solution Applied

### 1. Fixed ~/.claude/settings.json
Changed from `mcp__playwright__*` to `mcp__playwright` (without wildcard):

```json
{
  "permissions": {
    "allow": [
      "Read(~/**)",
      "Edit(~/**)",
      "Write(~/**)",
      "Bash",
      "mcp__playwright",           // ✅ Approves ALL Playwright tools
      "mcp__microsoft-learn",       // ✅ Approves ALL Microsoft Learn tools
      "mcp__context7",              // ✅ Approves ALL Context7 tools
      "SlashCommand(/sub_DL_Restart)"
    ]
  },
  "sandbox": {
    "autoAllowBashIfSandboxed": true,
    "enabled": true
  },
  "alwaysThinkingEnabled": true
}
```

### 2. MCP Permission Syntax Rules

**Server-level approval (recommended for trusted servers):**
- `mcp__playwright` - Approves ALL tools from playwright server
- `mcp__github` - Approves ALL tools from github server

**Tool-specific approval:**
- `mcp__github__get_issue` - Only approves specific tool
- `mcp__playwright__browser_navigate` - Only approves specific tool

**Invalid syntax:**
- ❌ `mcp__playwright__*` - Wildcards NOT supported
- ❌ `mcp__playwright__browser_*` - Wildcards NOT supported

## Alternative: Bypass All Permissions

For development environments, you can use `bypassPermissions` mode:

```json
{
  "defaultMode": "bypassPermissions",
  "permissions": {
    "allow": ["Read(~/**)", "Edit(~/**)", "Write(~/**)", "Bash"]
  }
}
```

⚠️ **Warning:** Only use in safe, isolated environments (sandboxes, containers, VMs)

## Verification

After restarting VSCode/Claude Code, MCP Playwright tools should now execute without manual approval prompts.

## References

- [Claude Code IAM Documentation](https://docs.claude.com/en/docs/claude-code/iam)
- MCP Tool Permission Format: `mcp__[server-name]` or `mcp__[server-name]__[tool-name]`
- Permission precedence: deny > ask > allow

## Last Updated
2025-11-02
