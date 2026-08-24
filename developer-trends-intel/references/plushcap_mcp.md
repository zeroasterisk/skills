# Plushcap MCP Tool Reference

Plushcap tracks tech company engineering blogs, YouTube metrics, Hacker News posts, competitive spaces, and industry concept/tool trends across 550+ tech organizations.

All tools are accessible via the `plushcap` MCP server using `call_mcp_tool(ServerName="plushcap", ToolName="<tool_name>", Arguments={...})`.

---

## 1. Industry & Trend Analysis

### `get_trends_summary`
* **Purpose:** High-level summary of current tech trends across all tracked company blogs.
* **Arguments:**
  * `weeks` (*integer, optional*): Number of weeks to analyze (default: 12).
* **Returns:** `trending_up`, `trending_down`, `emerging_count`, `total_mentions`, `companies_count`, `mode`.

### `get_trend_topics`
* **Purpose:** List all active trend topics being tracked across company blogs.
* **Arguments:**
  * `page` (*integer, optional*): Page number (default: 1).
  * `page_size` (*integer, optional*): Results per page (default: 50, max: 200).
* **Returns:** List of topics with `id`, `name`, `slug`, `keywords`, `category`, `description`, `trend_kind`.

### `get_trend_topic`
* **Purpose:** Detailed metadata about a specific trend topic by its slug.
* **Arguments:**
  * `slug` (*string, required*): Trend topic slug (e.g. `"ai-agents"`, `"ai-guardrails"`).

### `get_trend_topic_data`
* **Purpose:** Single-trend time-series data plus enriched blog-post evidence.
* **Arguments:**
  * `slug` (*string, required*): Trend topic slug.
  * `weeks` (*integer, optional*): Analysis window in weeks.
  * `space` (*string, optional*): Competitive space slug filter.
  * `post_days` / `post_weeks` / `post_months` (*integer, optional*): Evidence window.
  * `post_limit` (*integer, optional*): Maximum posts to return.

### `get_trends_data`
* **Purpose:** Comprehensive trends data including summary stats, per-topic weekly mentions, week-over-week changes, and emerging velocity scores.
* **Arguments:**
  * `weeks` (*integer, optional*): Number of weeks to analyze.

### `get_monthly_trend_metrics` / `get_yearly_trend_metrics`
* **Purpose:** Raw monthly or yearly trend metric records, previous counts, and period-over-period percentage changes.
* **Arguments:**
  * `topic_slug` (*string, optional*): Specific topic.
  * `space_slug` (*string, optional*): Specific competitive space.
  * `scope` (*string, optional*): Scope filter (`"global"`, `"space"`).
  * `start` / `end` (*string, optional*): Date bounds (`"YYYY-MM"` or `"YYYY"`).
  * `page` / `page_size` (*integer, optional*).

### `list_trend_reports` / `get_trend_report`
* **Purpose:** List and retrieve curated long-form Markdown trend reports.
* **Arguments (`get_trend_report`):**
  * `slug` (*string, required*): Report slug.

---

## 2. Company Intelligence & Tracking

### `list_companies`
* **Purpose:** List and search tech companies tracked by Plushcap.
* **Arguments:**
  * `search` (*string, optional*): Company name or domain search query.
  * `stage` (*string, optional*): Company funding stage.
  * `page` / `page_size` (*integer, optional*).

### `get_company`
* **Purpose:** Detailed profile of a specific company.
* **Arguments:**
  * `slug` (*string, required*): Company slug (e.g. `"anthropic"`, `"cloudflare"`, `"deepseek"`).

### `detect_company_from_url`
* **Purpose:** Map any arbitrary website or blog post URL to its tracked company slug.
* **Arguments:**
  * `url` (*string, required*): The URL to test (e.g. `"https://blog.cloudflare.com/workers-ai"`).

### `compare_companies`
* **Purpose:** Compare 2 to 10 companies across blog word output, YouTube channel growth, and Hacker News traction.
* **Arguments:**
  * `company_slugs` (*array of strings, required*): Slugs to compare (e.g. `["anthropic", "openai", "cohere"]`).
  * `section` (*string, optional*): Focus area (`"blogs"`, `"youtube"`, `"hackernews"`).
  * `start_year` (*integer, optional*): Starting year for historical comparison.

---

## 3. Competitive Spaces

### `list_competitive_spaces`
* **Purpose:** List market categories and competitive spaces.
* **Arguments:**
  * `search` (*string, optional*): Search query.
  * `company_slug` (*string, optional*): Filter spaces containing this company.
  * `space_type` (*string, optional*).

### `get_competitive_space`
* **Purpose:** Get description, space type, and member companies of a competitive space.
* **Arguments:**
  * `slug` (*string, required*): Competitive space slug.

### `get_competitive_space_comparison`
* **Purpose:** Multi-dimensional comparison dashboard for all companies in a space.
* **Arguments:**
  * `slug` (*string, required*): Competitive space slug.
  * `section` (*string, optional*): `"blogs"`, `"youtube"`, `"hackernews"`.

---

## 4. Engineering Blogs & Content

### `search_blog_posts`
* **Purpose:** Search and filter engineering blog posts across all companies.
* **Arguments:**
  * `company_slug` (*string, optional*): Target company.
  * `trend_slug` (*string, optional*): Target trend topic.
  * `space` (*string, optional*): Competitive space.
  * `days` / `weeks` / `months` (*integer, optional*): Recency window.
  * `include_text` (*boolean, default: false*): Include post snippets.
  * `limit` / `offset` (*integer, optional*).

### `get_blog_leaderboard`
* **Purpose:** Rank companies by engineering blog publishing volume and word counts.
* **Arguments:**
  * `min_posts` (*integer, optional*): Minimum post threshold.
  * `min_words` (*integer, optional*): Minimum word count threshold.
  * `sort` (*string, optional*): Sort metric.

### `get_blog_post_company_activity`
* **Purpose:** Real-time stream of companies publishing blog posts in the last N hours.
* **Arguments:**
  * `window_hours` (*integer, default: 72*): Activity window.

---

## 5. Community & Video Signals

### `get_hackernews_posts` / `get_hackernews_latest`
* **Purpose:** Retrieve Hacker News submissions and point trajectories associated with a company.
* **Arguments:**
  * `company_slug` (*string, required*).

### `get_youtube_metrics` / `get_youtube_metrics_latest` / `get_youtube_leaderboard`
* **Purpose:** YouTube subscriber velocity, view growth, and company channel leaderboards.
