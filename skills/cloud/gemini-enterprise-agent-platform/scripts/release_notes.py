#!/usr/bin/env -S uv run --with google-cloud-bigquery
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-cloud-bigquery"]
# ///
"""
Google Cloud Release Notes — agent-ergonomic query tool.

Queries bigquery-public-data.google_cloud_release_notes.release_notes
to research product names, renames, and GA announcements.

Usage:
  ./release_notes.py                        # recent agent/Gemini/Vertex notes (default)
  ./release_notes.py products               # all product names with activity timeline
  ./release_notes.py renames                # notes mentioning renames/rebrandings
  ./release_notes.py product <NAME>         # history for one product (partial match ok)
  ./release_notes.py search <TERM>          # search description text
  ./release_notes.py --project <GCP_PROJECT>  # override default project (alanblount-sandbox)
  ./release_notes.py --limit <N>            # override default result limit (30)
  ./release_notes.py --since <YYYY-MM-DD>   # notes on or after this date
  ./release_notes.py --help                 # this message
"""

import sys
import re
import argparse
from datetime import date, timedelta

DEFAULT_PROJECT = "alanblount-sandbox"
DEFAULT_LIMIT = 30
DEFAULT_SINCE = str(date.today() - timedelta(days=365))  # 1 year back
TABLE = "bigquery-public-data.google_cloud_release_notes.release_notes"

AGENT_PRODUCTS = [
    "%agent%", "%gemini enterprise%", "%vertex ai%",
    "%generative ai on vertex%", "%dialogflow%", "%cx agent studio%",
]


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate(text: str, n: int = 280) -> str:
    if len(text) <= n:
        return text
    return text[:n] + f"… ({len(text)} chars total)"


def run_query(client, sql: str) -> list:
    return list(client.query(sql).result())


def fmt_row(row) -> str:
    desc = truncate(strip_html(row.description))
    return f"{row.published_at} | {row.product_name} | {row.release_note_type}\n  {desc}"


def cmd_default(client, args):
    """Recent notes for agent/Gemini/Vertex products."""
    where = " OR ".join(f"LOWER(product_name) LIKE '{p}'" for p in AGENT_PRODUCTS)
    sql = f"""
    SELECT published_at, product_name, release_note_type, description
    FROM `{TABLE}`
    WHERE ({where}) AND published_at >= '{args.since}'
    ORDER BY published_at DESC
    LIMIT {args.limit}
    """
    rows = run_query(client, sql)
    if not rows:
        print(f"0 results since {args.since}")
        print("hint: Try --since with an earlier date, or use 'products' to see all product names.")
        return
    print(f"release_notes[{len(rows)}]{{published_at,product_name,release_note_type}}:")
    for r in rows:
        print(f"  {fmt_row(r)}")
    print(f"\nhint: Run `./release_notes.py product '<PRODUCT_NAME>'` for full history of one product.")
    print(f"hint: Run `./release_notes.py renames` to find all rename/rebrand announcements.")


def cmd_products(client, args):
    """All product names matching agent/Gemini/Vertex with activity timeline."""
    where = " OR ".join(f"LOWER(product_name) LIKE '{p}'" for p in AGENT_PRODUCTS)
    sql = f"""
    SELECT product_name,
      COUNT(*) AS note_count,
      MIN(published_at) AS first_seen,
      MAX(published_at) AS last_seen
    FROM `{TABLE}`
    WHERE ({where})
    GROUP BY product_name
    ORDER BY last_seen DESC, note_count DESC
    """
    rows = run_query(client, sql)
    if not rows:
        print("0 results")
        return
    print(f"products[{len(rows)}]{{product_name,notes,first_seen,last_seen}}:")
    for r in rows:
        print(f"  {r.product_name:55} | n={r.note_count:4} | {r.first_seen} → {r.last_seen}")
    print(f"\nhint: Run `./release_notes.py product '<NAME>'` for one product's full history.")


def cmd_renames(client, args):
    """Notes mentioning renames, rebrands, or 'now called'."""
    rename_terms = ["%renamed%", "%rebranded%", "%now called%", "%replaces%", "%has been renamed%"]
    where_rename = " OR ".join(f"LOWER(description) LIKE '{t}'" for t in rename_terms)
    where_prod = " OR ".join(f"LOWER(product_name) LIKE '{p}'" for p in AGENT_PRODUCTS)
    sql = f"""
    SELECT published_at, product_name, release_note_type, description
    FROM `{TABLE}`
    WHERE ({where_rename}) AND ({where_prod})
    ORDER BY published_at DESC
    LIMIT {args.limit}
    """
    rows = run_query(client, sql)
    if not rows:
        print("0 rename/rebrand notes found")
        return
    print(f"renames[{len(rows)}]{{published_at,product_name,release_note_type}}:")
    for r in rows:
        print(f"  {fmt_row(r)}")


def cmd_product(client, args):
    """Full history for a specific product name (partial match)."""
    if not args.term:
        print("error: 'product' requires a product name argument")
        print("hint: Run `./release_notes.py products` to see all product names.")
        sys.exit(1)
    term = args.term.lower()
    sql = f"""
    SELECT published_at, product_name, release_note_type, description
    FROM `{TABLE}`
    WHERE LOWER(product_name) LIKE '%{term}%'
    ORDER BY published_at DESC
    LIMIT {args.limit}
    """
    rows = run_query(client, sql)
    if not rows:
        print(f"0 results for product matching '{args.term}'")
        print("hint: Run `./release_notes.py products` to see available product names.")
        return
    print(f"product[{len(rows)}] matching '{args.term}'{{published_at,product_name,release_note_type}}:")
    for r in rows:
        print(f"  {fmt_row(r)}")


def cmd_search(client, args):
    """Search description text for a term."""
    if not args.term:
        print("error: 'search' requires a search term argument")
        sys.exit(1)
    term = args.term.lower()
    where_prod = " OR ".join(f"LOWER(product_name) LIKE '{p}'" for p in AGENT_PRODUCTS)
    sql = f"""
    SELECT published_at, product_name, release_note_type, description
    FROM `{TABLE}`
    WHERE LOWER(description) LIKE '%{term}%'
      AND ({where_prod})
      AND published_at >= '{args.since}'
    ORDER BY published_at DESC
    LIMIT {args.limit}
    """
    rows = run_query(client, sql)
    if not rows:
        print(f"0 results for '{args.term}' since {args.since}")
        print("hint: Try --since with an earlier date, or broaden your search term.")
        return
    print(f"search[{len(rows)}] for '{args.term}'{{published_at,product_name,release_note_type}}:")
    for r in rows:
        print(f"  {fmt_row(r)}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", nargs="?", default="default",
                        choices=["default", "products", "renames", "product", "search"],
                        help="Subcommand (default: recent agent/Gemini/Vertex notes)")
    parser.add_argument("term", nargs="?", default=None,
                        help="Product name or search term (for 'product' and 'search' commands)")
    parser.add_argument("--project", default=DEFAULT_PROJECT,
                        help=f"GCP project for BQ billing (default: {DEFAULT_PROJECT})")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                        help=f"Max results (default: {DEFAULT_LIMIT})")
    parser.add_argument("--since", default=DEFAULT_SINCE,
                        help=f"Start date YYYY-MM-DD (default: {DEFAULT_SINCE})")

    args = parser.parse_args()

    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=args.project)
    except Exception as e:
        print(f"error: Failed to initialize BigQuery client: {e}")
        print("hint: Ensure GOOGLE_CLOUD_PROJECT is set or pass --project, and ADC credentials are available.")
        sys.exit(1)

    try:
        dispatch = {
            "default": cmd_default,
            "products": cmd_products,
            "renames": cmd_renames,
            "product": cmd_product,
            "search": cmd_search,
        }
        dispatch[args.command](client, args)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
