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
    mode = os.getenv("APP_MODE", "prod")
    app.state.engine = EngineFactory.getEngine(mode)
    app.state.engine.start()
    print("Engine started in mode:", mode)
    yield
    
    app.state.engine.stop()
    print("Engine stopped.")


app = FastAPI(lifespan=lifespan)

# --- MOUNT THE ROUTER ---
app.include_router(ui_router)




if __name__ == "__main__":
    # This line tells Python: "Don't just read the recipe, START the chef!"
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)