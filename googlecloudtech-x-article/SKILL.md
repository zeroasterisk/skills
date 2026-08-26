---
description: |
  Alan's standard workflow to produce a high-impact, viral X Article for the @GoogleCloudTech
  brand account from a trend, architecture pattern, repo, or launch: connect the trend to Google Cloud
  Agent Platform + live developer context, propose title/hook angles first, draft to the proven structure
  in Alan's Pragmatic Builder voice (20-year dev experience, muted "muppet" warmth, dry technical wit,
  parenthetical asides, zero em-dashes, and strict anti-AI discipline), generate dark-mode hand-drawn
  diagrams, and publish to a Google Doc on approval. Use whenever Alan wants to draft an X Article, turn
  a trend/spec/repo into an article, or brainstorm @GoogleCloudTech content angles.
name: googlecloudtech-x-article
license: MIT
metadata:
  version: "2.0.0"
---

# GoogleCloudTech X Article (Alan Blount Edition)

Alan's standard, repeatable method to turn a trend, launch, spec, or architectural breakthrough into a high-performing X Article for the **@GoogleCloudTech** brand account. The job of this skill is to structure, voice, quality-gate, and illustrate what Alan brings. It does not pick the topic out of thin air, and it never invents technical details.

---

## When to Use

- Alan provides a trend, product launch, repo, architectural spec, or notes and wants an X Article.
- Brainstorming content angles, titles, or cold-open hooks for @GoogleCloudTech.
- Any request like "let's write / draft an X article" or "turn this into an article for Google Cloud Tech".

---

## Non-Negotiables (Read Before Doing Anything)

1. **Channel is @GoogleCloudTech (Google Brand Account):**
   - Voice is firsthand but collective: "we" (the team that built, dogfooded, or broke it) and "you" (the reader).
   - Author credit goes in a mid-intro byline: `By Alan Blount (@zeroasterisk)`.
   - Never write in a personal-diary voice ("I installed it on my laptop this weekend"); that belongs on a personal account. Keep it grounded in collective engineering reality.
2. **Alan's Authentic Voice (The Pragmatic Builder):**
   - 20-year software engineer turned PM. Allergic to demoware, buzzwords, and marketing puffery.
   - **Muted "Muppet" Factor:** Bring earnest, nerdy enthusiasm and dry observational wit, but keep it muted just below the surface of a clean, authoritative DevRel register. Use parenthetical asides `(...)` for self-deprecating humor or internal winks.
   - High-fives for things that actually work in production.
3. **Strict Anti-AI Discipline (The Humanizer Standard):**
   - The article must read like an experienced human engineer wrote it, never a chatbot.
   - Run `references/anti-ai-checklist.md` on every draft before Alan sees it.
4. **Zero Em-Dashes. Ever.**
   - No em-dashes or en-dashes anywhere in the text. Use commas, colons, periods, or conversational parentheses.
5. **Never Fabricate a Technical Detail:**
   - Credibility comes from un-fakeable specifics: named protocol fields, real error names, exact token or latency numbers, and edge cases. If a detail is missing from Alan's source material, ask him or omit it.
6. **High Accuracy Bar (Google's Name Is on It):**
   - Verify every product, API, model, and protocol name against `references/product-map.md` and official sources. Mark unconfirmed numbers "illustrative".
7. **Input Comes from Alan; Volatile Facts Come from Live Sources:**
   - Pull current launches, roadmap items, and trend numbers live each run. Never publish need-to-know roadmap.

---

## Workflow

### Step 1: Angles First (Before Any Drafting)
Connect the trend to Google Cloud's agent ecosystem and live developer conversations.
1. **Map to Products:** Map the trend to the right products using `references/product-map.md` (e.g., ADK, A2A, MCP, A2UI, UCP, Agent Plugins, Agent Gateway, Model Armor, Agent Observability).
2. **Pull Live Context:**
   - **Trends (Primary Feed):** The Plushcap MCP connector (see `references/plushcap.md`). Run `get_trends_data` for ranked movers, then `get_trend_topic_data` for topic gap analysis. Weight by real volume, not raw percentage.
   - **Internal Signals:** Search Drive for content trackers and trend briefs. Flag public vs need-to-know.
   - **External Signals:** Run web searches for live developer discussions, competitor benchmarks, and OSS sentiment.
3. **Find the Anchor Artifact:** Identify the concrete artifact that gives the piece credibility: a repo, spec, benchmark, or firsthand dogfooding result.
4. **Present 3-4 Angle Candidates:**
   For each candidate, provide:
   - **Title / Hook:** Numbered listicle or flat thesis claim (see `references/article-skeleton.md`).
   - **The Assumption the Cold Open Kills:** The common myth or naive assumption being dismantled.
   - **The Section Spine:** What the article covers.
   - **Why It Wins:** The specific gap it fills or data shape that performs on @GoogleCloudTech.
5. **Wait for Approval:** Let Alan pick or redirect before drafting.

### Step 2: Draft the Article
Draft the complete article following `references/article-skeleton.md` in the voice defined in `references/voice-bank.md`.
- Code must be real and runnable, included only when earned.
- Ground every claim in an exact number, named artifact, or firsthand result.
- Keep the "What with Why" structure clear throughout.

### Step 3: Self-Review (Anti-AI Gate)
Grade the draft against `references/anti-ai-checklist.md`:
- **Pass 1 (Deterministic):** Scan for em-dashes, banned AI vocabulary, staccato triples, emojis, and title-case headings. Fix every failure.
- **Pass 2 (Judgment):** Check voice authenticity, muted muppet warmth, technical depth, and absence of generic optimism.

### Step 4: Generate Diagrams
Produce a hero image plus one diagram per section using the house style in `references/diagram-style.md` (dark-mode hand-drawn whiteboard sketch, Excalidraw aesthetic). If image generation is disabled in the session, notify Alan before promising diagrams.

### Step 5: Iterate in Chat
Present the draft and diagrams in chat. Iterate on feedback here. Do NOT create a Google Doc yet.

### Step 6: Publish to Google Doc (Only on Explicit Approval)
Lay out the approved piece in a Google Doc:
- Assets link at the very top (Drive folder).
- Hero image.
- Title and cold open.
- Byline mid-intro: `By Alan Blount (@zeroasterisk)`.
- Numbered sections with embedded diagrams.
- Synthesis beat and actionable "Get started today" / "Verify it yourself" close.
- Cross-link to the previous article in the series.

---

## References

- `references/article-skeleton.md`: The exact section-by-section structure and requirements.
- `references/voice-bank.md`: Alan's brand voice rules, hard bans, and real exemplar paragraphs.
- `references/anti-ai-checklist.md`: The deterministic kill-list and judgment rubric.
- `references/product-map.md`: Google Cloud Agent Platform map and trend mapping.
- `references/diagram-style.md`: Hand-drawn dark-mode Excalidraw style guide.
- `references/plushcap.md`: Guide to using Plushcap MCP for live trend intelligence.
