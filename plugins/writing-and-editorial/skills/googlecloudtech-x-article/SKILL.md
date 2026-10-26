---
description: |
  Alan's standard workflow to produce a high-impact, viral X Article for the @GoogleCloudTech
  brand account from a trend, architecture pattern, repo, or launch: connect the trend to Google Cloud
  Gemini platform + live developer context, propose title/hook angles first, draft to the proven structure
  in Alan's Pragmatic Builder voice (20-year dev experience, muted "muppet" warmth, dry technical wit,
  parenthetical asides, zero em-dashes, and strict anti-AI discipline), generate clean Engineering Graph
  Paper diagrams, and publish to a Google Doc on approval. Use whenever Alan wants to draft an X Article, turn
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

### Step 4: Generate High-Level X-Optimized Slides
Produce a hero slide plus one high-level slide per numbered section following `references/diagram-style.md` and `scripts/render_x_slides.py`:
- **Optimize for X Mobile/Desktop Feeds:** Keep every slide under **30 words total** with `64px` headlines, `38px–46px` card titles, single-line `24px–28px` pills (`white-space: nowrap`), and an informal Pragmatic Builder footer callout.
- **Render Programmatically:** Use `scripts/render_x_slides.py` (HTML/CSS on `#faf6ed` warm graph paper with `4px solid #18181b` borders and `10px 10px 0px #18181b` shadows via headless Chrome) rather than dense architectural schematics or AI diffusion.
- **Visual QA Gate:** Inspect every generated PNG with `view_file` and fix any multi-line pill wraps before showing Alan or updating Google Docs/Drive.

### Step 5: Iterate in Chat
Present the draft and diagrams in chat. Iterate on feedback here. Do NOT create a Google Doc yet.

### Step 6: Publish & Update Google Doc (Only on Explicit Approval)
Lay out the approved piece in a Google Doc:
- Assets link at the very top (Drive folder: `### Drive Folder for Artifacts: [Folder Name](url)`).
- Hero image.
- Title and cold open.
- Byline mid-intro: `By Alan Blount (@zeroasterisk)` (plus co-authors).
- Numbered sections with embedded diagrams.
- Synthesis beat and actionable "Get started today" / "Verify it yourself" close.
- Cross-link to the previous article in the series.
- **Preserving Inline Comments on Edits:** Once a Google Doc has active reviewer comments, NEVER overwrite the entire document body (which wipes comment anchors). Apply surgical index-ranged batch updates and verify zero broken comment anchors afterward.
- **Google Docs Markdown Parser Gotcha:** Never nest markdown links `[text](url)` inside bold spans `**...**` when importing to Google Docs; keep links outside bold spans (`**Title**: [link](url)`) so literal `**` characters do not leak into the document.

### Step 7: Handoff & Portfolio Roundups in Team Chat
When handing off one or more articles to social/publishing leads in your content sprint room:
1. **Multi-Message Thread Pacing (Never One Giant Wall of Text):**
   - **Thread Starter:** 1-line bracketed header (`[Roundup of <Topic> X articles to enqueue @ N right now, with followups 🧵]`) so the main room stream stays clean.
   - **Message 1 (Portfolio Body):** Tag the publishing leads, soften scheduling urgency with a conversational parenthetical (`with the first two ready to schedule today (or whenever):`), and list each article.
   - **Message 2 (Rollout Order):** Post `Proposed rollout order:` as a separate short bulleted reply (`* Ship #1...`, `* Ship #2...`) so the scheduling sequence stands out instead of getting buried at the bottom of a long post.
   - **Message 3 (Forward-Looking Caveats):** Post a short `NOTE:` reply if upcoming OSS repos, tooling, or new model weights within days might shift the rollout order.
2. **Per-Item Formatting & Signal Hygiene:**
   - **Avoid the CommonMark `<ol>` Reset Trap:** In CommonMark-based Chat parsers, following `1. Title` with unindented `-` bullets closes the ordered list and resets every subsequent item to `1.`. Bold the numbered title (`*1. Title* (Ready to ship)`) and use flat single-level `*` bullets underneath.
   - **Titled Doc Links Only:** Always format `Doc:` as a titled link (`[Exact Doc Title](url)`), never a raw URL.
   - **No Separate `Assets:` Line in Chat:** Since the Drive folder link is already at line 1 of the Google Doc, omit `Assets:` from the Chat summary so it doesn't clutter the message or spawn redundant Drive attachment cards.
   - **Never Contradict `(Ready to ship)` with `"In review with..."`:** Only include a `Sign-offs:` bullet when recording a completed LGTM (e.g. `Sign-offs: LGTM from domain lead + peer review.`). Never write `Review: In review with ...` on a ready-to-ship item; it signals to publishing leads that the piece is blocked.
   - **1–2 Sentence Pitch-Altitude `Angle:`:** Keep `Angle:` to a 1–2 sentence hook plus the single winning headline metric (e.g. `Winning route: 100% accuracy, 14.9% cheaper, 1.87x faster...`). Cut negative/methodology sub-bullets and exhaustive platform lists.

---

## References

- `references/article-skeleton.md`: The exact section-by-section structure and requirements.
- `references/voice-bank.md`: Alan's brand voice rules, hard bans, and real exemplar paragraphs.
- `references/anti-ai-checklist.md`: The deterministic kill-list and judgment rubric.
- `references/product-map.md`: Google Cloud Gemini platform map and trend mapping.
- `references/diagram-style.md`: Diagram house style guide (Engineering Graph Paper default, whiteboard sketch alternative).
- `references/plushcap.md`: Guide to using Plushcap MCP for live trend intelligence.
