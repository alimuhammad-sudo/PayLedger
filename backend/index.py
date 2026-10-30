"""Entry point for hosting (Vercel's Python runtime looks for `app` here).

Locally: uvicorn app.main:create_app --factory --reload
"""

from app.main import create_app

app = create_app()
