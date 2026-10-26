# Humanizer — Remove AI Writing Patterns

Rewrite AI-generated or AI-sounding prose so it reads naturally and authentically while strictly preserving meaning, claims, citations, and factual accuracy.

Based on Wikipedia's ["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (maintained by WikiProject AI Cleanup) and portable across agent environments.

## When to Use

- Editing or reviewing drafts, blog posts, documentation, PR descriptions, emails, executive summaries, or customer escalations for AI tells.
- Eliminating buzzwords, inflated claims, sales hyperbole, repetitive structures, unnecessary bolding/emojis, and chatbot artifacts.
- Refining prose to match a specific human writer's voice without adding or losing factual claims.

## Core Rules

1. **Keep Every Claim:** Never drop facts, names, dates, numbers, quotes, or citations. Preserve the core information even when restructuring or condensing.
2. **Never Invent Details:** Do not hallucinate or add facts, background, or citations not in the source text.
3. **Match the Voice:** Analyze the user's sample writing if provided (sentence rhythm, vocabulary, punctuation) or adopt an appropriate neutral/engaging register.
4. **Remove the 35 AI Patterns:** Systematically detect and fix patterns across Content, Language, Style, and Chatbot categories.

## The 35 Anti-Patterns at a Glance

| Category | Patterns & Tells |
|---|---|
| **Content** | 1. Inflated importance/legacy (`stands as`, `pivotal moment`, `enduring testament`)<br>2. Name-dropping without context<br>3. Shallow `-ing` clauses (`highlighting...`, `ensuring...`)<br>4. Sales/marketing hyperbole (`nestled`, `vibrant`, `groundbreaking`)<br>5. Vague sources (`Industry reports`, `Experts argue`)<br>6. Formulaic challenges/outlook sections |
| **Language** | 7. High-frequency AI words (`delve`, `tapestry`, `underscore`, `crucial`, `interplay`, `foster`)<br>8. Avoiding *is* / *are* / *has* (`serves as`, `boasts`)<br>9. "Not only X, but Y" and clipped negative endings<br>10. Forced groups of three<br>11. Synonym cycling & repetitive sentence openers<br>12. False "from X to Y" ranges<br>13. Passive voice & dropped subjects |
| **Style** | 14. Em dashes (—) and en dashes (–) unless present in human sample<br>15. Gratuitous bold text<br>16. Lists with bold mini-headings on every bullet<br>17. Title case in standard section headings<br>18. Emoji decoration (🚀, 💡, ✅)<br>19. Curly quotation marks where straight quotes are standard |
| **Chatbot & Filler** | 20. Leftover conversational artifacts (`I hope this helps!`, `Certainly!`)<br>21. Knowledge-limit disclaimers and speculative guesses<br>22. Overly agreeable sycophancy (`Great question! You're absolutely right`)<br>23. Wordy filler (`in order to`, `due to the fact that`, `at this point in time`)<br>24. Stacked qualifiers & excessive hedging<br>25. Generic optimistic wrap-ups<br>26. Over-hyphenation of compound phrases<br>27. Faux-profound truths (`at its core`, `the real question is`)<br>28. Stage-announcing next points (`Let's dive in`, `Here's what you need to know`)<br>29. Restating section heading in the first sentence<br>30. Documenting past implementation rather than current behavior<br>31. Dramatic staccato fragments & forced punchlines<br>32. Formulaic aphorisms (`X is the currency of Y`)<br>33. Fake-candid openers (`Honestly?`, `Look, here's the thing`)<br>34. Defensive denials against unraised objections (`This isn't to say...`)<br>35. Fabricating and instantly rejecting strawman alternatives |

## Output Modes

- **Pasted Text:** Return flagged patterns found + natural rewritten text.
- **File Mode:** Overwrite or update file directly with natural prose; keep code, metadata, tables, and links intact.
- **Embedded Mode:** For commit messages, PRs, or docs, output clean, humanized text directly without meta-commentary.

See [SKILL.md](SKILL.md) for full examples, before/after pairs, and detailed explanations.
