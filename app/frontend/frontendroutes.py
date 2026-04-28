from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="frontend/templates")


@router.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    # This syntax is mandatory for Starlette 1.0.0+
    return templates.TemplateResponse(request=request, name="index.html")

@router.get("/api/v1/label-counts/data")
async def get_label_counts_data(request: Request):
    counts = request.app.state.engine.ReturnLabelcount()
    print(f"[DEBUG] Frontend API (JSON) caught updated counts: {counts}")
    return counts

@router.get("/api/v1/conversations/{label}")
async def get_conversations(label: str, request: Request):
    convs = request.app.state.engine.ReturnConversations(label)
    return convs

@router.get("/api/v1/label-counts", response_class=HTMLResponse)
async def get_label_counts(request: Request):
    counts = request.app.state.engine.ReturnLabelcount()
    print(f"[DEBUG] Frontend API (HTML) rendering counts: {counts}")

    html_output = '<div class="space-y-3">'
    for label, count in counts.items():
        html_output += f"""
        <div class="flex justify-between items-center bg-zinc-800/30 p-2 rounded-lg border border-zinc-800">
            <span class="text-[10px] font-mono text-indigo-400 uppercase tracking-tight">{label}</span>
            <span class="text-xs font-bold text-zinc-100">{count}</span>
        </div>
        """
    html_output += "</div>"
    
    # If no traffic exists yet
    if not counts:
        return '<p class="text-[10px] text-zinc-600 italic">Listening for packets...</p>'
        
    return html_output