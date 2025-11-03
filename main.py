# main.py
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from routers.summarize import router as summarize_router

# Load environment variables from .env file
load_dotenv()

# Optional: richer Markdown description shown in Swagger UI
DESCRIPTION = """
Jira Ticket Summarizer API
--------------------------

Send a Jira ticket URL to `/api/summarize` and receive two concise human-readable
summaries (Developer and Business Analyst). The service:
- Scrapes the Jira ticket using Selenium
- Cleans and normalizes the text
- Sends the content to an LLM (provider-agnostic) to generate summaries

**Notes**
- Ensure Chrome/ChromeDriver is available in the runtime environment.
- Configure LLM credentials via environment variables (e.g. `OPENAI_API_KEY`) if integrating an LLM provider.
"""

# OpenAPI tags metadata (helps organize endpoints in Swagger UI)
OPENAPI_TAGS = [
    {
        "name": "Summarize",
        "description": "Endpoints for scraping Jira tickets and generating human summaries."
    }
]

app = FastAPI(
    title="Jira Ticket Summarizer",
    description=DESCRIPTION,
    version="1.0.0",
    contact={
        "name": "Your Team",
        "email": "devops@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=OPENAPI_TAGS,
    # You can customize the URLs for docs/openapi if needed:
    openapi_url="/openapi.json",
    docs_url="/swagger",    # Swagger UI
    redoc_url="/redoc",  # ReDoc UI
    # Swagger UI tweaks: keep models collapsed and persist auth between reloads
    swagger_ui_parameters={
        "docExpansion": "none",
        "defaultModelsExpandDepth": -1,
        "persistAuthorization": True
    },
)

# Include the router from the summarize module under a versioned prefix
# and tag it so it appears under the "Summarize" section in Swagger UI.
app.include_router(summarize_router, prefix="/api", tags=["Summarize"])

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
