# services/summarizer_langchain_async.py
import json
from typing import Any, Dict, Tuple, Optional
from langchain_core.prompts import PromptTemplate
from enums.summarizer_prompts import SummarizerPromptsEnum
from factories.llm_factory import get_llm


def _build_ticket_brief(ticket_details: Dict[str, Any]) -> Dict[str, str]:
    """Create a compact textual representation of the ticket for the prompt."""
    key = ticket_details.get("issue_key") or ticket_details.get("key") or ""
    summary = ticket_details.get("summary", "") or ""
    description = ticket_details.get("description_text", "") or ticket_details.get("description", "") or ""
    comments = ticket_details.get("last_comments", []) or ticket_details.get("comments", []) or []

    comment_lines = []
    for c in comments:
        created = c.get("created", "") or c.get("date", "")
        author = c.get("author_displayName") or (c.get("author") or {}).get("displayName") or ""
        body = (c.get("body") or "")[:400].replace("\n", " ")
        comment_lines.append(f"- {created} | {author}: {body}")
    comments_text = "\n".join(comment_lines) if comment_lines else "None"

    ticket_brief = {
        "key": key,
        "summary": summary.strip(),
        "description": description.strip(),
        "last_comments": comments_text
    }
    return ticket_brief


async def summarize_with_langchain_async(
    ticket_details: Dict[str, Any],
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> Tuple[str, str]:
    """
    Async version: generate (developer_summary, business_summary) using LangChain async calls.

    Args:
        ticket_details: normalized dict from get_issue_summary(...)
        provider: optional provider override (e.g., "openai")
        model: optional model name override
        temperature: optional temperature override

    Returns:
        (developer_summary, business_summary)
    """
    # Instantiate LLM from factory. The LangChain LLM must support async .arun() calls.
    # get_llm should return an LLM instance compatible with LangChain's async interface.
    llm = get_llm(provider=provider, model=model, temperature=(temperature if temperature is not None else None))

    # Prepare prompt templates and LLM chains
    dev_template = PromptTemplate(template=SummarizerPromptsEnum.DEV_PROMPT, input_variables=["ticket"])
    ba_template = PromptTemplate(template=SummarizerPromptsEnum.BA_PROMPT, input_variables=["ticket"])


    # Build compact ticket representation
    ticket_brief = _build_ticket_brief(ticket_details)
    ticket_str = json.dumps(ticket_brief, ensure_ascii=False, indent=2)

    try:
        dev_prompt = dev_template.format(ticket=ticket_str)
        ba_prompt = ba_template.format(ticket=ticket_str)
    except Exception:
        # Fallback: append ticket at the end
        dev_prompt = f"{dev_template}\n\n{ticket_str}"
        ba_prompt = f"{ba_template}\n\n{ticket_str}"

    # Run chains asynchronously using arun (LangChain async)
    # Note: Some LLM wrappers require async initialization; using get_llm as above should be fine for OpenAI.
    developer_out = await llm.ainvoke(dev_prompt)
    business_out = await llm.ainvoke(ba_prompt)

    return developer_out.text, business_out.text
