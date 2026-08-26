# Good AI List REST API & Taxonomy Reference

Good AI List (`goodailist.com`) is a daily-updated registry tracking 19,500+ open-source AI repositories, 200,000+ developers, and ecosystem growth metrics.

---

## 1. REST Endpoints

Base URL: `https://goodailist.com`

### `GET /api/repos`
Search, filter, and paginate AI repositories.

* **Query Parameters:**
  * `search` (*string*): Substring search across repository name, description, and keywords.
  * `category` (*string*): Single category or comma-separated list.
  * `subcategory` (*string*): Specific subcategory.
  * `keyword` (*string*): Specific keyword tag.
  * `country` (*string*): Geographic filter.
  * `is_new` (*string*): Pass `"1"` to filter repositories newly added today.
  * `sort_by` (*string*):
    * `star_1d` (Daily star gain — default for velocity)
    * `star_1d_pct` (% daily star surge)
    * `star_7d` (7-day star gain)
    * `star_7d_pct` (% weekly star surge)
    * `stars` (Total all-time stars)
    * `forks` (Total forks)
    * `contributors` (Contributor count)
    * `created_at` / `updated_at`
  * `sort_order` (*string*): `"desc"` (default) or `"asc"`.
  * `page` (*integer*): 1-based page index.
  * `limit` (*integer*): Results per page (default: 100 on web, 15-20 on CLI).

* **Repository Object Schema:**
  ```json
  {
    "repo": "owner/repo-name",
    "description": "Text summary",
    "stars": 172177,
    "forks": 18572,
    "star_1d": 6394,
    "star_1d_pct": 3.85,
    "star_7d": 12500,
    "star_7d_pct": 7.8,
    "category": "AI Engineering",
    "subcat": "Build agent workflow (SDK),Build agent workflow (visual)",
    "keywords": "Agent-ready APIs, Automation, Tool use",
    "country": "China",
    "top_devs": "alice, bob, charlie",
    "contributors": 27,
    "created_at": "2026-08-13",
    "updated_at": "2026-08-20",
    "first_seen": "2026-08-14",
    "is_new": false,
    "language": "TypeScript",
    "archived": false
  }
  ```

---

### `GET /api/devs`
Discover and rank AI developers and maintainers.

* **Query Parameters:**
  * `search` (*string*): GitHub username or full name search.
  * `country` (*string*): Country name (e.g. `"USA"`, `"France"`).
  * `city` (*string*): City name (e.g. `"San Francisco"`, `"Paris"`).
  * `min_repos` (*integer*): Minimum indexed repository threshold.
  * `sort_by` (*string*): `weighted_contributions` (default), `contributions`, `repos`.
  * `sort_order` (*string*): `"desc"` or `"asc"`.
  * `page` & `limit` (*integer*).

---

### `GET /api/bots`
Track bot accounts and automated infrastructure across AI repositories.

* **Query Parameters:** `search`, `page`, `limit`.

---

### `GET /api/summary`
Ecosystem counts: `total_repos`, `total_devs`, `total_stars`, `updated_at`.

---

### `GET /api/repos/filters`
Enumerate valid filter terms:
* `categories`: Top-level groupings.
* `subcategories`: Detailed workflow & architecture groupings.
* `countries`: All mapped countries.
* `keywords`: Tagged capabilities.

---

## 2. Category & Subcategory Taxonomy

### Category: `AI Engineering`
* `Build agent workflow (SDK)` — Open-source agent orchestration SDKs (e.g. LangChain, AutoGen, ADK).
* `Build agent workflow (visual)` — Flow/node visual builders.
* `Build agent UI` — Generative UI, artifact viewers, agent chat widgets.
* `Bring agent to users` — Integrations, desktop overlays, browser extensions.
* `Give agent tools` — MCP servers, tool collections, integrations.
* `Prompt & Scaffold` — Prompt engineers, templates, starter kits.
* `Agent-ready APIs` — Fast structured inference gateways.
* `AIE roadmap` — Agentic AI architectural taxonomies and roadmaps.

### Category: `Models`
* `Audio/Speech models` — Text-to-speech, transcription, voice agents.
* `Image & Vision models` — Generative diffusion, vision encoders.
* `Multimodal models` — Unified vision-language-audio models.
* `Reasoning & Small LLMs` — Distilled, quantized, SLMs.

### Category: `Model Development`
* `Fine-tuning & LoRA` — Unsloth, Axolotl, PEFT.
* `Evaluation & Benchmarks` — LLM-as-a-judge, SWE-bench suites.
* `Dataset generation & synthetic data` — Distillation pipelines.

### Category: `Infrastructure`
* `Inference servers` — vLLM, Ollama, SGLang, TensorRT-LLM.
* `Vector DBs & Embeddings` — Search & retrieval backends.
* `Agent Runtime & Sandboxes` — Secure execution microVMs.
