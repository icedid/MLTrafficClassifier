from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from frontend.frontendroutes import router as ui_router
from backend.EngineFactory import EngineFactory
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    mode = os.getenv("APP_MODE", "test")
    app.state.engine = EngineFactory.create_engine("test")
    app.state.engine.start()
    print("Engine started in mode:", mode)
    yield
    
    app.state.engine.stop()
    print("Engine stopped.")

app = FastAPI()


# --- THE DATA BRIDGE ---
# We attach a dictionary to the app state so 'routes.py' can see it.
app.state.latest_traffic = {
    "app": "WAITING...", 
    "confidence": 0.0,
    "metadata": {"packets": 0}
}

# --- MOUNT THE ROUTER ---
app.include_router(ui_router)




if __name__ == "__main__":
    # This line tells Python: "Don't just read the recipe, START the chef!"
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)