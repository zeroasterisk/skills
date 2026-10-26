#!/usr/bin/env python3
import os
import subprocess

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", os.path.join(os.getcwd(), "assets"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

COMMON_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700&family=Inter:wght@500;600;700;800&family=JetBrains+Mono:wght@600;700&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  width: 1920px;
  height: 1080px;
  background-color: #faf6ed;
  background-image:
    linear-gradient(to right, #e6dfd1 1.5px, transparent 1.5px),
    linear-gradient(to bottom, #e6dfd1 1.5px, transparent 1.5px);
  background-size: 48px 48px;
  color: #18181b;
  font-family: 'Inter', -apple-system, sans-serif;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 68px 88px 56px 88px;
}

.slide-header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: #18181b;
  color: #faf6ed;
  font-family: 'JetBrains Mono', monospace;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  padding: 10px 22px;
  border-radius: 999px;
  box-shadow: 4px 4px 0px #c9bfa8;
}

.headline {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 64px;
  font-weight: 700;
  color: #18181b;
  letter-spacing: -1.2px;
  line-height: 1.08;
}

.headline .accent-blue {
  background: #d0d7f3;
  padding: 2px 18px;
  border-radius: 14px;
  border: 3px solid #18181b;
  display: inline-block;
}

.headline .accent-green {
  background: #c8ead3;
  padding: 2px 18px;
  border-radius: 14px;
  border: 3px solid #18181b;
  display: inline-block;
}

.headline .accent-amber {
  background: #fde68a;
  padding: 2px 18px;
  border-radius: 14px;
  border: 3px solid #18181b;
  display: inline-block;
}

.headline .accent-red {
  background: #fecaca;
  padding: 2px 18px;
  border-radius: 14px;
  border: 3px solid #18181b;
  display: inline-block;
}

.card {
  background: #ffffff;
  border: 4px solid #18181b;
  border-radius: 28px;
  box-shadow: 10px 10px 0px #18181b;
  padding: 44px;
  display: flex;
  flex-direction: column;
  position: relative;
}

.card-red { background: #fff5f5; }
.card-green { background: #f2fbf5; }
.card-blue { background: #f3f6fc; }
.card-amber { background: #fffbeb; }

.tag-pill {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 22px;
  font-weight: 700;
  padding: 10px 22px;
  border-radius: 14px;
  border: 3px solid #18181b;
  width: fit-content;
}

.pill-red { background: #fecaca; color: #7f1d1d; }
.pill-green { background: #bbf7d0; color: #14532d; }
.pill-blue { background: #c7d2fe; color: #1e3a8a; }
.pill-amber { background: #fde68a; color: #78350f; }
.pill-dark { background: #18181b; color: #ffffff; }

.slide-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 3px solid #d6cebf;
  padding-top: 22px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 22px;
  font-weight: 600;
  color: #52525b;
}

.footer-note {
  background: #f2d6b3;
  color: #18181b;
  padding: 8px 20px;
  border-radius: 12px;
  border: 2.5px solid #18181b;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 22px;
}
"""

# SLIDE 0: HERO CO-SCALING MATRIX
slide_0 = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
__COMMON_CSS__
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 110px 1fr;
  align-items: stretch;
  height: 640px;
  margin: 16px 0;
}
.vs-col {
  display: flex;
  align-items: center;
  justify-content: center;
}
.vs-circle {
  width: 84px;
  height: 84px;
  border-radius: 50%;
  background: #fde68a;
  border: 4px solid #18181b;
  box-shadow: 5px 5px 0px #18181b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 32px;
  font-weight: 700;
}
.card-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 46px;
  font-weight: 700;
  margin-top: 22px;
  margin-bottom: 14px;
}
.card-sub {
  font-size: 26px;
  color: #3f3f46;
  font-weight: 600;
  margin-bottom: 34px;
}
.stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: auto;
}
.step-row {
  background: #ffffff;
  border: 3px solid #18181b;
  border-radius: 18px;
  padding: 20px 26px;
  font-size: 28px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 4px 4px 0px #18181b;
}
.step-row span.mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 22px;
  padding: 6px 14px;
  border-radius: 10px;
  border: 2px solid #18181b;
}
</style></head><body>
  <div class="slide-header">
    <div class="eyebrow">DEFENSIVE CO-SCALING · AGENT GATEWAY</div>
    <div class="headline">Polite Prompts Don't Scale. <span class="accent-green">Gateways Do.</span></div>
  </div>

  <div class="grid-2">
    <div class="card card-red">
      <div class="tag-pill pill-red">❌ PROMPT-ONLY GUARDRAILS</div>
      <div class="card-title">Gentle Suggestions</div>
      <div class="card-sub">"Do not approve unauthorized fees."</div>
      <div class="stack">
        <div class="step-row">
          <span>1. Shared admin@ credentials</span>
          <span class="mono" style="background:#fecaca;">BLIND</span>
        </div>
        <div class="step-row">
          <span>2. Urgent supplier panic hits</span>
          <span class="mono" style="background:#fecaca;">BYPASSED</span>
        </div>
        <div class="step-row" style="background:#fecaca;">
          <span>💥 Agent rationalizes breaking rule</span>
          <span class="mono" style="background:#ffffff;">FAIL</span>
        </div>
      </div>
    </div>

    <div class="vs-col">
      <div class="vs-circle">VS</div>
    </div>

    <div class="card card-green">
      <div class="tag-pill pill-green">✅ DEFENSIVE CO-SCALING</div>
      <div class="card-title">Two-Layer Network Defense</div>
      <div class="card-sub">Enforced at the Agent Gateway boundary.</div>
      <div class="stack">
        <div class="step-row">
          <span>0. Identity (SPIFFE + mTLS + DPoP)</span>
          <span class="mono" style="background:#c7d2fe;">AUTHN</span>
        </div>
        <div class="step-row">
          <span>1. Deterministic CEL Math</span>
          <span class="mono" style="background:#bbf7d0;">&lt; 0.5ms</span>
        </div>
        <div class="step-row" style="background:#bbf7d0;">
          <span>2. Airlocked Intent Policy (SGP)</span>
          <span class="mono" style="background:#ffffff;">TEMP 0</span>
        </div>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <div class="footer-note">💡 Rule #1: Never rely on one LLM prompt to police another LLM.</div>
    <div>@GoogleCloudTech · @zeroasterisk</div>
  </div>
</body></html>
"""

# SLIDE 1: CRYPTOGRAPHIC IDENTITY PERIMETER
slide_1 = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
__COMMON_CSS__
.rows-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
  height: 640px;
  justify-content: center;
}
.lane {
  border: 4px solid #18181b;
  border-radius: 28px;
  padding: 36px 44px;
  box-shadow: 10px 10px 0px #18181b;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.lane-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.lane-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 38px;
  font-weight: 700;
}
.flow-nodes {
  display: grid;
  grid-template-columns: 1fr 80px 1.2fr 80px 1.1fr;
  align-items: center;
}
.node-box {
  background: #ffffff;
  border: 3.5px solid #18181b;
  border-radius: 20px;
  padding: 24px 28px;
  box-shadow: 5px 5px 0px #18181b;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.node-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 30px;
  font-weight: 700;
}
.node-code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 20px;
  color: #3f3f46;
  background: #f4f4f5;
  padding: 6px 12px;
  border-radius: 8px;
  border: 2px solid #d4d4d8;
  width: fit-content;
}
.arrow-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 46px;
  font-weight: 800;
}
</style></head><body>
  <div class="slide-header">
    <div class="eyebrow">1 · AUTHENTICATED IDENTITY (AUTHN BEFORE AUTHZ)</div>
    <div class="headline">Stop Sharing <span class="accent-red">Ambient Service Accounts</span></div>
  </div>

  <div class="rows-container">
    <div class="lane card-red">
      <div class="lane-header">
        <div class="lane-title">❌ The Hobbyist Trap: Shared Credentials</div>
        <div class="tag-pill pill-red">ZERO ATTRIBUTION</div>
      </div>
      <div class="flow-nodes">
        <div class="node-box">
          <div class="node-title">🤖 50 Agent Loops</div>
          <div class="node-code">Untrusted Runtime</div>
        </div>
        <div class="arrow-cell">➔</div>
        <div class="node-box" style="background:#fecaca;">
          <div class="node-title">🔑 One Shared Key</div>
          <div class="node-code">admin@corp.iam...</div>
        </div>
        <div class="arrow-cell">➔</div>
        <div class="node-box">
          <div class="node-title">😱 "Dave from Accounting"</div>
          <div class="node-code">Blamed for 5,000 queries</div>
        </div>
      </div>
    </div>

    <div class="lane card-green">
      <div class="lane-header">
        <div class="lane-title">✅ Agent Gateway: Cryptographic Identity per Agent</div>
        <div class="tag-pill pill-green">VERIFIED AT WIRE</div>
      </div>
      <div class="flow-nodes">
        <div class="node-box">
          <div class="node-title">🪪 Workload Identity</div>
          <div class="node-code">spiffe://.../procurement-agent</div>
        </div>
        <div class="arrow-cell">➔</div>
        <div class="node-box" style="background:#c7d2fe;">
          <div class="node-title">🔒 mTLS + DPoP Proof</div>
          <div class="node-code">Sender-Bound Token (No Replay)</div>
        </div>
        <div class="arrow-cell">➔</div>
        <div class="node-box" style="background:#bbf7d0;">
          <div class="node-title">🛡️ Agent Gateway</div>
          <div class="node-code">Caller Proven Before AuthZ</div>
        </div>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <div class="footer-note">🔐 If you can't prove WHO is calling, you can't enforce WHAT they touch.</div>
    <div>@GoogleCloudTech · @zeroasterisk</div>
  </div>
</body></html>
"""

# SLIDE 2: LAYER 1 DETERMINISTIC BEDROCK (CEL)
slide_2 = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
__COMMON_CSS__
.pipeline {
  display: grid;
  grid-template-columns: 1fr 90px 1.25fr 90px 1fr;
  align-items: center;
  height: 640px;
}
.stage-card {
  height: 540px;
  justify-content: space-between;
}
.big-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 40px;
  font-weight: 700;
  margin-top: 14px;
}
.code-pill-box {
  background: #18181b;
  color: #f8fafc;
  font-family: 'JetBrains Mono', monospace;
  font-size: 22px;
  padding: 24px;
  border-radius: 20px;
  line-height: 1.55;
  border: 3px solid #18181b;
}
.check-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.check-item {
  background: #ffffff;
  border: 3.5px solid #18181b;
  border-radius: 16px;
  padding: 18px 22px;
  font-size: 26px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 4px 4px 0px #18181b;
}
.outcome-stack {
  display: flex;
  flex-direction: column;
  gap: 28px;
  height: 540px;
}
.outcome-card {
  flex: 1;
  border: 4px solid #18181b;
  border-radius: 26px;
  padding: 32px;
  box-shadow: 8px 8px 0px #18181b;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
}
.arrow-big {
  font-size: 56px;
  font-weight: 800;
  text-align: center;
}
</style></head><body>
  <div class="slide-header">
    <div class="eyebrow">2 · LAYER 1 AUTHORIZATION (DETERMINISTIC BEDROCK)</div>
    <div class="headline">Wire-Speed Math in Envoy <span class="accent-blue">(&lt; 0.5ms CEL)</span></div>
  </div>

  <div class="pipeline">
    <div class="card stage-card">
      <div>
        <div class="tag-pill pill-dark">INBOUND CALL</div>
        <div class="big-title">Agent Tool Request</div>
      </div>
      <div class="code-pill-box">
        tool: "issue_po"<br>
        vendor: 8492<br>
        amount: $88,500<br>
        contract: "MC-401"
      </div>
      <div style="font-size:22px; font-weight:600; color:#52525b;">
        Intercepted before ERP allocates a thread.
      </div>
    </div>

    <div class="arrow-big">➔</div>

    <div class="card card-blue stage-card">
      <div>
        <div class="tag-pill pill-blue">⚡ ENVOY + CEL ENGINE</div>
        <div class="big-title">Hard Math Boundaries</div>
      </div>
      <div class="check-list">
        <div class="check-item">✅ Caller == procurement-agent</div>
        <div class="check-item">✅ Tool in Allowlist</div>
        <div class="check-item">✅ Amount &lt;= $100,000 Cap</div>
      </div>
      <div style="font-family:'JetBrains Mono',monospace; font-size:21px; font-weight:700; color:#1e3a8a;">
        0 Hallucinations · 0 Prompt Injection
      </div>
    </div>

    <div class="arrow-big">➔</div>

    <div class="outcome-stack">
      <div class="outcome-card card-red">
        <div class="tag-pill pill-red">🚫 OVER $100K / WRONG API</div>
        <div style="font-family:'Space Grotesk',sans-serif; font-size:34px; font-weight:700;">Dropped at Proxy</div>
        <div style="font-size:22px; font-weight:600; color:#7f1d1d;">Instant 403 Forbidden in &lt; 0.5ms</div>
      </div>
      <div class="outcome-card card-green">
        <div class="tag-pill pill-green">✅ UNDER $100K CAP</div>
        <div style="font-family:'Space Grotesk',sans-serif; font-size:34px; font-weight:700;">Pass to Layer 2</div>
        <div style="font-size:22px; font-weight:600; color:#14532d;">Proceeds to Semantic Intent Check</div>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <div class="footer-note">📐 CEL is your floor: fast, deterministic, and immune to smooth talk.</div>
    <div>@GoogleCloudTech · @zeroasterisk</div>
  </div>
</body></html>
"""

# SLIDE 3: THE SEMANTIC EXPLOITATION GAP
slide_3 = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
__COMMON_CSS__
.three-cols {
  display: grid;
  grid-template-columns: 1.1fr 70px 1fr 70px 1.1fr;
  align-items: stretch;
  height: 630px;
  margin: 12px 0;
}
.col-card {
  justify-content: space-between;
}
.col-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 38px;
  font-weight: 700;
  margin-top: 18px;
}
.quote-bubble {
  background: #ffffff;
  border: 3.5px solid #18181b;
  border-radius: 22px;
  padding: 26px;
  font-size: 26px;
  font-weight: 600;
  line-height: 1.45;
  box-shadow: 5px 5px 0px #18181b;
}
.highlight-red {
  background: #fecaca;
  padding: 2px 10px;
  border-radius: 8px;
  font-weight: 800;
}
.math-box {
  background: #ffffff;
  border: 3.5px solid #18181b;
  border-radius: 22px;
  padding: 28px;
  text-align: center;
  box-shadow: 5px 5px 0px #18181b;
}
.math-eq {
  font-family: 'JetBrains Mono', monospace;
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 12px;
}
.arrow-mid {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 52px;
  font-weight: 800;
}
</style></head><body>
  <div class="slide-header">
    <div class="eyebrow">3 · THE INTENT GAP (DEEPMIND OVEREAGERNESS TRAP)</div>
    <div class="headline">Why Static Math <span class="accent-amber">Misses Human Intent</span></div>
  </div>

  <div class="three-cols">
    <div class="card card-amber col-card">
      <div>
        <div class="tag-pill pill-amber">1. URGENT VENDOR QUOTE</div>
        <div class="col-title">Authority Spoofing</div>
      </div>
      <div class="quote-bubble">
        "Factory line stops Friday!<br><br>
        $50k parts + <span class="highlight-red">$38.5k freight</span><br><br>
        <span class="highlight-red">Verbally approved</span> by Director Vance!"
      </div>
      <div style="font-size:22px; font-weight:700; color:#78350f;">
        77% unverified surcharge hidden in free text.
      </div>
    </div>

    <div class="arrow-mid">➔</div>

    <div class="card card-blue col-card">
      <div>
        <div class="tag-pill pill-blue">2. STATIC CEL CHECK</div>
        <div class="col-title">Math Sees Valid JSON</div>
      </div>
      <div class="math-box">
        <div class="math-eq" style="font-size:28px; white-space:nowrap;">$88,500 &lt;= $100,000</div>
        <div style="font-size:22px; font-weight:700; color:#15803d; white-space:nowrap;">✓ Valid Schema · ✓ Under Cap</div>
      </div>
      <div style="font-size:22px; font-weight:700; color:#1e3a8a;">
        CEL only checks numbers, never the excuse.
      </div>
    </div>

    <div class="arrow-mid">➔</div>

    <div class="card card-red col-card">
      <div>
        <div class="tag-pill pill-red">3. OVEREAGER AGENT</div>
        <div class="col-title">Goal-Seeking Panic</div>
      </div>
      <div class="quote-bubble" style="background:#fecaca;">
        🤖 <i>"Must prevent factory shutdown! Issuing $88,500 Purchase Order now."</i>
      </div>
      <div class="tag-pill pill-dark" style="width:100%; justify-content:center; font-size:24px;">
        💸 $38,500 UNAUTHORIZED LOSS
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <div class="footer-note">⚠️ DeepMind (arXiv:2605.30322): Agents break rules out of overeagerness, not malice.</div>
    <div>@GoogleCloudTech · @zeroasterisk</div>
  </div>
</body></html>
"""

# SLIDE 4: LAYER 2 AIRLOCKED POLICY EVALUATOR (SGP)
slide_4 = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
__COMMON_CSS__
.sgp-grid {
  display: grid;
  grid-template-columns: 0.95fr 80px 1.25fr 80px 1.15fr;
  align-items: center;
  height: 640px;
}
.panel-card {
  height: 550px;
  justify-content: space-between;
}
.panel-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 38px;
  font-weight: 700;
  margin-top: 14px;
}
.nlc-card {
  background: #ffffff;
  border: 3.5px solid #18181b;
  border-radius: 20px;
  padding: 24px;
  font-size: 25px;
  font-weight: 700;
  line-height: 1.45;
  box-shadow: 5px 5px 0px #18181b;
}
.input-chip {
  background: #f4f4f5;
  border: 2.5px solid #18181b;
  border-radius: 14px;
  padding: 14px 18px;
  font-size: 23px;
  font-weight: 700;
}
.split-right {
  display: flex;
  flex-direction: column;
  gap: 26px;
  height: 550px;
}
.branch-box {
  flex: 1;
  border: 4px solid #18181b;
  border-radius: 26px;
  padding: 28px 32px;
  box-shadow: 8px 8px 0px #18181b;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
}
.arrow-col {
  font-size: 54px;
  font-weight: 800;
  text-align: center;
}
</style></head><body>
  <div class="slide-header">
    <div class="eyebrow">4 · LAYER 2 SEMANTIC GOVERNANCE POLICY (SGP)</div>
    <div class="headline">The Airlocked <span class="accent-green">Policy Evaluator</span></div>
  </div>

  <div class="sgp-grid">
    <div class="card panel-card">
      <div>
        <div class="tag-pill pill-dark">ISOLATED INPUTS</div>
        <div class="panel-title">Strict Airlock</div>
      </div>
      <div style="display:flex; flex-direction:column; gap:14px;">
        <div class="input-chip">📦 Proposed $88.5k Call</div>
        <div class="input-chip">📜 Natural Language Policy</div>
        <div class="input-chip" style="background:#fecaca; color:#7f1d1d;">🚫 Zero Agent Scratchpad</div>
      </div>
      <div style="font-size:21px; font-weight:700; color:#52525b;">
        Agent cannot talk the judge into bending rules.
      </div>
    </div>

    <div class="arrow-col">➔</div>

    <div class="card card-green panel-card">
      <div>
        <div class="tag-pill pill-green">🔒 TEMP 0 POLICY MODEL</div>
        <div class="panel-title">Natural Language Rule</div>
      </div>
      <div class="nlc-card">
        "Surcharges &gt; 15% require cryptographic Director sign-off.<br><br>
        <span style="background:#fecaca; padding:2px 8px; border-radius:6px;">Never approve verbal claims.</span>"
      </div>
      <div class="tag-pill pill-red" style="width:100%; justify-content:center; font-size:24px;">
        🛑 VERDICT: DENY (77% FEE)
      </div>
    </div>

    <div class="arrow-col">➔</div>

    <div class="split-right">
      <div class="branch-box card-green">
        <div class="tag-pill pill-green">✅ AUTO-REMEDIATION</div>
        <div style="font-family:'Space Grotesk',sans-serif; font-size:34px; font-weight:700;">Issue $50k Base PO</div>
        <div style="font-size:23px; font-weight:600; color:#14532d;">Secures 10,000 parts at catalog price</div>
      </div>
      <div class="branch-box card-amber">
        <div class="tag-pill pill-amber">👤 HUMAN ESCALATION</div>
        <div style="font-family:'Space Grotesk',sans-serif; font-size:34px; font-weight:700;">Route $38.5k to Director</div>
        <div style="font-size:23px; font-weight:600; color:#78350f;">Waits for real cryptographic sign-off</div>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <div class="footer-note">🎯 Calibrate in DRY_RUN shadow mode for 7 days before flipping ENFORCE.</div>
    <div>@GoogleCloudTech · @zeroasterisk</div>
  </div>
</body></html>
"""

slides = [
    ("hero-coscaling-matrix", slide_0),
    ("diagram-1-cryptographic-perimeter", slide_1),
    ("diagram-2-deterministic-bedrock", slide_2),
    ("diagram-3-semantic-gap", slide_3),
    ("diagram-4-airlocked-evaluator", slide_4),
]

for name, html_content in slides:
    html_content = html_content.replace("__COMMON_CSS__", COMMON_CSS)
    html_path = os.path.join(OUTPUT_DIR, f"{name}.html")
    png_path = os.path.join(OUTPUT_DIR, f"{name}.png")
    with open(html_path, "w") as f:
        f.write(html_content)
    cmd = [
        "google-chrome",
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--window-size=1920,1080",
        "--default-background-color=00000000",
        f"--screenshot={png_path}",
        f"file://{html_path}"
    ]
    subprocess.run(cmd, check=True)
    print(f"Rendered {png_path}")
