# Article Skeleton (Alan Blount / @GoogleCloudTech)

Every high-performing @GoogleCloudTech X Article follows this proven structure. Order matters. Length typically runs 1,000 to 1,700 words of crisp technical prose, plus runnable code snippets where earned and one hand-drawn diagram per section.

---

## 1. Assets Link (Top Line)
An internal production link placed at the very top of the draft:
`Drive Link for Assets: [Folder Name](https://drive.google.com/...)`
Points to the diagram source folder. Omitted from the final public post.

---

## 2. Title
Two shapes perform consistently:
- **Numbered Listicle:**
  - *"5 Agent Skill design patterns every ADK developer should know"*
  - *"7 Rules for resilient agent loops every engineer should know"*
  - *"5 Architecture patterns to learn from DeepSeek's open-source harness"*
- **Flat Thesis Claim:**
  - *"Agent Plugins are the future of portable agent skills"*
  - *"Generative UI is a data format, not a rendering engine"*

*Rules:* No colon-plus-subtitle stacks, no "Gemini" in the title, sentence case, lowercase "agents".

---

## 3. Hero Image
Immediately following the title. Hand-drawn dark-mode Excalidraw style (see `references/diagram-style.md`).

---

## 4. Cold Open (1-2 Sentences)
Kill a common industry myth, naive assumption, or state a sharp technical tension.
- *"Every agent demo looks brilliant when it runs on a toy script. The moment you give it real production traffic, auth tokens that expire, and flaky network calls, the magic turns into an expensive infinite loop."*
- *"Most agent architectures treat user interfaces as an afterthought: a big block of markdown dumped into a chat bubble. But real users don't want to chat with an invoice."*

---

## 5. Problem Setup (2-4 Short Paragraphs)
Establish why this problem matters right now. Ground it in firsthand collective credibility from the Google Cloud engineering team:
- *"We spent the last few months dogfooding multi-agent loops across our internal systems before rolling this out."*
- *"Here is what we learned after putting thousands of automated tasks through the harness."*
Name what broke and why the existing conventional wisdom fails.

---

## 6. Byline (Mid-Intro)
Placed immediately after the problem setup, bolded:
**By Alan Blount (@zeroasterisk)**

---

## 7. Preview List
The N items with one line of gloss each, giving the reader a complete roadmap of the architectural argument before diving into details.

---

## 8. The N Sections
Each section must follow this exact sequence:
1. **Heading = Opinionated Full-Sentence Lesson:**
   - Prefer: `## Loops get broken with reminders, not blocks` or `## Kill the context, keep the workspace`
   - Avoid generic labels like `## Pattern 2: The Loop`
2. **Reader's Pain (Second Person):**
   - *"If you have built an agent, you have probably run into this: your client logs swear the agent received the updated parameters, but your backend traces show..."*
3. **Why It Happens (Root Cause):**
   - Explain the mechanical failure in plain, precise technical terms.
4. **What We Did (The Architectural Fix):**
   - The specific pattern, data model, or protocol abstraction used to solve it.
5. **Proof of Depth (Un-Fakeable Specifics):**
   - Exact error codes, named protocol fields, token counts, or race condition edge cases from Alan's source material.
6. **Muted Muppet Touch:**
   - A subtle parenthetical aside `(...)` acknowledging messy engineering reality.
7. **Diagram:**
   - Inline hand-drawn dark-mode diagram visualizing the data flow or failure boundary.
8. **How to Steal It:**
   - Hand the reader a concrete, sized takeaway: *"You can build this in an afternoon with about thirty lines of code. Start by flipping your write order..."*

---

## 9. Synthesis Beat (Outranking the List)
A single higher-order architectural insight that elevates the piece beyond a simple listicle:
- *"These patterns are not mutually exclusive. They compose."*
- *"Eval and observability turn out to be the exact same loop sampled from two directions: over the test cases you wrote, and over the production conversations you didn't."*
- *"A good interface does not try to guess what the user wants. It renders what the agent knows and gets out of the way."*

---

## 10. "Get Started Today" / "Verify It Yourself" (CTA)
A concrete, runnable next step that matches the subject:
- **Google Cloud / ADK Product:** A runnable CLI command, a documentation link with clean UTM tracking, and a memorable builder kicker:
  - *"Your agent doesn't need to be perfect. It just needs to fail predictably and be measurable. High-fives are earned in production, not in slide decks."*
- **OSS / Industry Trend:** A command to clone the repo, run a test harness, and verify the claim in fifteen minutes:
  - *"Start with the one pattern that solves a headache you already have today."*

---

## 11. Series Cross-Link
Position the article as part of an ongoing conversation:
*"If you found this breakdown useful, check out our previous piece on [Previous Article Title]. Follow @GoogleCloudTech and @zeroasterisk for more deep dives from the builder trenches."*
