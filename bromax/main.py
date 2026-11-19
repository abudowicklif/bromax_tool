import asyncio, logging
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from .config import settings
from .deriv import DerivFeed
from .agents import analyse
from .backtest import backtest

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bromax")
ticks = deque(maxlen=settings.max_ticks)
errors = deque(maxlen=100)
clients = set()
feed_status = "starting"
feed_task = None
feed = None
analysis_cache = {}

def on_status(status):
    global feed_status
    feed_status = status

def on_error(message):
    log.warning(message)
    errors.append(message)

def on_tick(record, source):
    # Avoid duplicate latest history/live tick if both channels overlap.
    if record.get("epoch") is not None and any(t.get("epoch") == record["epoch"] for t in list(ticks)[-3:]):
        return
    ticks.append({**record, "source": source})
    analysis_cache.clear()

async def broadcaster():
    while True:
        if clients:
            payload = snapshot()
            dead = []
            for ws in list(clients):
                try:
                    await ws.send_json(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                clients.discard(ws)
        await asyncio.sleep(1)

def snapshot():
    digits = [t["digit"] for t in ticks]
    result = analyse(digits, settings.min_signal_sample)
    return {"status": feed_status, "symbol": settings.symbol,
            "tick_count": len(ticks), "latest_ticks": list(ticks)[-100:],
            "analysis": result, "errors": list(errors)[-10:]}

@asynccontextmanager
async def lifespan(app):
    global feed, feed_task
    feed = DerivFeed(settings.ws_url, settings.symbol, settings.history_count,
                     on_tick, on_status, on_error)
    feed_task = asyncio.create_task(feed.run())
    broadcast_task = asyncio.create_task(broadcaster())
    yield
    feed.stop()
    feed_task.cancel()
    broadcast_task.cancel()
    await asyncio.gather(feed_task, broadcast_task, return_exceptions=True)

app = FastAPI(title="BROMAX TOOL", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent.parent / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return (Path(__file__).resolve().parent.parent / "static" / "index.html").read_text(encoding="utf-8")

@app.get("/api/status")
async def status():
    return snapshot()

@app.get("/api/backtest")
async def get_backtest():
    if len(ticks) < settings.min_signal_sample + 100:
        raise HTTPException(422, f"Need at least {settings.min_signal_sample + 100} ticks for a meaningful backtest.")
    return backtest([t["digit"] for t in ticks], min_train=settings.min_signal_sample)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        await ws.send_json(snapshot())
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        clients.discard(ws)
    except Exception:
        clients.discard(ws)
