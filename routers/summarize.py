from fastapi import APIRouter
from enums.llm_provider_enums import LlmProviderEnum
from schema.summarize import SummarizeRequest, SummarizeResponse
from services.jira import get_issue_summary
from services.summarizer import summarize_with_langchain_async
import asyncio

router = APIRouter()

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_endpoint(request: SummarizeRequest):
    """
    Endpoint to summarize a Jira ticket given its URL.
    Returns separate summaries for developers and business analysts.
    """
    print("Incoming request: ", request)
    # try:
    ticket_summary = await asyncio.to_thread(get_issue_summary, str(request.url))
    # Scrape the ticket content (blocking operation) in a separate thread
    # raw_text = await asyncio.to_thread(scrape_ticket, request.url)
    print("Ticket summary: ", ticket_summary)
    # Clean the extracted text
    # cleaned_text = clean_text(raw_text)

    # raise Exception(f'Cleaned text exception: {clean_text}')

    # Generate summaries (blocking operation) in a separate thread
    developer_summary, business_summary = await summarize_with_langchain_async(
        ticket_summary, LlmProviderEnum.GROQ
    )

    # Return the summaries as a JSON response
    return SummarizeResponse(
        developer_summary=developer_summary,
        business_summary=business_summary
    )
    # except Exception as e:
    #     # In production, use proper logging instead of print
    #     raise HTTPException(status_code=500, detail=f"Error processing request: {e}")
