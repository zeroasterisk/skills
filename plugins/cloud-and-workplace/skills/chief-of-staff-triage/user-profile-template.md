# User Profile: [Your Name]

This profile configures the `chief-of-staff-triage` skill. Customize the tables and rules below to define how the agent should prioritize your inbox, chat, and calendar.

---

## 1. Project Taxonomy & Priority Weights

Define the projects you are currently tracking. The agent will use the weights to calculate triage scores.

| Project Name | Priority (High/Medium/Low) | Weight (%) | Keywords / Context |
| :--- | :--- | :--- | :--- |
| **[Project Alpha]** | High | 40% | e.g., "AI UI", "Frontend" |
| **[Project Beta]** | Medium | 20% | e.g., "API Integration" |
| **[Project Gamma]** | Low | 5% | e.g., "Legacy Maintenance" |

---

## 2. Key People & Relationships

Define the individuals whose communications should be prioritized.

| Name | Email / LDAP | Priority (Critical/High/Medium) | Role / Context |
| :--- | :--- | :--- | :--- |
| **[Manager Name]** | `manager@example.com` | Critical | Your direct manager |
| **[Key Collaborator]** | `peer@example.com` | High | Co-lead on Project Alpha |
| **[Partner Lead]** | `partner@example.com` | Medium | External stakeholder |

---

## 3. Custom Triage Scoring Rules

Define specific rules for the agent to follow when scoring:

*   **Rule 1:** Elevate any direct message (DM) or @mention from anyone marked as **Critical** in the Key People list (Score +50).
*   **Rule 2:** Boost threads containing keywords related to **High** priority projects (Score +30).
*   **Rule 3:** Automatically demote automated calendar invites or newsletters (Score -20).
*   **Rule 4:** [Add your own rule here, e.g., "Highlight any thread mentioning 'Production Blocker'"].

---

## 4. Leader → Assistant / Admin Map

If you coordinate meetings with busy leaders, list them and their assistants here. The agent will recommend routing scheduling logistics through the assistant.

| Leader Name | Assistant Name / LDAP | Chat Space / DM Link | Notes |
| :--- | :--- | :--- | :--- |
| **[Leader Name]** | `assistant@example.com` | [Link] | Route all 1:1 scheduling here |
