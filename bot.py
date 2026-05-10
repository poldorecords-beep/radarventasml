import os, time, random, logging, requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHANNEL = "@radarventasml"
AFFILIATE_ID = os.environ.get("AFFILIATE_ID", "")
HORAS = 4

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(_name_)

BUSQUEDAS = ["auriculares bluetooth","smartwatch","cargador rapido","notebook","tablet","cafetera","aspiradora","zapatillas running","camara de seguridad","power bank","mouse inalambrico","silla gamer"]

def get_oferta():
    q = random.choice(BUSQUEDAS)
    try:
        r = requests.get("https://api.mercadolibre.com/sites/MLA/search", headers={"User-Agent":"Mozilla/5.0"}, params={"q":q,"sort":"relevance","limit":20,"condition":"new"}, timeout=15)
        r.raise_for_status()
        items = r.json().get("results", [])
        desc = [p for p in items if p.get("original_price") and p.get("price") and p["original_price"] > p["price"]]
        pool = desc if desc else items
        return (random.choice(pool[:8]), q) if pool else (None, None)
    except Exception as e:
        log.error("API error: %s", e)
        return (None, None)

def make_link(url):
    sep = "&" if "?" in url else "?"
    return "%s%saff_id=%s" % (url, sep, AFFILIATE_ID)

def make_msg(p, q):
    titulo = p.get("title","")[:70]
    precio = p.get("price", 0)
    orig = p.get("original_price")
    url = p.get("permalink","")
    desc = ""
    if orig and orig > precio:
        pct = int((1 - precio/orig)*100)
        desc = "-%d%% OFF\n" % pct
    return "%s\n\n$%s\n%sVer: %s\n%s hs" % (titulo, "{:,.0f}".format(precio).replace(",","."), desc, make_link(url), datetime.now().strftime("%H:%M"))

def send(msg):
    try:
        r = requests.post("https://api.telegram.org/bot%s/sendMessage" % TELEGRAM_TOKEN, json={"chat_id":CHANNEL,"text":msg}, timeout=15)
        r.raise_for_status()
        log.info("Enviado OK")
    except Exception as e:
        log.error("Telegram error: %s", e)

def run():
    log.info("Bot iniciando")
    if not TELEGRAM_TOKEN or not AFFILIATE_ID:
        log.error("Faltan variables")
        return
    while True:
        try:
            p, q = get_oferta()
            if p:
                send(make_msg(p, q))
            else:
                time.sleep(1800)
                continue
        except Exception as e:
            log.error("Error: %s", e)
        time.sleep(HORAS * 3600)

if _name_ == "_main_":
    run()
