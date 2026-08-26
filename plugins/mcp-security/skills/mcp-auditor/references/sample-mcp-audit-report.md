# MCP Security Audit Report

**Date:** April 16, 2026
**Target:** Local Environment (`~/.gemini`) & Custom Built MCP Servers (`mcp-genmedia`)
**Reference Advisory:** [OX Security: MCP Supply Chain Advisory & RCE Vulnerabilities](https://www.ox.security/blog/mcp-supply-chain-advisory-rce-vulnerabilities-across-the-ai-ecosystem/)

## 1. Vulnerability Background
Based on the OX Security advisory, the primary attack vector for Remote Command Execution (RCE) in the Model Context Protocol (MCP) ecosystem occurs when AI clients (like IDEs or CLI tools) use the **STDIO transport** to execute external server binaries. Because these configurations are often modified silently by the AI itself (prompt injection), attackers can inject malicious flags like `npx -c` or `bash -c` into the configuration files.

## 2. Audit of Configured MCP Servers (Local Environment)
*Target: `~/.gemini/settings.json` and `~/.gemini/extensions/**/gemini-extension.json`*

**Findings:**
*   **`readability_docstats`** (`settings.json`): 
    *   **Command:** `~/.cargo/bin/uv`
    *   **Args:** `["run", "python", "~/dev/docstats/main.py", "--server-type", "mcp"]`
    *   **Status: Safe.** This uses an absolute path to a known safe binary (`uv`) and executes a specific python script. It does not invoke a shell interpreter (`sh`, `bash`) or use generic package runners (`npx`) that allow arbitrary command injection flags (`-c`).
*   **`google-genmedia-extension`** (`extensions/.../gemini-extension.json`):
    *   **Commands:** `mcp-veo-go`, `mcp-gemini-go`, `mcp-lyria-go`, `mcp-avtool-go`, `mcp-nanobanana-go`.
    *   **Status: Safe.** These invoke compiled Go binaries directly via the system `$PATH`. There are no arguments passed via the configuration that could be hijacked for injection.
*   **`Internal-Service`** (`extensions/.../gemini-extension.json`):
    *   **Transport:** SSE/HTTP (`https://internal-service.example.com/mcp`)
    *   **Status: Safe.** It uses HTTP transport, completely bypassing the local STDIO execution vulnerability described in the advisory.

**Conclusion for Configured Servers:** Your local `.gemini` configurations are currently clean. There is no evidence of malicious servers or vulnerable `npx -c` / `python -c` configurations. 

---

## 3. Audit of Built MCP Servers (Source Code)
*Target: `~/projects/vertex-ai-creative-studio/experiments/mcp-genmedia/mcp-genmedia-go` ([View on GitHub](https://github.com/GoogleCloudPlatform/vertex-ai-creative-studio/tree/main/experiments/mcp-genmedia))*

**Findings:**

*   **SDK Vulnerability Check:**
    *   All custom servers use the Go-based SDK `github.com/mark3labs/mcp-go` (v0.45.0).
    *   **Status: Safe.** The vulnerabilities heavily detailed in the advisory primarily affect the official JavaScript (`@modelcontextprotocol/sdk`) and Python SDKs where STDIO transport logic or sub-process spawning might improperly handle unescaped strings. 

*   **Command Execution Audit (Generative AI Models):**
    *   **Servers:** `mcp-chirp3-go`, `mcp-gemini-go`, `mcp-imagen-go`, `mcp-lyria-go`, `mcp-nanobanana-go`, `mcp-veo-go`.
    *   **Status: Safe.** These servers strictly communicate with Vertex AI / Google Cloud APIs using HTTP/gRPC SDKs (`google.golang.org/genai`). They contain no `exec.Command` or system-level shell execution. There is zero risk of STDIO-based OS command injection.

*   **Command Execution Audit (`mcp-avtool-go`):**
    *   The `mcp-avtool-go` server routinely executes external system commands using Go's `os/exec` (specifically `exec.CommandContext(ctx, "ffmpeg", args...)` and `ffprobe`).
    *   **Status: Structurally Safe, Minor Argument Injection Risk.** 
        *   Unlike Node's `child_process.exec()` or Python's `os.system()`, Go's `exec.Command` **does not invoke a shell**. This inherently protects you from classic shell injection (e.g., an attacker passing `; rm -rf /`).
        *   *However*, if an attacker uses the AI to pass a malicious file name starting with a hyphen (e.g., `-f`), `ffmpeg` will interpret it as a command-line flag rather than a file path (Argument Injection). Because your implementation relies on `common.PrepareInputFile(ctx, inputAudioURI, ...)`—which downloads/copies files to controlled local absolute or temp paths—this risk is heavily mitigated. The resolved file path passed to `ffmpeg` will be an absolute path (e.g., `/tmp/...`), preventing it from being parsed as a flag.

---

## 4. Recommendations for Ongoing Security

To ensure your MCP environments remain secure against the supply chain and RCE threats identified by OX Security:

1.  **Monitor Config Files for Tampering:** The most insidious attack vector is Prompt Injection silently modifying your `~/.gemini/settings.json` or extension configs. Consider using Git to track changes in `~/.gemini/` or setting file permissions strictly (e.g., `chmod 600`) so you are alerted if an AI agent attempts to register a new, malicious server without your explicit consent.
2.  **Avoid Shell Wrappers:** Continue your current practice of pointing the MCP configuration directly to absolute binaries (like `~/.cargo/bin/uv` or `mcp-veo-go`) rather than using shell interpreters (`bash -c`, `npx`).
3.  **Strict Path Sanitization in Go:** In your `mcp-avtool-go` implementation, ensure that any variable passed to `exec.Command` that represents a file path (like `localInputVideo` or `tempOutputFile`) always starts with a safe prefix (like `./` or `/`) and never directly reflects user input without validation.
