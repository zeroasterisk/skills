# OPM Tracking (Salesforce Expert Requests)

You have access to the **OPM Tracking** skill for logging customer meetings as Expert Requests in Salesforce Vector Lightning (`vector.lightning.force.com`).

## Key Principles & Defaults
- **Form URL**: `https://vector.lightning.force.com/lightning/o/Expert_Request__c/new`
- **Type of Expertise**: `Other SME Teams`
- **Expert Team**: `Cloud AI OPM (Global)`
- **Solution / Product**: `AI`
- **Engagement Type**: `Customer Meetings`
- **Description / Purpose**: `"Agent Platform"` (or specific meeting context)

## Critical Workflow Steps
1. **Opportunity Resolution**: Select active/open opportunity for customer; avoid Closed Lost and unrelated subsidiaries. Escalate ambiguity to user/sales team.
2. **Form Save**: Submit initial form.
3. **Assign to Me**: Click top action button `Assign to Me` (Owner -> Alan Blount, Status -> Assigned).
4. **Complete Status**: Click `Mark Status as Complete` twice (`Accepted` -> `Completed`).
5. **Workload Dates**: Edit `Request Start Date` and `Request End Date` with meeting date (`M/D/YYYY`) and click Save.

See `SKILL.md` for complete decision tree, edge case handling, and browser automation selectors.
