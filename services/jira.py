import os
import re
from typing import Any, Dict, Optional
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup

JIRA_BASE = os.getenv("JIRA_BASE_URL", "https://justinoghenekomeebedi.atlassian.net")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_KEY")


def extract_issue_key(url_or_key: str) -> Optional[str]:
    """Accept browse URL, REST URL, or plain key and return the issue key."""
    m = re.search(r"/browse/([A-Z0-9]+-[0-9]+)", url_or_key)
    if m:
        return m.group(1)
    m = re.search(r"/issue/([A-Z0-9]+-[0-9]+)", url_or_key)
    if m:
        return m.group(1)
    if re.match(r"^[A-Z0-9]+-[0-9]+$", url_or_key):
        return url_or_key
    return None


def _storage_to_text(node: Any) -> str:
    """
    Convert Atlassian 'storage' JSON structure (the new editor format) into plain text.
    This recurses into 'content' nodes and extracts 'text' fields.
    It's intentionally simple: collects text nodes and preserves basic spacing.
    """
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        text_parts = []
        # If a direct text node
        if "text" in node and isinstance(node["text"], str):
            text_parts.append(node["text"])
        # Recurse into 'content' if present
        if "content" in node and isinstance(node["content"], list):
            for child in node["content"]:
                text_parts.append(_storage_to_text(child))
        return " ".join(p for p in (p.strip() for p in text_parts) if p)
    if isinstance(node, list):
        return " ".join(_storage_to_text(item) for item in node)
    return ""


def _html_to_text(html: str) -> str:
    """Strip HTML to plain text using BeautifulSoup."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    # Remove scripts/styles
    for tag in soup(["script", "style"]):
        tag.decompose()
    # Get textual content and collapse whitespace
    text = soup.get_text(separator="\n")
    # Normalize whitespace: collapse multiple newlines/spaces
    text = re.sub(r"\n\s*\n+", "\n\n", text)  # keep paragraph breaks
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _comment_body_to_text(comment: Dict[str, Any]) -> str:
    """
    Convert a comment body's possible shapes to text.
    Jira comments may contain:
      - 'renderedBody' (HTML),
      - 'body' as a string,
      - 'body' as storage JSON (dict with 'content').
    """
    # 1) renderedBody (preferred)
    if comment.get("renderedBody"):
        return _html_to_text(comment["renderedBody"])

    # 2) body as plain string
    body = comment.get("body")
    if isinstance(body, str):
        return body.strip()

    # 3) body as Atlassian storage format (dict)
    if isinstance(body, dict):
        # Sometimes the storage is nested under 'content' etc.
        text = _storage_to_text(body)
        if text:
            return text

    # 4) older style: comment['body'] might be dict with 'versioned' or markup
    # fallback: try to find any textual values in nested structures
    def _walk_and_collect_text(obj):
        if obj is None:
            return []
        if isinstance(obj, str):
            return [obj]
        if isinstance(obj, dict):
            results = []
            for v in obj.values():
                results += _walk_and_collect_text(v)
            return results
        if isinstance(obj, list):
            results = []
            for x in obj:
                results += _walk_and_collect_text(x)
            return results
        return []

    fallback_text = " ".join(_walk_and_collect_text(body))[:4000]
    return fallback_text.strip()


def get_issue_raw(issue_key_or_url: str) -> Dict[str, Any]:
    """
    Fetch the issue JSON from Jira API (fields: summary, description, attachment, comment).
    Returns raw JSON dict.
    """
    issue_key = extract_issue_key(issue_key_or_url)

    print("Issue key: ", issue_key)
    if not issue_key:
        raise ValueError("Could not extract issue key from input. Provide /browse/KEY, /issue/KEY or KEY.")

    if not (JIRA_EMAIL and JIRA_API_TOKEN):
        raise EnvironmentError("Set JIRA_EMAIL and JIRA_API_KEY environment variables (.env)")

    api_url = f"{JIRA_BASE}/rest/api/3/issue/{issue_key}"
    # Request only required fields for efficiency, and ask for renderedFields to get HTML
    params = {
        "fields": "summary,description,attachment,comment,reporter,priority,created,updated",
        "expand": "renderedFields",
    }
    resp = requests.get(api_url, auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN),
                        headers={"Accept": "application/json"}, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def normalize_issue(issue_json: Dict[str, Any], max_comments: int = 10) -> Dict[str, Any]:
    """
    Reduce the Jira issue JSON to the fields you need:
    - summary
    - description_text (plain text)
    - attachments: list of {filename, url, size}
    - last_comments: list of up to `max_comments` with {author, created, body}
    - reporter, priority, created
    """
    fields = issue_json.get("fields", {})

    # 1) Summary
    summary = fields.get("summary") or ""

    # 2) Description: prefer renderedFields.description (HTML) -> then fields.description (storage or string)
    description_text = ""
    rendered = issue_json.get("renderedFields") or {}
    if rendered.get("description"):
        description_text = _html_to_text(rendered["description"])
    else:
        desc = fields.get("description")
        if isinstance(desc, str):
            description_text = desc.strip()
        elif isinstance(desc, dict):
            description_text = _storage_to_text(desc).strip()

    # 3) Attachments: collect filename, content/URL, size if present
    attachments = []
    for a in fields.get("attachment", []) or []:
        attachments.append({
            "filename": a.get("filename"),
            "content": a.get("content"),   # URL to download (requires auth)
            "size": a.get("size"),
            "mimeType": a.get("mimeType")
        })

    # 4) Comments: Jira stores comments under fields.comment.comments as a list (chronological)
    comments_block = fields.get("comment") or {}
    comments = comments_block.get("comments", []) if isinstance(comments_block, dict) else []
    # Keep last N comments (most recent)
    last_comments = comments[-max_comments:] if comments else []

    # Normalize each comment to simple dict
    normalized_comments = []
    for c in last_comments:
        author = c.get("author", {}) or {}
        normalized_comments.append({
            "id": c.get("id"),
            "author_displayName": author.get("displayName"),
            "author_accountId": author.get("accountId"),
            "created": c.get("created"),
            "body": _comment_body_to_text(c)
        })

    # Make sure comments are ordered oldest -> newest (slice above preserves order)
    result = {
        "issue_key": issue_json.get("key"),
        "summary": summary,
        "description_text": description_text,
        "attachments": attachments,
        "last_comments": normalized_comments,
        "reporter": {
            "displayName": (fields.get("reporter") or {}).get("displayName"),
            "accountId": (fields.get("reporter") or {}).get("accountId"),
        },
        "priority": (fields.get("priority") or {}).get("name"),
        "created": fields.get("created"),
        "updated": fields.get("updated"),
    }
    return result


def get_issue_summary(issue_key_or_url: str, max_comments: int = 10) -> Dict[str, Any]:
    """High-level helper: fetch raw JSON, then normalize and return minimal data."""
    raw = get_issue_raw(issue_key_or_url)
    return normalize_issue(raw, max_comments=max_comments)
