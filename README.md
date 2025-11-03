# Jira Ticket Summarizer

This FastAPI application provides a `/summarize` endpoint that accepts a Jira ticket URL and returns two summaries:
one tailored for developers and one for business analysts. It uses Selenium to scrape the ticket content and an abstracted LLM interface for generating summaries.

## Project Structure

    main.py
    app/routers/summarize.py
    schemas/summarize.py
    services/scraper.py
    services/summarizer.py
    utils/text_cleaning.py
    requirements.txt
    README.md

## Setup and Installation

1. Clone the repository.
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
