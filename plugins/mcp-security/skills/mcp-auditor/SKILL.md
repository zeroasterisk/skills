---
name: mcp-auditor
description: Audits local Model Context Protocol (MCP) server configurations and custom-built MCP servers for Remote Command Execution (RCE) and supply chain vulnerabilities, specifically focusing on STDIO transport injection and malicious prompt injection. Use when auditing MCP server configs, reviewing MCP server source code, or conducting a security review of AI IDE extensions.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# MCP Security Auditor

## Description
Audits local Model Context Protocol (MCP) server configurations and custom-built MCP servers for Remote Command Execution (RCE) and supply chain vulnerabilities, specifically focusing on STDIO transport injection and malicious prompt injection.

## Background
A systemic command injection vulnerability exists in the MCP SDK that enables RCE across AI platforms. Attackers exploit the STDIO transport layer by injecting malicious OS commands into MCP server configurations (e.g., using `npx -c`, `bash -c`). Prompt injection in AI IDEs can also silently modify local MCP JSON files to register malicious servers. 

Reference: [OX Security: MCP Supply Chain Advisory & RCE Vulnerabilities](https://www.ox.security/blog/mcp-supply-chain-advisory-rce-vulnerabilities-across-the-ai-ecosystem/)

## Instructions
When asked to perform a security audit of MCP servers, follow these steps:

### 1. Audit Configured MCP Servers (Local Environment)
Locate and read MCP configuration files for various AI environments. Common locations include:
- **Gemini CLI:** `~/.gemini/settings.json`, `~/.gemini/extensions/**/gemini-extension.json`
- **Claude Desktop:** `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)
- **Cursor:** `.cursor/mcp.json` or global Cursor settings.

**Analysis Rules:**
- Analyze the `command` and `args` fields for every configured server.
- **Hunt for Red Flags:** Flag any configurations using dangerous flags like `-c` (in `bash`, `sh`, `npx`, `python`), shell metacharacters (`|`, `&&`, `;`), or executing a shell interpreter directly instead of a specific binary.

### 2. Audit Built MCP Servers (Source Code)
If the user provides a source code directory for custom MCP servers, inspect its codebase:
- **Inventory All Servers:** Explicitly list out all the MCP servers or tools found in the directory. Ensure none are skipped in the final report.
- **Dependency Check:** Inspect dependencies (`package.json`, `pyproject.toml`, `go.mod`) for vulnerable MCP SDK versions (e.g., `@modelcontextprotocol/sdk`).
- **Code Execution Scan:** Scan the source code for uses of shell execution functions (e.g., `child_process.exec` or `child_process.spawn(..., { shell: true })` in Node.js, `os.system` or `subprocess.Popen(..., shell=True)` in Python, or `exec.Command` in Go).
- **Assess Network vs Local Execution:** If a server only uses HTTP/gRPC SDKs to communicate with remote backends and has zero local OS-level execution, explicitly declare it as structurally safe from STDIO RCE.
- **Hidden STDIO Configurations (MITM):** Check if the server's API accepts STDIO transport configurations (e.g., in its JSON schema or request parsing) even if the frontend UI only advertises HTTP/SSE. Attackers can use man-in-the-middle (MITM) techniques to substitute the transport type and achieve RCE if the backend still processes STDIO payloads.
- **Argument Injection Validation:** For servers that *do* execute external binaries (even safely without a shell interpreter, like Go's `exec.Command`), verify if arguments passed from the client via MCP tool calls are interpolated into the command without strict sanitization. Ensure that malicious inputs starting with a hyphen (e.g., `-f`) cannot be passed directly into the binary's arguments to hijack its behavior.

### 3. Generate a Security Report
Produce a structured report detailing the findings for both configured servers and built servers.
- **State clearly** whether each server (configured or custom) is "Safe" or "Vulnerable/At Risk".
- **Detail** the exact command or code snippet that triggered a flag.
- **Provide actionable recommendations** for securing the environment (e.g., tracking config file changes, avoiding shell wrappers, strict path sanitization).

## Example
**User:** "Audit my MCP configurations in ~/.gemini and the custom server in ./my-mcp-server."

**Assistant:** 
[Reads config files and source code, catalogs all servers, analyzes for injection vectors based on the OX Security report, checks for Argument Injection, and outputs a structured security report]
