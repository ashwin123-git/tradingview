
from flask import Flask, render_template, jsonify
import requests, os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# keep a simple in‑memory cache of the last good quote data.  It's not
# persisted between restarts, but it prevents the UI from immediately losing
# all numbers when an occasional DNS or connectivity glitch occurs.
_stock_cache = {}

def _load_file_data(path):
    """Read stock data from a local JSON or CSV file.

    JSON should map symbol -> {price, change, history}.  CSV should have header
    ``symbol,price,change,history`` where history is semicolon-separated values.
    This allows the app to run in completely offline environments as long as a
    file is provided with accurate quotes.
    """
    import json, csv
    stocks = {}
    try:
        if path.lower().endswith('.json'):
            with open(path, 'r') as f:
                stocks = json.load(f)
        elif path.lower().endswith('.csv'):
            with open(path, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sym = row.get('symbol')
                    if not sym:
                        continue
                    hist = []
                    if row.get('history'):
                        hist = [float(x) for x in row['history'].split(';') if x]
                    stocks[sym.upper()] = {
                        'price': float(row.get('price', 0)),
                        'change': float(row.get('change', 0)),
                        'history': hist,
                    }
    except Exception as e:
        print('error loading stock file', path, e)
    return stocks


def get_stocks():
    """Return current stock information and a string describing the source.

    The return value is a tuple ``(data, source)`` where source is one of
    ``"live"`` (fresh from Yahoo), ``"cache"`` (previous successful fetch),
    ``"file"`` (local STOCK_DATA_FILE or prices.json), or ``"none"`` (empty).

    ``STOCK_SYMBOLS`` still controls which symbols we request when live, but
    it does not affect the cache/file paths: the cache/file may contain any
    symbols and they will be returned in full.
    """

    raw = os.getenv("STOCK_SYMBOLS", "AAPL,TSLA,GOOGL,MSFT,AMZN,FB,BRK-A,JNJ,V,PG,NVDA")
    symbols = [s.strip().upper() for s in raw.split(",") if s.strip()]

    quotes_url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=" + ",".join(symbols)
    results = {}
    try:
        r = requests.get(quotes_url, timeout=5).json()
        for quote in r.get("quoteResponse", {}).get("result", []):
            sym = quote.get("symbol")
            price = quote.get("regularMarketPrice")
            change = quote.get("regularMarketChangePercent")
            history = []
            try:
                hist_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d"
                hdata = requests.get(hist_url, timeout=5).json()
                cr = hdata.get("chart", {}).get("result")
                if cr:
                    closes = cr[0]["indicators"]["quote"][0].get("close", [])
                    history = [p for p in closes if p is not None]
            except Exception:
                pass

            results[sym] = {
                "price": price,
                "change": round(change, 2) if change is not None else None,
                "history": history,
            }
        if results:
            _stock_cache.clear()
            _stock_cache.update(results)
            return results, "live"
    except Exception as ex:
        print("error fetching stocks", ex)

    # no fresh data; try the cache first
    if _stock_cache:
        print("get_stocks: returning cached data", list(_stock_cache.keys()))
        return _stock_cache.copy(), "cache"

    # if the cache is empty, see if a local data file exists; allow fallback to
    # "prices.json" in the working directory for convenience
    file_path = os.getenv('STOCK_DATA_FILE')
    if not file_path and os.path.exists('prices.json'):
        file_path = 'prices.json'
        print("get_stocks: using default prices.json file")
    if file_path:
        if os.path.exists(file_path):
            print(f"get_stocks: loading data from file {file_path}")
            file_data = _load_file_data(file_path)
            if file_data:
                _stock_cache.update(file_data)
                return file_data, "file"
            else:
                print(f"get_stocks: no usable data in {file_path}")
        else:
            print(f"get_stocks: STOCK_DATA_FILE set to {file_path} but file not found")

    # nothing available
    print("get_stocks: no data available (cache empty and no file)")
    return {}, "none"

def get_crypto():
    return {
        "BTC":{"usd":27000,"history":[26800,26900,27100,27000]},
        "ETH":{"usd":1800,"history":[1790,1800,1810,1800]},
        "DOGE":{"usd":0.075,"history":[0.073,0.074,0.076,0.075]}
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/stock/<symbol>")
def stock_detail(symbol):
    return render_template("stock_detail.html", symbol=symbol)

@app.route("/api/stocks")
def api_stocks():
    data, source = get_stocks()
    # metadata so front end can warn user if not live
    return jsonify({"source": source, "stocks": data})

@app.route("/api/currencies")
def api_currencies():
    return jsonify(get_crypto())

# removed currency detection; stocks are always shown in USD

@app.route("/api/convert/<amount>/<to_currency>")
def convert(amount, to_currency):
    """Convert a USD amount to the requested currency.

    ``amount`` is captured as a string so that integers without a decimal
    point (e.g. "27000") will still match the route. We attempt to coerce to
    float; on failure or if the external API can't be reached we simply return
    the original amount and a 200 status so the front end doesn't misbehave.
    """
    try:
        amt = float(amount)
    except ValueError:
        return jsonify({"error": "invalid amount"}), 400

    converted = amt
    try:
        r = requests.get(
            f"https://api.exchangerate.host/latest?base=USD&symbols={to_currency}",
            timeout=3,
        ).json()
        rate = r.get("rates", {}).get(to_currency)
        if rate is not None:
            converted = round(amt * rate, 2)
    except Exception:
        # leave converted equal to amt
        pass

    return jsonify({"converted": converted})

if __name__=="__main__":
    app.run(debug=True)
