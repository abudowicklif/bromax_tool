# BROMAX TOOL

A standalone, read-only Deriv Digit MATCH market-data research system. Python + NumPy + Pandas-compatible data structures + SciPy + FastAPI + browser dashboard.

## Safety boundary

BROMAX connects only to Deriv's public, unauthenticated market-data WebSocket endpoint. It never sends `authorize`, account, proposal, buy, sell, balance, or trading requests. There is no trading code. It does not accept or store API tokens. The only market is the configured underlying symbol, and all analytics concern the final quote digit for MATCH research.

## Quick start

Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows; on macOS/Linux use: cp .env.example .env
uvicorn bromax.main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000`. To present from a phone on the same Wi-Fi, open `http://YOUR_COMPUTER_LAN_IP:8000`. Allow inbound TCP port 8000 in the local firewall only on a trusted network.

Set `DERIV_SYMBOL` to a valid Deriv short symbol. `1HZ100V` is the default example; symbols can change availability. The app will show feed/API errors if the symbol is unavailable. Public endpoint: `wss://api.derivws.com/trading/v1/options/ws/public`.

## Architecture

- **Feed adapter**: requests `ticks_history` and subscribes to `ticks`; reconnects with exponential backoff. It only sends public market-data requests.
- **Digit extraction**: uses `quote` plus `pip_size` to normalize decimal precision, then extracts the final displayed digit. Invalid quotes/precision are logged in diagnostics.
- **Frequency agent**: empirical 0–9 frequencies, Pearson chi-square against uniformity, and one-sided per-digit exact binomial tests with Bonferroni adjustment across ten digits.
- **Sequence agent**: run lengths and a 10×10 transition matrix. Every conditional transition is tested against 10% with Bonferroni correction across up to 100 comparisons.
- **Statistical model agent**: Jeffreys Dirichlet categorical posterior with marginal 95% beta credible intervals.
- **Verification agent**: rejects low sample sizes and uncorrected/non-significant patterns. Only a frequency candidate that survives the corrected test and minimum sample gate can become the unconditional digit signal. Sequence findings remain contextual because a conditional transition is not an unconditional next-digit prediction.
- **Backtest**: expanding-window chronological one-step-ahead evaluation. A prediction at index t uses only digits before t. Abstentions are separately reported; hit-rate significance uses an exact one-sided binomial test against 10%.

## Statistical interpretation

A significant goodness-of-fit test says the observed sample is inconsistent with a uniform distribution; it does not establish stable next-tick predictability. Multiple testing is controlled conservatively with Bonferroni. The default minimum sample is 1,000 and can be changed with `MIN_SIGNAL_SAMPLE`.

The posterior intervals quantify uncertainty under a Jeffreys prior and an IID categorical model. They are not frequentist confidence intervals, do not correct for data snooping, and do not protect against non-stationarity. The dashboard deliberately abstains unless the frequency agent has a corrected significant candidate and sufficient sample size. Even then, this is a research flag, not a promise of an exploitable edge. A serious claim of predictive edge requires repeated, independent, pre-registered out-of-sample tests across regimes.

The current implementation does not use a black-box LLM or claim that multiple agents create independent evidence: all agents inspect the same stream, and their tests are correlated. “Multi-agent” means separated analytical responsibilities and an explicit verification gate.

## API

- `GET /` dashboard
- `GET /api/status` current ticks, diagnostics, and analysis
- `GET /api/backtest` walk-forward test on the in-memory tick buffer
- `WS /ws` live dashboard updates

## Tests

```bash
pytest -q
```

## Operational notes

- Data is held in memory only and disappears on restart.
- `MAX_TICKS` controls memory retention; `HISTORY_COUNT` controls requested initial history.
- The current history parser requires a `pip_size` field on the history response. If Deriv omits it, history is explicitly not digitized rather than guessing. Live tick responses are precision-aware.
- Production deployment should add TLS/reverse proxy, process supervision, persistent audit storage, metrics/alerting, rate-limit awareness, and longer-running shadow validation. Do not expose the dashboard publicly without access controls.
- This is a research tool, not financial advice or a trading recommendation.

## Deriv documentation

- [Public WebSocket endpoint](https://developers.deriv.com/docs/options/ws-public/)
- [Ticks stream](https://developers.deriv.com/docs/data/ticks/)
- [Ticks history](https://developers.deriv.com/docs/data/ticks-history/)
