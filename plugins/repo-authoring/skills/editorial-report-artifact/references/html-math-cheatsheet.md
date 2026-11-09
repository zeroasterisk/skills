# Zero-CDN HTML Mathematical Typography Cheatsheet

## Why Offline Semantic HTML Math Beats CDN Scripts

Standalone HTML experiment records are frequently opened directly via `file://`, attached to emails or patent disclosures, or viewed in air-gapped environments where external CDNs (`KaTeX`, `MathJax`) are blocked or cause layout shift.

When an agent synthesizes content from Markdown `.md` files into `.html`, the #1 failure mode is **Markdown-to-HTML bleed**: raw `$...$` LaTeX macros (`\tilde{H}_m`, `\ln|\mathcal{V}_m|`, `\implies`, `\ge`, `\tau`) or inline Markdown backticks (`` `code` ``) left unparsed inside HTML paragraphs.

**Mandate**: Always style inline formulas with `<span class="math">...</span>` and display equations inside `<pre class="code">...` using Unicode combining marks, `<i>`, `<sub>`, `<sup>`, and HTML entities.

## CSS Rule for `.math`

```css
.math {
  font-family: "STIX Two Math", "Cambria Math", "Times New Roman", Georgia, serif;
  font-size: 1.03em;
  white-space: nowrap;
  color: var(--slate);
}
.math i { font-style: italic; }
.math sub { font-size: 0.76em; vertical-align: -0.18em; }
.math sup { font-size: 0.76em; vertical-align: 0.35em; }
```

## LaTeX-to-HTML Lookup Table

| LaTeX Expression | Offline Semantic HTML (`.math`) | Visual Output |
| :--- | :--- | :--- |
| `$\tilde{H}_m$` | `<span class="math"><i>H&#771;</i><sub><i>m</i></sub></span>` | *H̃*<sub>*m*</sub> |
| `$\tilde{H}_m = H_m / \ln\|\mathcal{V}_m\|$` | `<span class="math"><i>H&#771;</i><sub><i>m</i></sub> = <i>H</i><sub><i>m</i></sub> / ln\|<i>V</i><sub><i>m</i></sub>\|</span>` | *H̃*<sub>*m*</sub> = *H*<sub>*m*</sub> / ln\|*V*<sub>*m*</sub>\| |
| `$\hat{y}_m$` | `<span class="math"><i>y&#770;</i><sub><i>m</i></sub></span>` | *ŷ*<sub>*m*</sub> |
| `$p_{m,k}$` | `<span class="math"><i>p</i><sub><i>m,k</i></sub></span>` | *p*<sub>*m,k*</sub> |
| `$z_{m,k}$` | `<span class="math"><i>z</i><sub><i>m,k</i></sub></span>` | *z*<sub>*m,k*</sub> |
| `$\|\mathcal{V}_m\| = K_m$` | `<span class="math">\|<i>V</i><sub><i>m</i></sub>\| = <i>K</i><sub><i>m</i></sub></span>` | \|*V*<sub>*m*</sub>\| = *K*<sub>*m*</sub> |
| `$\tau = 0.16$` | `<span class="math">&tau; = 0.16</span>` | τ = 0.16 |
| `$H_m \ge 0.35\text{ nats}$` | `<span class="math"><i>H</i><sub><i>m</i></sub> &ge; 0.35 nats</span>` | *H*<sub>*m*</sub> ≥ 0.35 nats |
| `$\tilde{H}_m < 0.160$` | `<span class="math"><i>H&#771;</i><sub><i>m</i></sub> &lt; 0.160</span>` | *H̃*<sub>*m*</sub> < 0.160 |
| `$\in [0, 1]$` | `<span class="math">&in; [0, 1]</span>` | ∈ [0, 1] |
| `$\implies$` | `<span class="math">&rArr;</span>` | ⇒ |
| `$\to$` | `<span class="math">&rarr;</span>` | → |
| `$O(1)$` / `$O(L)$` | `<span class="math"><i>O</i>(1)</span>` / `<span class="math"><i>O</i>(<i>L</i>)</span>` | *O*(1) / *O*(*L*) |
| `$\mathbb{E}[v] = \sum_k v_k \cdot p_k$` | `<span class="math">E[<i>v</i>] = &Sigma;<sub><i>k</i></sub> <i>v</i><sub><i>k</i></sub> &middot; <i>p</i><sub><i>k</i></sub></span>` | E[*v*] = Σ<sub>*k*</sub> *v*<sub>*k*</sub> · *p*<sub>*k*</sub> |
| `$\Delta H$` | `<span class="math">&Delta;<i>H</i></span>` | Δ*H* |

## Combining Diacritical Marks for Mathematical Accents

- **Tilde (`\tilde{x}`)**: Append `&#771;` (`U+0303`) immediately after the base character inside `<i>`: `<i>H&#771;</i>` → *H̃*
- **Hat (`\hat{x}`)**: Append `&#770;` (`U+0302`) immediately after the base character inside `<i>`: `<i>y&#770;</i>` → *ŷ*
- **Bar / Mean (`\bar{x}`)**: Append `&#772;` (`U+0304`) immediately after the base character inside `<i>`: `<i>x&#772;</i>` → *x̄*
