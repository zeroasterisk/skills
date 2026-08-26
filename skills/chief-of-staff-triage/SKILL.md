---
name: chief-of-staff-triage
description: >-
  Triages the user's unread Chat, Email, and Calendar into an actionable "pay attention vs. ignore" digest.
  Uses a local user profile (~/.config/agent/user-profile.md) to personalize prioritization weights,
  key collaborators, and projects. If the profile is missing, the agent will guide the user to create one.
---

# Chief-of-Staff Triage

Goal: Cut down high inbound communication volume into a short, ranked list of what to act on, what to skim, and what to ignore across Chat, Email, and Calendar.

## 1. Onboarding & Bootstrapping (First Run)

Before performing the triage, the agent **MUST** check for the existence of the local user profile:

*   **Primary Path:** `references/user-profile.md` (relative to this skill)
*   **Fallback Path:** `~/.config/agent/user-profile.md`

### If the profile is missing:
1.  Stop the triage.
2.  Inform the user that the Chief-of-Staff skill requires a personalized profile to score items accurately.
3.  Present the `user-profile-template.md` to the user.
4.  Offer to guide them through a quick 3-minute interview in the chat to bootstrap the file for them, or instruct them to create the file manually.
5.  **Do not proceed** with triaging until the profile is created.

---

## 2. Triage Workflow

Once the profile is verified:

1.  **Load the Profile:** Read the project weights, key people, and custom scoring adjustments from the local profile.
2.  **Gather Chat Context:** Retrieve recent unread Chat messages/threads using available Chat APIs or CLIs.
3.  **Gather Email Context:** Retrieve unread emails (e.g., `is:unread`) from the last 3 days.
4.  **Gather Calendar Context:** Retrieve upcoming calendar events for the next 7 days.
5.  **Score and Group:** Apply the scoring criteria below using the weights defined in the user's profile.
6.  **Generate Digest:** Present the categorized and cross-referenced digest.

---

## 3. Dynamic Scoring Engine

Apply a score to each inbound item (Chat, Email, Calendar Invite) based on the local profile:

### Positive Signals (Elevate Priority)
*   **Direct Asks:** Thread contains a direct question to the user, @mention, or explicit request for action/decision/approval.
*   **Key People:** Sender or participants match the "Key People" list in the profile (apply the corresponding weight).
*   **Core Projects:** Thread matches keywords of "High" or "Medium" priority projects in the profile (apply the project weight).
*   **Leadership/Urgency:** Contains indicators of exec pings or tight deadlines.
*   **Recent Engagement:** The user has recently participated in the thread (indicates active interest). *Note: If the user posted last and there is no subsequent ask, treat as FYI/handled.*

### Negative Signals (Deprioritize)
*   **Broadcasts:** Automated notifications, newsletters, system alerts, or large group/community space updates.
*   **Unrelated Projects:** Projects marked as "Low" priority or not listed.
*   **Cold Inbounds:** Unsolicited requests from external orgs or people not in the key contacts list.

---

## 4. Output Buckets

Group and present the triage results in three clear buckets:

1.  **🔴 ACT NOW:** Directed asks, blockers, urgent decisions, key people pings, and pending calendar RSVPs.
2.  **🟡 REVIEW:** Skim-worthy project updates, FYIs from key collaborators, and relevant industry/internal news.
3.  **⚪ IGNORE/FYI:** Automated alerts, newsletters, and general community chatter.

*Cross-reference:* If an email, chat thread, and calendar event share a topic, group them together under a single item.

---

## 5. Calendar RSVP Auditing

When asked to review the calendar:
1.  List all upcoming meetings with status `needsAction` or `tentative`.
2.  Compare them against the high-priority projects and key people in the profile.
3.  Recommend changing RSVP to **No** for large-group meetings with no active role, or conflicts with high-priority tasks.
4.  Present a recommendation table: `Event Name`, `Organizer`, `Current RSVP`, `Recommended RSVP`, `Reasoning`.
5.  **Do not write RSVPs** without explicit user approval.
