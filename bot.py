import os
import time
import random
import logging
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHANNEL = "@radarventasml"
AFFILIATE_ID = os.environ.get("AFFILIATE_ID", "")
HORAS_ENTRE_POSTS = 4

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(_name_)

BUSQUEDAS = [
    ("auriculares bluetooth", "Auriculares"),
    ("smartwatch", "Smartwatch"),
    ("cargador rapido", "Cargador"),
    ("parlante portatil", "Parlante"),
    ("tablet", "Tablet"),
    ("notebook", "Notebook"),
    ("herramienta electrica", "Herramienta"),
    ("cafetera", "Cafetera"),
    ("aspiradora", "Aspiradora"),
    ("zapatillas running", "Zapatillas"),
    ("camara de seguridad", "Camara"),
    ("power bank", "Power Bank"),
    ("mouse inalambrico", "Mouse"),
    ("teclado mecanico", "Teclado"),
    ("silla gamer", "Silla"),
]

def get_oferta():
    busqueda, categoria = random.choice(BUSQUEDAS)
    url = "https://api.mercadolibre.com/sites/MLA/search"
    headers = {"User-Agent": "Mozilla/5.0"}
    params = {"q": busqueda, "sort": "relevance", "limit": 20, "condition": "new"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        con_descuento = [p for p in results if p.get("original_price") and p.get("price") and p["original_price"] > p["price"]]
        pool = con_descuento if con_descuento else results
        if not pool:
            return None, None, None
        producto = random.choice(pool[:8])
        return producto, categoria, busqueda
    except Exception as e:
        log.error("Error en API ML: %s", e)
        return None, None, None

def build_affiliate_link(url_producto):
    sep = "&" if "?" in url_producto else "?"
    return "%s%saff_id=%s" % (url_producto, sep, AFFILIATE_ID)

def formatear_precio(precio):
    return "$%s" % "{:,.0f}".format(precio).replace(",", ".")

def build_mensaje(producto, categoria, busqueda):
    titulo = producto.get("title", "")[:70]
    precio = producto.get("price", 0)
    precio_original = producto.get("original_price")
    url = producto.get("permalink", "")
    vendedor = producto.get("seller", {}).get("nickname", "")
    link = build_affiliate_link(url)
    descuento_txt = ""
    if precio_original and precio_original > precio:
        pct = int((1 - precio / precio_original) * 100)
        descuento_txt = "-%s%% OFF (antes %s)\n" % (pct, formatear_precio(precio_original))
    hora = datetime.now().strftime("%H:%M")
    msg = "%s\n\n%s\n%s%s\nVer en Mercado Libre: %s\n\n%s hs - Radar Ventas ML" % (
        titulo, formatear_precio(precio), descuento_txt,
        ("Vendedor: %s\n" % vendedor if vendedor else ""), link, hora)
    return msg

def send_telegram(mensaje):
    url = "https://api.telegram.org/bot%s/sendMessage" % TELEGRAM_TOKEN
    payload = {"chat_id": CHANNEL, "text": mensaje, "disable_web_page_preview": False}
    try:
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()
        log.info("Mensaje enviado OK")
        return True
    except Exception as e:
        log.error("Error Telegram: %s", e)
        return False

def run():
    log.info("Bot arrancando...")
    if not TELEGRAM_TOKEN:
        log.error("Falta TELEGRAM_TOKEN")
        return
    if not AFFILIATE_ID:
        log.error("Falta AFFILIATE_ID")
        return
    log.info("Canal: %s", CHANNEL)
    while True:
        try:
            log.info("Buscando oferta...")
            producto, categoria, busqueda = get_oferta()
            if producto:
                mensaje = build_mensaje(producto, categoria, busqueda)
                send_telegram(mensaje)
            else:
log.warning("Sin resultados, reintento en 30 min")
                time.sleep(1800)
                continue
        except Exception as e:
            log.error("Error: %s", e)
        log.info("Proximo post en %s horas", HORAS_ENTRE_POSTS)
        time.sleep(HORAS_ENTRE_POSTS * 3600)

if _name_ == "_main_":
    run()
