# Plushcap MCP (trend identification)

Plushcap tracks 550+ tech-company engineering blogs, plus YouTube, Hacker News, and derived trend topics. It is the primary trend feed for Step 1 (angles).

## How to call
Plushcap is an external remote MCP server, not a workspace MCP server, so use the bundled connector instead of `call_mcp_tool`:
```
python3 scripts/plushcap_mcp.py <method> '<params-json>'
```
- Auth: the connector reads `PLUSHCAP_API_KEY` from the environment, else from `<skill>/.env` (gitignored).
- Endpoint: https://mcp.plushcap.com/mcp. Needs network: approve the sandbox network prompt once per session.
- A browser User-Agent is set inside the connector; Plushcap is behind Cloudflare, which blocks default library user-agents with "error 1010".

Examples:
```
python3 scripts/plushcap_mcp.py tools/list
python3 scripts/plushcap_mcp.py tools/call '{"name":"get_trends_data","arguments":{"weeks":8}}'
python3 scripts/plushcap_mcp.py tools/call '{"name":"get_trend_topic_data","arguments":{"slug":"ai-guardrails","weeks":8,"post_limit":10}}'
```

## The tools that matter for Step 1
- `get_trends_summary(weeks)`: counts of up/down/emerging. Quick pulse.
- `get_trends_data(weeks)`: the ranked-movers call. Per topic: `latest_wow_change` (week-over-week %), `latest_mention_count`, `latest_company_count`, `latest_post_count`, `weekly_data`, `related_topics`, `concepts`, `implementations`. Rank by `latest_wow_change`, weighted by volume.
- `get_trend_topics()`: the ~33 tracked topic slugs. Maps closely to the content buckets.
- `get_trend_topic_data(slug, weeks, post_limit, post_weeks, space)`: single-topic time series PLUS blog-post evidence (who covered it, summaries, previews). Use for gap analysis: find the white space no one has written well.
- `search_blog_posts(trend_slug|company_slug|space, weeks, limit, include_text)`: competitor coverage on a trend.
- `list_competitive_spaces` / `get_competitive_space_comparison(slug)`: market-category view.
- `list_trend_reports` / `get_trend_report(slug)`: full Markdown trend reports (paid tier). Rich context for a deep piece.
- Supporting signals: `get_youtube_leaderboard`, `get_hackernews_posts`, `compare_companies`, `get_monthly_trend_metrics`, `get_yearly_trend_metrics`.

## Reading the numbers (judgment)
- Prefer topics with real volume AND a positive WoW change. A big percentage on a tiny base (e.g. mlx +1100% at 12 mentions, token-engineering +100% at 2) is an "emerging watch", not a headline.
- The emerging keyword list is noisy: it mixes real signals (scorer, watermarking, context) with generic words (data, code, teams) and vendor marketing surges (clerk, sign-in, m2m = a Clerk auth push). Apply judgment; do not headline a marketing surge.
- Cross-check the topic against `product-map.md` to find the Google wedge, then run `get_trend_topic_data` to find the uncovered angle.

## Snapshot (2026-08-22, illustrative: always pull live)
Real-volume risers: `ai-guardrails` +161% (180 mentions / 17 companies), `zero-trust` +130% (106 / 11), `ai-coding-assistant` +25% (393 / 54), `platform-engineering` +39%, `loop-engineering` +39%, `harness-engineering` +17%. Cooling: `agent-plugins` (post-launch, back to baseline), `mcp` -22% (still the highest volume at 1312), `ai-agents` -31%, `multi-agent-systems` -24%. Emerging watch: `openclaw` +350% (low base).
