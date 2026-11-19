from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    ws_url: str = os.getenv("DERIV_WS_URL", "wss://api.derivws.com/trading/v1/options/ws/public")
    symbol: str = os.getenv("DERIV_SYMBOL", "1HZ100V")
    history_count: int = int(os.getenv("HISTORY_COUNT", "5000"))
    max_ticks: int = int(os.getenv("MAX_TICKS", "20000"))
    min_signal_sample: int = int(os.getenv("MIN_SIGNAL_SAMPLE", "1000"))
    reconnect_min_seconds: float = 1.0
    reconnect_max_seconds: float = 30.0

settings = Settings()
