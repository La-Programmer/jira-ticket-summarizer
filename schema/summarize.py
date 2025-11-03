from pydantic import BaseModel, HttpUrl

class SummarizeRequest(BaseModel):
    """
    Request schema for summarization endpoint.
    """
    url: HttpUrl

class SummarizeResponse(BaseModel):
    """
    Response schema containing developer and business summaries.
    """
    developer_summary: str
    business_summary: str
