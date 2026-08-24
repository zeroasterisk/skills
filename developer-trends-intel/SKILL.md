---
name: developer-trends-intel
description: >-
  Synthesizes AI and developer ecosystem intelligence by combining Plushcap MCP (tech company engineering blogs, YouTube metrics, Hacker News activity, competitive spaces, and industry trend topics) with Good AI List (19,500+ open-source AI repositories, daily/weekly star velocity, developer activity, and category taxonomies). Use when asked to investigate AI tech trends, discover fast-growing open-source AI projects or breakout GitHub repositories, research tech company engineering momentum or blog activity, lookup items on goodailist.com or Plushcap, track developer metrics, analyze competitive spaces, or cross-reference enterprise tech announcements with open-source ecosystem adoption. Don't use for generic non-tech web search (use search_web) or single-file git operations (use vcs).
---

# Developer & AI Trends Intelligence

Combines enterprise tech momentum (via **Plushcap MCP**) with open-source developer adoption (via **Good AI List**) to deliver multi-dimensional trend analysis, competitive benchmarking, and breakout project discovery.

```
┌──────────────────────────────────────┐       ┌──────────────────────────────────────┐
│             Plushcap MCP             │       │             Good AI List             │
│   (550+ Tech Company Org Blogs,      │  ◄─►  │    (19,500+ Open-Source AI Repos,    │
│    YouTube Metrics, Hacker News,     │       │     Daily/Weekly Star Gainers,       │
│    Competitive Spaces, Topic Trends) │       │     200,000+ AI Devs, Subcategories) │
└──────────────────┬───────────────────┘       └──────────────────┬───────────────────┘
                   └───────────────────► ◄────────────────────────┘
                                         ▼
                   Unified Tech & Developer Intelligence
```

---

## Quick Reference

| Source | Primary Scope | How to Invoke | Deep Reference |
| :--- | :--- | :--- | :--- |
| **Plushcap MCP** | Enterprise blogs, HN sentiment, YouTube reach, company spaces | `call_mcp_tool(ServerName="plushcap", ToolName="...", Arguments={...})` | [plushcap_mcp.md](file:///usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/references/plushcap_mcp.md) |
| **Good AI List** | Open-source GitHub repos, daily star velocity, top developers | Direct CLI helper: [goodailist.py](file:///usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py) or REST API (`goodailist.com/api/repos`) | [goodailist_api.md](file:///usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/references/goodailist_api.md) |

---

## 1. Querying Good AI List (`goodailist.com`)

Use the bundled [goodailist.py](file:///usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py) script for instant querying and filtering of 19,500+ AI repositories.

### Common Recipes

```bash
# Ecosystem overview (total repos, devs, stars, last update)
/usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py summary

# Top 1-day star gainers across the entire AI ecosystem
/usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py trending --window 1d --limit 15

# Top 7-day surging projects by percentage growth
/usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py trending --window 7d --by-pct --limit 15

# Discover newly indexed repositories added today
/usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py new --limit 15

# Search repositories with specific keywords or category filters
/usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py repos --search "mcp" --category "AI Engineering" --limit 10

# Search repositories in agent orchestration subcategories
/usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py repos --subcat "Build agent workflow (SDK)" --sort star_1d --limit 10

# Search top developers by name, country, or city
/usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py devs --search "karpathy"
/usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py devs --city "San Francisco" --limit 10

# Output raw JSON for programmatic analysis
/usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py repos --search "deepseek" --json
```

---

## 2. Querying Plushcap MCP

Call tools on the `plushcap` MCP server using `call_mcp_tool`.

### Key MCP Calls

1. **Ecosystem Trends Summary:**
   ```json
   call_mcp_tool(ServerName="plushcap", ToolName="get_trends_summary", Arguments={"weeks": 12})
   ```
2. **List Active Trend Topics:**
   ```json
   call_mcp_tool(ServerName="plushcap", ToolName="get_trend_topics", Arguments={"page": 1, "page_size": 50})
   ```
3. **Deep Topic Time-Series & Blog Evidence:**
   ```json
   call_mcp_tool(ServerName="plushcap", ToolName="get_trend_topic_data", Arguments={"slug": "ai-agents", "weeks": 12, "post_limit": 10})
   ```
4. **Company Profile & Competitive Space:**
   ```json
   call_mcp_tool(ServerName="plushcap", ToolName="get_company", Arguments={"slug": "cloudflare"})
   call_mcp_tool(ServerName="plushcap", ToolName="list_competitive_spaces", Arguments={"search": "agent"})
   ```
5. **Search Engineering Blog Posts:**
   ```json
   call_mcp_tool(ServerName="plushcap", ToolName="search_blog_posts", Arguments={"trend_slug": "ai-guardrails", "days": 30, "limit": 10})
   ```
6. **Company Public Sentiment & Reach:**
   ```json
   call_mcp_tool(ServerName="plushcap", ToolName="get_hackernews_posts", Arguments={"company_slug": "openai", "page_size": 10})
   call_mcp_tool(ServerName="plushcap", ToolName="get_youtube_metrics_latest", Arguments={"company_slug": "anthropic"})
   ```

---

## 3. Core Synthesis Workflows

### Workflow A: Topic / Concept Deep Dive
*Goal: Understand where an AI trend is heading across both enterprise engineering and open source.*
1. **Identify the Topic:** Query Plushcap `get_trend_topics` or `get_trends_data` for topic velocity, historical mention curves, and emerging concept tags.
2. **Read Company Evidence:** Call `get_trend_topic_data` and `search_blog_posts` to see which enterprise engineering teams are shipping production architectures.
3. **Find Open Source Implementations:** Run `goodailist.py repos --search "<topic>" --sort star_1d` and `goodailist.py repos --subcat "<subcat>"` to uncover the fastest-growing GitHub tools, libraries, and protocols in that space.
4. **Synthesize:** Compare enterprise architectural focus with grassroots developer adoption patterns.

### Workflow B: Company Intelligence & Open Source Footprint
*Goal: Profile a company's total developer footprint (blogs, HN traction, open-source repositories, developer community).*
1. **Detect / Resolve Company:** Use `detect_company_from_url` or `list_companies` to obtain the official `company_slug`.
2. **Inspect Corporate Output:** Call `get_company`, `search_blog_posts(company_slug=...)`, and `get_hackernews_latest`.
3. **Check Open Source Repos:** Run `goodailist.py repos --search "<org_or_product_name>"` to find open-source repositories, star trajectories, and contributor networks.
4. **Benchmark Peers:** Use `compare_companies` or `get_competitive_space_comparison` to evaluate against peers.

### Workflow C: Scouting Emerging & Breakout Tech
*Goal: Detect early breakout repositories and cross-check if they represent a broader industry shift.*
1. **Scan Velocity Signals:** Run `goodailist.py trending --window 1d --by-pct --limit 20` and `goodailist.py new --limit 20`.
2. **Isolate Breakout Themes:** Note recurring keywords, frameworks, or subcategories (e.g. MCP implementations, local SLM harnesses, synthetic evaluation).
3. **Validate Industry Mentions:** Query Plushcap `get_trends_summary` and `search_blog_posts` with relevant keywords to see if corporate blogs or HN discussions are surging around the same concept.

---

## 4. Gotchas & Best Practices

1. **Plushcap Pagination:** `get_trend_topics`, `list_companies`, `get_hackernews_posts`, etc., use `page` (integer) and `page_size` (integer, max 200). Do NOT pass `limit` or `weeks` to `get_trend_topics`.
2. **Company Slugs:** Always look up exact slugs via `list_companies(search="...")` or `detect_company_from_url(url="...")` before calling slug-specific tools like `get_company` or `compare_companies`.
3. **Good AI List Star Velocity:** `star_1d` reflects absolute daily star gain, while `star_1d_pct` highlights viral small/new projects surging from a lower star base. Use `--by-pct` to catch early breakout signals.
4. **Direct Script Execution:** When running Good AI List queries in terminal commands, use the direct absolute path `/usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py` rather than relative paths or shell aliases.
