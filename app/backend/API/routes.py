from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# 1. Initialize the Router
router = APIRouter()

# 2. Setup Templates 
# Note: Path is relative to where uvicorn is run (usually the root)
templates = Jinja2Templates(directory="app/templates")

@router.get("/traffic-update", response_class=HTMLResponse)
async def get_traffic_update(request: Request):
    """
    HTMX ENDPOINT: Returns a styled HTML fragment representing the latest 
    network traffic classification.
    """
    # 3. Access the 'Shared Memory' from the app state
    # This allows the API to remain independent of the Engine's internal logic.
    latest_data = getattr(request.app.state, "latest_traffic", {
        "app": "OFFLINE",
        "confidence": 0.0,
        "metadata": {}
    })
    
    # 4. Return the 'Cooked' HTML fragment
    return templates.TemplateResponse(
        "partials/stats_card.html", 
        {
            "request": request, 
            "app_name": latest_data.get("app"),
            "conf": latest_data.get("confidence"),
            "extra": latest_data.get("metadata")
        }
    )

@router.get("/status", response_class=HTMLResponse)
async def get_system_status(request: Request):
    """Example of a second HTMX endpoint for system health."""
    return HTMLResponse(content="<span class='text-green-500'>SYSTEM_READY</span>")