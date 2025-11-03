from enum import Enum
import textwrap


class SummarizerPromptsEnum(str, Enum):
    DEV_PROMPT = textwrap.dedent("""
    You are a Lead Product Manager writing a concise technical summary for a software engineer.
    Given the Jira ticket data below, produce a short (max 120 words) Developer Summary that includes:
    - The core technical problem or behavior
    - The expected behavior after a fix
    - Concrete next steps for the engineer (3 short actionable items)

    Ticket data (JSON-like):
    {ticket}

    Developer Summary:
    """).strip()

    BA_PROMPT = textwrap.dedent("""
    You are a Lead Product Manager writing a short business-facing summary for a Business Analyst or stakeholder.
    Given the Jira ticket data below, produce a short (max 120 words) Business Analyst Summary that includes:
    - User/business impact
    - Expected outcome once fixed
    - Any dependencies or decision points

    Ticket data (JSON-like):
    {ticket}

    Business Analyst Summary:
    """).strip()