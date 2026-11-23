# Brand DNA Schema Reference

The `brand_dna.json` file captures the high-level aesthetic DNA, typographic classification, palette architecture, and design ethos derived from web sources and screenshots.

---

## JSON Schema Structure

```json
{
  "colors": [
    {
      "name": "Cobalt Action",
      "hex": "#1D54D8"
    },
    {
      "name": "Pristine White",
      "hex": "#FFFFFF"
    },
    {
      "name": "Ghost Slate",
      "hex": "#F8FAFC"
    },
    {
      "name": "Neutral Slate",
      "hex": "#475569"
    }
  ],
  "fonts": {
    "headline": "Inter",
    "body": "Inter",
    "classification": "Modern Neo-Grotesque Sans-serif"
  },
  "tone": [
    "minimalist",
    "focused",
    "approachable",
    "utilitarian"
  ],
  "summary": "A hyper-focused, minimalist interface prioritizing generous whitespace, soft elevation, and crisp blue CTAs.",
  "design_md_lines": [
    "---",
    "version: 1.0",
    "colors:",
    "  primary: '#1D54D8'",
    "---",
    "",
    "## Overview",
    "..."
  ]
}
```

---

## Field Definitions

| Field | Type | Description |
|---|---|---|
| `colors` | array of objects | Named color palette entries with human-readable agency names and uppercase hex codes. |
| `fonts` | object | Typographic pairing specifying `headline`, `body`, and typeface `classification`. |
| `tone` | array of strings | 3 to 6 evocative aesthetic keywords describing visual ethos and mood. |
| `summary` | string | Sophisticated narrative summary of brand philosophy and visual positioning. |
| `design_md_lines` | array of strings | (Optional) Complete line-by-line array representation of the generated `DESIGN.md` file. |
