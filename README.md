
## Setup

```bash
pip install -r requirements.txt
```

Run the server:

```bash
python app.py
```

Browse to http://127.0.0.1:5000 in your browser.

## Configuration

The app fetches live quotes from the Yahoo Finance API.  You can customise
which symbols to display by setting the `STOCK_SYMBOLS` environment variable
with a comma-separated list (e.g. `AAPL,MSFT,GOOGL`).  If you don't set it a
sensible default list is used.

In environments without network access the fetch may fail.  In that case the
server will attempt the following fallback sources *in order*:

1. An in-memory cache of the last successful fetch (survives until the
   application restarts).
2. A local stock data file specified by the `STOCK_DATA_FILE` environment
   variable.  The file may be JSON or CSV; format details are in
   `app.py`'s documentation string.
3. If neither cache nor file contain data, the APIs return an empty response
   and the front end displays a message noting the lack of live data.

To run with a pre-populated file you might do:

```bash
export STOCK_DATA_FILE=./prices.json   # or prices.csv
export STOCK_SYMBOLS=AAPL,TSLA,MSFT    # optional
python app.py
```

This lets you supply accurate prices even when the machine is offline.
