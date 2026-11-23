# Inline SVG Architecture & Interactive Explorer Patterns

## 1. SVG Hygiene Rules

1. **Responsive ViewBox**: Always set `viewBox="0 0 940 205"` (for horizontal schematics) or `viewBox="0 0 640 360"` (for interactive pipeline graphs) with `style="width:100%;height:auto;display:block"`.
2. **XML Entity Escaping**: Inside `<svg><text>...</text></svg>`, raw `<` or `&` breaks XML parsing and truncates the diagram. Always escape:
   - `<` → `&lt;`
   - `>` → `&gt;`
   - `&` → `&amp;`
3. **Monospace Font Stack**: Wrap text groups in `<g font-family="ui-monospace, Menlo, monospace" font-size="11.5">` so text metrics remain consistent across macOS, Linux, and Windows without clipping rounded rectangles (`rx="8"`).

## 2. Reusable Horizontal System Schematic Pattern

```html
<svg viewBox="0 0 940 205" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block">
  <defs>
    <marker id="arr1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#87867F"/>
    </marker>
  </defs>
  <g font-family="ui-monospace, Menlo, monospace" font-size="11.5">
    <!-- Stage 1 Input Box (Slate) -->
    <rect x="12" y="45" width="215" height="105" rx="8" fill="#141413"/>
    <text x="119" y="70" text-anchor="middle" fill="#FAF9F5" font-weight="600">[INPUT / PREFIX]</text>
    <text x="119" y="92" text-anchor="middle" fill="#C9B98A" font-size="10">Policy Schema + Context</text>

    <!-- Stage 2 Core Mechanism (Paper + Clay Stroke) -->
    <rect x="260" y="24" width="220" height="148" rx="8" fill="#FFFFFF" stroke="#D97757" stroke-width="1.8"/>
    <text x="370" y="46" text-anchor="middle" font-weight="600" fill="#8A3B1E">[CORE READOUT]</text>

    <!-- Stage 3 Gate (Sand + Border) -->
    <rect x="518" y="45" width="188" height="105" rx="8" fill="#F0EEE6" stroke="#D1CFC5" stroke-width="1.5"/>
    <text x="612" y="72" text-anchor="middle" font-weight="600">H̃_m = H_m / ln|V_m|</text>
    <text x="612" y="95" text-anchor="middle" fill="#4B5C39" font-size="10.5">H̃_m &lt; 0.16 → Early Exit</text>
    <text x="612" y="118" text-anchor="middle" fill="#8A3B1E" font-size="10.5">H̃_m &gt;= 0.16 → Escalate</text>

    <!-- Branch Outcomes -->
    <rect x="742" y="22" width="184" height="64" rx="8" fill="rgba(120,140,93,0.14)" stroke="#788C5D" stroke-width="1.5"/>
    <text x="834" y="48" text-anchor="middle" font-weight="600" fill="#4B5C39">Tier-1 Fast Path</text>

    <rect x="742" y="106" width="184" height="68" rx="8" fill="rgba(217,119,87,0.12)" stroke="#D97757" stroke-width="1.5"/>
    <text x="834" y="132" text-anchor="middle" font-weight="600" fill="#8A3B1E">Tier-2 Escalation</text>
  </g>
  <g stroke="#87867F" stroke-width="1.5" fill="none" marker-end="url(#arr1)">
    <path d="M227 98 L258 98"/>
    <path d="M480 98 L516 98"/>
    <path d="M706 75 L740 54"/>
    <path d="M706 125 L740 140"/>
  </g>
</svg>
```

## 3. Interactive Pipeline Explorer Wiring (`.explorer` + `nodeData`)

Pair an SVG containing `.gnode[data-node="..."]` groups with a sticky `<aside class="inspector">` and a lightweight vanilla JS listener:

```javascript
const nodeData = {
  n1: {
    tag: "STAGE 1 · PASS-1 READOUT",
    title: "Bidirectional Diffusion Canvas (O(1))",
    body: "Single-step restricted-softmax readout across all masked slots simultaneously.",
    kv: [
      ["latency", "712 ms mean wall clock"],
      ["early-exit", "66.0% of suite (33/50) at 100% precision"],
      ["receipt", "benchmarks/results_calibration_cloudrun.json"]
    ],
    code: "./bin/dgem bench-calibration --workers 4"
  }
};

document.querySelectorAll('.gnode').forEach(node => {
  node.addEventListener('click', () => {
    document.querySelectorAll('.gnode').forEach(n => n.classList.remove('active'));
    node.classList.add('active');
    const d = nodeData[node.dataset.node];
    if (!d) return;
    document.getElementById('ins-tag').textContent = d.tag;
    document.getElementById('ins-title').textContent = d.title;
    document.getElementById('ins-body').textContent = d.body;
    document.getElementById('ins-kv').innerHTML = d.kv
      .map(([k, v]) => `<div class="k">${k}</div><div class="v">${v}</div>`)
      .join('');
    document.getElementById('ins-code').textContent = d.code;
  });
});
```
