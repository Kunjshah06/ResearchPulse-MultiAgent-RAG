"""
PaperMind AI — Application Entry Point
Run with: python main.py  or  uvicorn main:app --reload
"""
import uvicorn

from papermind.core.config.settings import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "papermind.api.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        workers=1 if settings.app.debug else settings.app.workers,
        log_level=settings.logging.level.lower(),
    )
