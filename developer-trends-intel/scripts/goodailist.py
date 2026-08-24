#!/usr/bin/env python3
"""Good AI List CLI — Query open source AI repos, developers, and trending metrics."""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://goodailist.com"


def fetch_api(endpoint: str, params: dict | None = None) -> dict:
  """Fetch JSON from Good AI List API."""
  url = f"{BASE_URL}{endpoint}"
  if params:
    clean_params = {k: str(v) for k, v in params.items() if v is not None}
    if clean_params:
      url += "?" + urllib.parse.urlencode(clean_params)

  req = urllib.request.Request(
      url,
      headers={
          "User-Agent": "developer-trends-intel-skill/1.0",
          "Accept": "application/json",
      },
  )
  try:
    with urllib.request.urlopen(req, timeout=20) as resp:
      return json.loads(resp.read().decode("utf-8"))
  except urllib.error.HTTPError as e:
    sys.stderr.write(f"HTTP Error {e.code}: {e.reason}\n")
    try:
      err_body = e.read().decode("utf-8")
      sys.stderr.write(f"Details: {err_body}\n")
    except Exception:
      pass
    sys.exit(1)
  except Exception as e:
    sys.stderr.write(f"Network error: {e}\n")
    sys.exit(1)


def fmt_num(val) -> str:
  if val is None:
    return "-"
  try:
    return f"{int(val):,}"
  except (ValueError, TypeError):
    return str(val)


def fmt_growth(val, pct=False) -> str:
  if val is None:
    return "-"
  try:
    n = float(val)
    if pct:
      return f"{n:+.1f}%" if n != 0 else "0.0%"
    return f"{int(n):+,}" if n != 0 else "0"
  except (ValueError, TypeError):
    return str(val)


def cmd_summary(args):
  data = fetch_api("/api/summary")
  if args.json:
    print(json.dumps(data, indent=2))
    return

  print("=" * 60)
  print(" Good AI List — Ecosystem Overview")
  print("=" * 60)
  print(f"Total AI Repos:     {fmt_num(data.get('total_repos'))}")
  print(f"Total Developers:   {fmt_num(data.get('total_devs'))}")
  print(f"Total Stars:        {fmt_num(data.get('total_stars'))}")
  print(f"Last Updated:       {data.get('updated_at', 'N/A')}")
  print("=" * 60)


def cmd_filters(args):
  data = fetch_api("/api/repos/filters")
  if args.json:
    print(json.dumps(data, indent=2))
    return

  print("### Available Categories:")
  for cat in data.get("categories", []):
    print(f"  - {cat}")

  if args.subcategories:
    print("\n### Available Subcategories:")
    for sub in data.get("subcategories", []):
      print(f"  - {sub}")

  if args.keywords:
    print("\n### Top Keywords:")
    for kw in data.get("keywords", []):
      print(f"  - {kw}")

  if args.countries:
    print("\n### Countries Tracked:")
    for c in data.get("countries", []):
      print(f"  - {c}")


def cmd_repos(args):
  sort_by = args.sort
  if args.by_pct:
    if sort_by == "star_1d":
      sort_by = "star_1d_pct"
    elif sort_by == "star_7d":
      sort_by = "star_7d_pct"

  params = {
      "search": args.search,
      "category": args.category,
      "subcategory": args.subcat,
      "country": args.country,
      "keyword": args.keyword,
      "is_new": "1" if args.new else None,
      "sort_by": sort_by,
      "sort_order": args.order,
      "page": args.page,
      "limit": args.limit,
  }
  data = fetch_api("/api/repos", params)
  if args.json:
    print(json.dumps(data, indent=2))
    return

  repos = data.get("repos", [])
  total = data.get("total", len(repos))
  page = data.get("page", 1)
  pages = data.get("pages", 1)

  print(f"\n--- Repositories (Page {page}/{pages}, Total: {total:,}) ---")
  if not repos:
    print("No matching repositories found.")
    return

  for r in repos:
    repo = r.get("repo", "Unknown")
    stars = fmt_num(r.get("stars"))
    s1d = fmt_growth(r.get("star_1d"))
    s1d_pct = fmt_growth(r.get("star_1d_pct"), pct=True)
    s7d = fmt_growth(r.get("star_7d"))
    cat = r.get("category", "")
    subcat = r.get("subcat", "")
    desc = (r.get("description") or "").strip()
    is_new = " [NEW TODAY]" if r.get("is_new") else ""
    country = f" ({r.get('country')})" if r.get("country") else ""
    lang = f" [{r.get('language')}]" if r.get("language") else ""

    print(f"\n• {repo}{is_new}{lang}{country}")
    print(
        f"  Stars: {stars} | +1d: {s1d} ({s1d_pct}) | +7d: {s7d} | Category:"
        f" {cat} > {subcat}"
    )
    if desc:
      print(f"  Description: {desc[:120] + '...' if len(desc) > 120 else desc}")
    if r.get("top_devs"):
      print(f"  Top Devs: {r.get('top_devs')}")


def cmd_trending(args):
  sort_field = f"star_{args.window}"
  if args.by_pct:
    sort_field = f"star_{args.window}_pct"

  args.sort = sort_field
  args.order = "desc"
  args.new = False
  args.subcat = None
  args.country = None
  args.keyword = None
  args.page = 1
  cmd_repos(args)


def cmd_new(args):
  args.sort = "stars"
  args.order = "desc"
  args.new = True
  args.search = None
  args.subcat = None
  args.country = None
  args.keyword = None
  args.by_pct = False
  args.page = 1
  cmd_repos(args)


def cmd_devs(args):
  params = {
      "search": args.search,
      "country": args.country,
      "city": args.city,
      "min_repos": args.min_repos,
      "sort_by": args.sort,
      "sort_order": args.order,
      "page": args.page,
      "limit": args.limit,
  }
  data = fetch_api("/api/devs", params)
  if args.json:
    print(json.dumps(data, indent=2))
    return

  devs = data.get("devs", [])
  total = data.get("total", len(devs))
  page = data.get("page", 1)
  pages = data.get("pages", 1)

  print(f"\n--- AI Developers (Page {page}/{pages}, Total: {total:,}) ---")
  if not devs:
    print("No matching developers found.")
    return

  for d in devs:
    user = d.get("User") or d.get("login") or "Unknown"
    name = f" ({d.get('Name')})" if d.get("Name") else ""
    country = f" [{d.get('Country')}]" if d.get("Country") else ""
    repos_cnt = fmt_num(d.get("Repos"))
    contribs = fmt_num(d.get("Contributions"))
    w_contribs = fmt_num(d.get("Weighted contributions"))
    top_repos = d.get("Top repos") or ""

    print(f"\n• {user}{name}{country}")
    print(
        f"  Repos: {repos_cnt} | Contributions: {contribs} (Weighted:"
        f" {w_contribs})"
    )
    if top_repos:
      print(f"  Top Repos: {top_repos}")


def main():
  parser = argparse.ArgumentParser(
      description="Good AI List CLI — AI Repository & Developer Intelligence"
  )
  subparsers = parser.add_subparsers(dest="command", required=True)

  # summary
  p_summary = subparsers.add_parser("summary", help="Show ecosystem overview")
  p_summary.add_argument("--json", action="store_true", help="Output JSON")
  p_summary.set_defaults(func=cmd_summary)

  # filters
  p_filters = subparsers.add_parser(
      "filters", help="List available categories and subcategories"
  )
  p_filters.add_argument(
      "--subcategories",
      action="store_true",
      help="Include all subcategories",
  )
  p_filters.add_argument(
      "--keywords", action="store_true", help="Include all keywords"
  )
  p_filters.add_argument(
      "--countries", action="store_true", help="Include all countries"
  )
  p_filters.add_argument("--json", action="store_true", help="Output JSON")
  p_filters.set_defaults(func=cmd_filters)

  # repos
  p_repos = subparsers.add_parser(
      "repos", help="Search and filter AI repositories"
  )
  p_repos.add_argument("--search", type=str, help="Search query")
  p_repos.add_argument("--category", type=str, help="Category name")
  p_repos.add_argument("--subcat", type=str, help="Subcategory name")
  p_repos.add_argument("--country", type=str, help="Country name")
  p_repos.add_argument("--keyword", type=str, help="Keyword tag")
  p_repos.add_argument(
      "--new", action="store_true", help="Only repos added today"
  )
  p_repos.add_argument(
      "--sort",
      type=str,
      default="star_1d",
      choices=[
          "star_1d",
          "star_1d_pct",
          "star_7d",
          "star_7d_pct",
          "stars",
          "forks",
          "contributors",
          "created_at",
          "updated_at",
      ],
      help="Sort column",
  )
  p_repos.add_argument(
      "--by-pct", action="store_true", help="Sort by percentage star growth"
  )
  p_repos.add_argument(
      "--order",
      type=str,
      default="desc",
      choices=["desc", "asc"],
      help="Sort order",
  )
  p_repos.add_argument(
      "--limit", type=int, default=15, help="Number of results"
  )
  p_repos.add_argument("--page", type=int, default=1, help="Page number")
  p_repos.add_argument("--json", action="store_true", help="Output JSON")
  p_repos.set_defaults(func=cmd_repos)

  # trending
  p_trending = subparsers.add_parser(
      "trending", help="Get fastest growing AI repositories"
  )
  p_trending.add_argument(
      "--window",
      type=str,
      default="1d",
      choices=["1d", "7d"],
      help="Time window (1d or 7d)",
  )
  p_trending.add_argument(
      "--by-pct", action="store_true", help="Sort by percentage star growth"
  )
  p_trending.add_argument("--category", type=str, help="Filter by category")
  p_trending.add_argument(
      "--search", type=str, help="Filter trending by keyword"
  )
  p_trending.add_argument(
      "--limit", type=int, default=15, help="Number of results"
  )
  p_trending.add_argument("--json", action="store_true", help="Output JSON")
  p_trending.set_defaults(func=cmd_trending)

  # new
  p_new = subparsers.add_parser(
      "new", help="List newly indexed repositories added today"
  )
  p_new.add_argument("--category", type=str, help="Filter by category")
  p_new.add_argument("--limit", type=int, default=15, help="Number of results")
  p_new.add_argument("--json", action="store_true", help="Output JSON")
  p_new.set_defaults(func=cmd_new)

  # devs
  p_devs = subparsers.add_parser(
      "devs", help="Search and rank top AI developers"
  )
  p_devs.add_argument(
      "--search", type=str, help="Search by username or real name"
  )
  p_devs.add_argument("--country", type=str, help="Filter by country")
  p_devs.add_argument("--city", type=str, help="Filter by city")
  p_devs.add_argument(
      "--min-repos", type=int, default=1, help="Minimum repo count"
  )
  p_devs.add_argument(
      "--sort",
      type=str,
      default="weighted_contributions",
      choices=["weighted_contributions", "contributions", "repos"],
      help="Sort column",
  )
  p_devs.add_argument(
      "--order",
      type=str,
      default="desc",
      choices=["desc", "asc"],
      help="Sort order",
  )
  p_devs.add_argument(
      "--limit", type=int, default=15, help="Number of results"
  )
  p_devs.add_argument("--page", type=int, default=1, help="Page number")
  p_devs.add_argument("--json", action="store_true", help="Output JSON")
  p_devs.set_defaults(func=cmd_devs)

  args = parser.parse_args()
  args.func(args)


if __name__ == "__main__":
  main()
