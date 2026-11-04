# Paperline

Live demo: https://aditya2375.github.io/paperline/

Source: https://github.com/Aditya2375/paperline

A paper-only crossover laboratory. Public hourly candles become an inspectable chart and causal fill ledger. No exchange account, API key, balance endpoint or order routing exists in this project.

## What runs

- Static browser app with BTC-USD / ETH-USD public Coinbase candles, SMA controls, fee and slippage assumptions, paper equity, drawdown, position and CSV ledger.
- Python reference ledger and a Pandas rolling-indicator cross-check.
- Rules: fast SMA crossing above slow SMA schedules a long entry; crossing below schedules an exit. Start flat with $10,000, long-only, all available cash, fractional units, no leverage.
- A signal uses candle i's close. A fill uses candle i+1's open. The signal column records the *start of the signal candle*, not the moment its close became available. Pending final signals are not filled without a next closed bar.
- Fees: percentage of fill notional. Buy units include the fee in the cash budget. Buy slippage raises price; sell slippage lowers it. Final liquidation equity subtracts hypothetical exit costs on an open position; drawdown is based on mark-to-market equity before those final costs.

## Data and operational boundaries

The Coinbase documentation describes up to 300 candles, but the observed default response on 2026-11-04 returned 350. The parser allows a bounded 1,000-row response, validates it, sorts and deduplicates timestamps, excludes open candles, then takes the newest 300 closed candles. Missing hourly intervals stop the run instead of silently changing the strategy clock. No fabricated fallback or bundled market replay is shown as live.

Initial fetch is explicit. Auto-refresh is opt-in, once per hour, only while the tab is visible. Manual requests have a one-minute guard, including after failures and market switches. Requests time out after 12 seconds. A failed refresh keeps the previous snapshot explicitly stale. The window is recomputed each time; there is no durable running brokerage ledger or account history. This is historical paper replay on recent public data, not real-time execution.

A small recent window is not evidence of profitability. No out-of-sample test, liquidity/partial-fill model, latency model, funding, taxes, shorting or exchange order execution. Fees and slippage are assumptions, not a verified exchange fee schedule. This is educational software, not investment advice.

The data provider sees the visitor's IP and requested pair. There is no analytics, credential storage, external font or third-party executable script.

## Verification

`node tests/test_core.mjs` checks Python/JavaScript ledger parity, one-bar causal fills, prefix invariance/no future dependence, fee/slippage effects, open-bar exclusion, invalid parameters, gaps and source ordering. `pandas_reference.py` independently computes rolling indicators and checks execution-side/time parity.

`python pandas_reference.py --input candles.json --as-of UNIX_SECONDS` uses public Coinbase candle JSON. The Python parser does not fetch or trade. Runtime browser errors and unavailable data are reported rather than replaced with invented performance.

## Sources

- Coinbase public candle schema and incomplete-interval caveat: https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles
- Public endpoint rate limits: https://docs.cdp.coinbase.com/exchange/introduction/rate-limits-overview
