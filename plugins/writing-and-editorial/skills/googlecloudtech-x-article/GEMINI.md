# GoogleCloudTech X Article: Alan Blount Edition

Produce high-performing, viral X Articles for the **@GoogleCloudTech** brand account from trends, architectures, product launches, or repos, in Alan Blount's authentic Pragmatic Builder voice.

## When to Use

- Alan provides a trend, product launch, repo, architectural spec, or notes and wants an X Article.
- Brainstorming content angles, titles, or cold-open hooks for @GoogleCloudTech.
- Requests to "draft an X article" or "turn this into an article for Google Cloud Tech".

## Core Principles & Non-Negotiables

1. **Brand Voice:** Firsthand collective "we" (the team that built/dogfooded it) and "you" (the reader). Byline placed mid-intro: `By Alan Blount (@zeroasterisk)`.
2. **Alan's Voice (The Pragmatic Builder):** 20-year software engineer turned PM. Allergic to demoware, buzzwords, and marketing fluff. Muted "muppet" warmth and dry observational wit kept strictly below the surface in parenthetical asides `(...)`. Celebrates working systems ("high-fives").
3. **Anti-AI Discipline:** Must pass `references/anti-ai-checklist.md`. Zero em-dashes or en-dashes. Zero AI filler words (`delve`, `tapestry`, `crucial`, `pivotal`, `seamless`, `supercharge`).
4. **Concrete Proof of Depth:** Credibility comes from real protocol fields, named errors, and measurable numbers from Alan's materials. Never invent technical details.
5. **Visuals:** One hero image plus one inline diagram per section in the dark-mode hand-drawn Excalidraw style (`references/diagram-style.md`).

## Workflow Summary

1. **Angles First:** Map trend to Google Cloud Agent Platform (`references/product-map.md`), pull live context via Plushcap MCP (`scripts/plushcap_mcp.py`), and present 3-4 angle candidates (title/hook, broken assumption, section spine, why it wins). Wait for Alan's choice.
2. **Draft:** Write full article following `references/article-skeleton.md` and `references/voice-bank.md`.
3. **Anti-AI Review:** Run `references/anti-ai-checklist.md` (Pass 1 deterministic, Pass 2 judgment).
4. **Diagrams:** Generate hero and section diagrams.
5. **Iterate in Chat:** Review and refine with Alan in chat before touching Google Docs.
6. **Publish:** Push to Google Doc only upon explicit approval.

See [SKILL.md](file:///usr/local/google/home/alanblount/Workspaces/skills/googlecloudtech-x-article/SKILL.md) for full instructions.
