from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from backend.API.routes import router
import uvicorn

app = FastAPI()

templates = Jinja2Templates(directory="frontend/templates")

# --- THE DATA BRIDGE ---
# We attach a dictionary to the app state so 'routes.py' can see it.
app.state.latest_traffic = {
    "app": "WAITING...", 
    "confidence": 0.0,
    "metadata": {"packets": 0}
}

# --- MOUNT THE ROUTER ---
app.include_router(router, prefix="/api/v1")

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """
    This is the 'Root' route. 
    When you go to http://127.0.0.1:8000, this function runs.
    """
    # templates.TemplateResponse finds index.html in your frontend/templates folder
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    # This line tells Python: "Don't just read the recipe, START the chef!"
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)