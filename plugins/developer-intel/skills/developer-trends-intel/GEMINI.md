# Developer & AI Trends Intelligence

Synthesizes AI ecosystem and tech industry intelligence by combining **Plushcap MCP** (tech company engineering blogs, YouTube metrics, Hacker News activity, competitive spaces, and industry topics) with **Good AI List** (19,500+ open-source AI repositories, daily/weekly star velocity, and AI developers).

## When to Use

- Researching tech company engineering activity, blog post volume, and topic velocity
- Investigating AI trends, industry sentiment, and competitive spaces
- Querying `goodailist.com` for fastest-growing open-source AI projects, star gainers, or maintainers
- Cross-referencing enterprise tech announcements with open-source developer adoption

## Quick Invocation

### Good AI List
```bash
# Top daily star gainers
/usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py trending --window 1d --limit 15

# Search specific category or subcategory
/usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py repos --search "mcp" --category "AI Engineering" --limit 10

# Search developers
/usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/scripts/goodailist.py devs --search "karpathy"
```

### Plushcap MCP
```json
call_mcp_tool(ServerName="plushcap", ToolName="get_trends_summary", Arguments={"weeks": 12})
call_mcp_tool(ServerName="plushcap", ToolName="get_trend_topics", Arguments={"page": 1, "page_size": 50})
call_mcp_tool(ServerName="plushcap", ToolName="get_company", Arguments={"slug": "cloudflare"})
call_mcp_tool(ServerName="plushcap", ToolName="get_trend_topic_data", Arguments={"slug": "ai-agents", "weeks": 12})
```

See [SKILL.md](file:///usr/local/google/home/alanblount/Workspaces/skills/developer-trends-intel/SKILL.md) for full instructions and multi-source synthesis workflows.
