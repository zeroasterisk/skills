# Diagram House Style: X-Optimized Engineering Notebook Slides

Every @GoogleCloudTech X Article needs a **Hero Slide** plus **one High-Level Slide per numbered section**.
Because X crops and scales inline 16:9 images down to **350px–600px wide** on mobile and desktop timelines, detailed architectural schematics with small text are completely unreadable on X.

**Golden Rule:** Build **high-level, informal keynote slides** on warm Engineering Graph Paper using **programmatic HTML/CSS + Headless Chromium** (`scripts/render_x_slides.py`), NOT dense diagrams or text-garbling AI diffusion.

---

## 1. Non-Negotiable X Legibility & Word Budget Rules

1. **Strict Word Cap (`< 30 Words Total` per Slide):**
   - Never put paragraphs, multi-sentence bullets, or full code files on a slide.
   - If a label or badge wraps onto a second line inside a pill, shorten it (`white-space: nowrap`).
2. **Slightly Informal, Opinionated Tone:**
   - Use conversational builder contrasts (`"Gentle Suggestions"` vs `"Two-Layer Network Defense"`, `"The Hobbyist Trap"`, `"Dave from Accounting"`, `"Math Sees Valid JSON"`).
   - End every slide with a single punchy **Pragmatic Builder Rule** pill in the bottom-left footer.
3. **Zero Em-Dashes or En-Dashes:**
   - Use middle dots (`·`), colons (`:`), or arrows (`➔`) instead.

---

## 2. Visual System & CSS Tokens (`1920x1080` Canvas)

### Canvas & Grid
- **Background:** Warm off-white graph paper (`#faf6ed`) with a `48px × 48px` engineering grid (`1.5px` lines in `#e6dfd1`).
- **Outer Padding:** `68px 88px 56px 88px` (`display: flex; flex-direction: column; justify-content: space-between;`).

### Typography Scale (Minimum Sizes on `1920x1080`)
- **Eyebrow Pill:** `20px` `JetBrains Mono` bold, uppercase, `#faf6ed` text on `#18181b` pill (`border-radius: 999px; padding: 10px 22px; box-shadow: 4px 4px 0px #c9bfa8`).
- **Slide Headline:** `64px` `Space Grotesk` (`font-weight: 700; letter-spacing: -1.2px; line-height: 1.08`). Highlight the 2–3 most important words in a bordered pastel box (`border: 3px solid #18181b; border-radius: 14px; padding: 2px 18px`).
- **Card Titles:** `38px–46px` `Space Grotesk` bold.
- **Step Rows / Check Chips:** `24px–28px` `Inter` bold inside bordered white/pastel pills (`border: 3px solid #18181b; border-radius: 16px; box-shadow: 4px 4px 0px #18181b; white-space: nowrap`).
- **Footer Takeaway Pill:** `22px` `Inter` bold in a warm sand badge (`background: #f2d6b3; border: 2.5px solid #18181b; border-radius: 12px; padding: 8px 20px`) paired with `@GoogleCloudTech · @zeroasterisk` on the right.

### Tactile Neo-Brutalist Notebook Cards
- **Card Container:** `border: 4px solid #18181b; border-radius: 28px; box-shadow: 10px 10px 0px #18181b; padding: 44px;`
- **Semantic Card Fills & Accent Pills:**
  - **Green (Verified / Defense / Target):** Card `#f2fbf5`, Pill `#bbf7d0` (`color: #14532d`), Headline Accent `#c8ead3`
  - **Red (Failure / Naive Prompt / Blocked):** Card `#fff5f5`, Pill `#fecaca` (`color: #7f1d1d`), Headline Accent `#fecaca`
  - **Blue (Deterministic Math / Protocol / Engine):** Card `#f3f6fc`, Pill `#c7d2fe` (`color: #1e3a8a`), Headline Accent `#d0d7f3`
  - **Amber (Caution / Exploit / Human Escalation):** Card `#fffbeb`, Pill `#fde68a` (`color: #78350f`), Headline Accent `#fde68a`

---

## 3. Proven Slide Archetypes

Use these 4 high-level slide layouts across an article:

1. **The `VS` Split Slide (Hero / Thesis):**
   - `grid-template-columns: 1fr 110px 1fr` with a circular yellow `VS` badge (`84px × 84px`) in the center.
   - Left card (`card-red`): The naive assumption (`❌ PROMPT-ONLY GUARDRAILS` -> 3 short step pills ending in `FAIL`).
   - Right card (`card-green`): The production architecture (`✅ DEFENSIVE CO-SCALING` -> 3 numbered layer pills).
2. **The Two-Lane Before/After Pipeline (`AuthN` / Anti-Pattern vs Fix):**
   - Top horizontal lane (`card-red`): `❌ The Hobbyist Trap` showing `[Node 1] ➔ [Node 2] ➔ [Painful Outcome]`.
   - Bottom horizontal lane (`card-green`): `✅ Production Pattern` showing `[Node 1] ➔ [Node 2] ➔ [Verified Outcome]`.
3. **The 3-Column Storyboard (`1. Trigger ➔ 2. Blind Spot ➔ 3. Consequence`):**
   - Three vertical cards connected by bold `52px` `➔` arrows showing how an edge case slips through or gets caught.
4. **The Gateway Filter & Split Outcome (`[Input Card] ➔ [Evaluator Card] ➔ [Top/Bottom Split Outcomes]`):**
   - Left card: Inbound payload or isolated inputs.
   - Center card: The engine (`< 0.5ms CEL` or `Temp 0 Policy Model`) with 3 crisp check pills.
   - Right stacked cards: Top branch (`🚫 Dropped / Auto-Remediation`) + Bottom branch (`✅ Pass / Human Escalation`).

---

## 4. Rendering & Visual QA Workflow

1. **Render Programmatically via `scripts/render_x_slides.py`:**
   - Customize the HTML/CSS slide definitions in `scripts/render_x_slides.py` and run with `google-chrome --headless=new --window-size=1920,1080`.
2. **Mandatory `view_file` Visual Audit:**
   - View every generated `.png` using `view_file` at 100% resolution before embedding.
   - **Check for Wrapped Pills:** If any pill, equation, or chip wraps onto 2 lines (e.g., `VERDICT: DENY (77%` / `SURCHARGE)`), shorten the text by 1–2 words (`VERDICT: DENY (77% FEE)`) and re-render until every pill is a single crisp line.
3. **Sync Across All Surfaces:**
   - Update inline images in the working Google Doc (using surgical index-ranged updates if reviewer comments are active).
   - Update the files in-place in the Google Drive assets folder so file IDs stay stable.
   - Commit both `.html` source templates and `.png` renders to `assets/` in GitHub.
