#!/usr/bin/env python3
"""OPM Tracking Automation Utility for Salesforce Expert Requests.

This script provides structured models and automation workflows for creating
and completing Expert Requests in Salesforce Vector Lightning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class CustomerMeetingEntry:
    """Represents a customer meeting event to track in Salesforce."""
    customer_name: str
    meeting_date: date
    opportunity_name_override: Optional[str] = None
    description: str = "Agent Platform"
    type_of_expertise: str = "Other SME Teams"
    expert_team: str = "Cloud AI OPM (Global)"
    solution_product: str = "AI"
    engagement_type: str = "Customer Meetings"

    # Generated upon creation
    expert_request_id: Optional[str] = None
    status: str = "Pending"
    resolved_opportunity: Optional[str] = None
    notes: List[str] = field(default_factory=list)


def validate_opportunity_candidate(candidate_title: str) -> tuple[bool, str]:
    """Evaluates an opportunity candidate string from Salesforce search results.

    Returns:
        (is_valid, reason): True if valid open candidate, False if invalid.
    """
    lower = candidate_title.lower()

    if "closed lost" in lower or "closed-lost" in lower:
        return False, "Opportunity is Closed Lost (Salesforce will block submission)"

    unrelated_keywords = ["applebee", "pineapple", "british airways", "appleton oil"]
    for keyword in unrelated_keywords:
        if keyword in lower:
            return False, f"Matches unrelated company/brand: {keyword}"

    return True, "Valid candidate"


def rank_opportunity_candidates(
    candidates: List[str], target_customer: str
) -> List[tuple[int, str]]:
    """Ranks opportunity candidates based on relevance to Cloud AI OPM.

    Score ranking:
      100+: Specific Agent Assist / Agent Platform / Cloud AI match
      50+:  Active Enterprise renewal / core account
      10+:  Other open opportunity
      <0:   Invalid or rejected
    """
    ranked = []
    for cand in candidates:
        is_valid, reason = validate_opportunity_candidate(cand)
        if not is_valid:
            continue

        lower = cand.lower()
        score = 10
        if any(term in lower for term in ["agent assist", "agent platform", "cloud ai", "generative ai"]):
            score += 100
        elif any(term in lower for term in ["renewal", "enterprise", "cloud"]):
            score += 50

        # Penalize niche unrelated subsidiaries if possible
        if any(term in lower for term in ["wellness", "claris"]):
            score -= 20

        ranked.append((score, cand))

    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked


if __name__ == "__main__":
    sample_candidates = [
        "Apple Inc. -- Online Retail, Agent Assist",
        "Apple Inc - sales.claris.com - 2026 Q4 renewal",
        "Apple Inc -- Broadcom (Closed Lost)",
        "Applebee's - Opportunity 123",
        "Apple Inc - test-acwellness.com - 500 demo licenses",
    ]

    print("Ranking sample candidates for 'Apple':")
    ranked = rank_opportunity_candidates(sample_candidates, "Apple")
    for score, cand in ranked:
        print(f"  [Score: {score:3d}] {cand}")
