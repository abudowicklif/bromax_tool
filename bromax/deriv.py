import asyncio, json, logging, random
import websockets
from .digits import tick_to_record, MalformedTick

log = logging.getLogger("bromax.deriv")

class DerivFeed:
    def __init__(self, url, symbol, history_count, on_tick, on_status, on_error):
        self.url, self.symbol, self.history_count = url, symbol, history_count
        self.on_tick, self.on_status, self.on_error = on_tick, on_status, on_error
        self.running = False

    async def _session(self):
        async with websockets.connect(self.url, ping_interval=20, ping_timeout=20,
                                      close_timeout=5, max_size=2**20) as ws:
            self.on_status("connected")
            # Public endpoint only: no authorize message is ever sent.
            await ws.send(json.dumps({"ticks_history": self.symbol, "count": self.history_count,
                                      "end": "latest", "style": "ticks", "req_id": 1}))
            history_loaded = False
            await ws.send(json.dumps({"ticks": self.symbol, "subscribe": 1, "req_id": 2}))
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                    if msg.get("error"):
                        self.on_error(f"Deriv API error: {msg['error'].get('message', msg['error'])}")
                        continue
                    if msg.get("msg_type") == "history" and not history_loaded:
                        prices = msg.get("history", {}).get("prices", [])
                        times = msg.get("history", {}).get("times", [])
                        pip = msg.get("pip_size")
                        if pip is None:
                            # History response can omit pip_size; use tick stream metadata
                            # where available. Do not guess precision.
                            self.on_error("History response omitted pip_size; history not digitized.")
                        else:
                            for i, price in enumerate(prices):
                                try:
                                    rec = tick_to_record({"tick": {"quote": price, "pip_size": pip,
                                        "epoch": times[i] if i < len(times) else None, "symbol": self.symbol}})
                                    self.on_tick(rec, "history")
                                except (MalformedTick, IndexError) as exc:
                                    self.on_error(f"Malformed history tick: {exc}")
                        history_loaded = True
                    elif msg.get("msg_type") == "tick":
                        try:
                            self.on_tick(tick_to_record(msg), "live")
                        except MalformedTick as exc:
                            self.on_error(f"Malformed live tick: {exc}")
                except (json.JSONDecodeError, TypeError) as exc:
                    self.on_error(f"Malformed WebSocket message: {exc}")

    async def run(self):
        self.running = True
        delay = 1.0
        while self.running:
            try:
                await self._session()
                delay = 1.0
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.on_error(f"Feed disconnected: {exc}")
                self.on_status("reconnecting")
                await asyncio.sleep(delay + random.random() * 0.25)
                delay = min(delay * 2, 30.0)
        self.on_status("stopped")

    def stop(self):
        self.running = False
