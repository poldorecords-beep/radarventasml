import os, time, random, logging, requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHANNEL = "@radarventasml"
AMAZON_TAG = os.environ.get("AMAZON_TAG", "radarventasml-20")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")

X_CONSUMER_KEY = os.environ.get("X_CONSUMER_KEY", "")
X_CONSUMER_SECRET = os.environ.get("X_CONSUMER_SECRET", "")
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET", "")

HORAS = 6

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

def get_deals():
    try:
        url = "https://real-time-amazon-data.p.rapidapi.com/deals-v2"
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
        }
        params = {"country": "US", "min_product_star_rating": "ALL", "price_range": "ALL", "discount_range": "ALL"}
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        deals = r.json().get("data", {}).get("deals", [])
        return deals if deals else []
    except Exception as e:
        log.error("API error: %s", e)
        return []

def make_link(asin):
    if asin:
        return "https://www.amazon.com/dp/%s?tag=%s" % (asin, AMAZON_TAG)
    return "https://www.amazon.com?tag=%s" % AMAZON_TAG

def make_msg(deal):
    titulo = deal.get("deal_title", "")[:70]
    precio = deal.get("deal_price", {}).get("amount", "")
    orig = deal.get("list_price", {}).get("amount", "")
    asin = deal.get("product_asin", "")
    pct = deal.get("savings_percentage", "")
    desc = ""
    if pct:
        desc = "🔥 -%s%% OFF\n" % pct
    msg = "%s%s" % (desc, titulo)
    if precio:
        msg += "\n\nPrecio: USD %s" % precio
    if orig:
        msg += "\nAntes: USD %s" % orig
    msg += "\nVer: %s\n%s hs" % (make_link(asin), datetime.now().strftime("%H:%M"))
    return msg

def make_tweet(deal):
    titulo = deal.get("deal_title", "")[:60]
    precio = deal.get("deal_price", {}).get("amount", "")
    asin = deal.get("product_asin", "")
    pct = deal.get("savings_percentage", "")
    desc = ""
    if pct:
        desc = "🔥 -%s%% OFF | " % pct
    tweet = "%s%s" % (desc, titulo)
    if precio:
        tweet += " | USD %s" % precio
    tweet += "\n%s" % make_link(asin)
    return tweet[:280]

def send_telegram(msg):
    try:
        r = requests.post(
            "https://api.telegram.org/bot%s/sendMessage" % TELEGRAM_TOKEN,
            json={"chat_id": CHANNEL, "text": msg},
            timeout=15
        )
        r.raise_for_status()
        log.info("Telegram: Enviado OK")
    except Exception as e:
        log.error("Telegram error: %s", e)

def send_tweet(msg):
    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=X_CONSUMER_KEY,
            consumer_secret=X_CONSUMER_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_TOKEN_SECRET
        )
        client.create_tweet(text=msg)
        log.info("X: Enviado OK")
    except Exception as e:
        log.error("X error: %s", e)

def run():
    log.info("Bot iniciando")
    if not TELEGRAM_TOKEN or not RAPIDAPI_KEY:
        log.error("Faltan variables")
        return
    while True:
        try:
            deals = get_deals()
            if deals:
                deal = random.choice(deals[:10])
                send_telegram(make_msg(deal))
                send_tweet(make_tweet(deal))
            else:
                log.warning("Sin deals, reintentando en 30 min")
                time.sleep(1800)
                continue
        except Exception as e:
            log.error("Error: %s", e)
        time.sleep(HORAS * 3600)

if __name__ == "__main__":
    run()
