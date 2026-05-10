import os
import time
import random
import logging
import requests
from datetime import datetime

# =============================================
# CONFIGURACION — NO TOCAR
# =============================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHANNEL = "@radarventasml"
AFFILIATE_ID = os.environ.get("AFFILIATE_ID", "")
HORAS_ENTRE_POSTS = 4
# =============================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger(_name_)

BUSQUEDAS = [
    ("auriculares bluetooth", "🎧"),
    ("smartwatch", "⌚"),
    ("cargador rapido", "⚡"),
    ("parlante portatil", "🔊"),
    ("tablet", "📱"),
    ("notebook", "💻"),
    ("herramienta electrica", "🔧"),
    ("cafetera", "☕"),
    ("aspiradora", "🏠"),
    ("zapatillas running", "👟"),
    ("camara de seguridad", "📷"),
    ("power bank", "🔋"),
    ("mouse inalambrico", "🖱️"),
    ("teclado mecanico", "⌨️"),
    ("silla gamer", "🪑"),
]

def get_oferta():
    busqueda, emoji = random.choice(BUSQUEDAS)
    
    url = "https://api.mercadolibre.com/sites/MLA/search"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    params = {
        "q": busqueda,
        "sort": "relevance",
        "limit": 20,
        "condition": "new",
        "attributes": "id,title,price,original_price,permalink,seller",
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        
        con_descuento = [
            p for p in results
            if p.get("original_price") and p.get("price")
            and p["original_price"] > p["price"]
        ]
        
        pool = con_descuento if con_descuento else results
        
        if not pool:
            return None, None, None
            
        producto = random.choice(pool[:8])
        return producto, emoji, busqueda
        
    except Exception as e:
        log.error(f"Error en API ML: {e}")
        return None, None, None

def build_affiliate_link(url_producto):
    sep = "&" if "?" in url_producto else "?"
    return f"{url_producto}{sep}aff_id={AFFILIATE_ID}&aff_platform=telegram"

def formatear_precio(precio):
    return f"${precio:,.0f}".replace(",", ".")

def build_mensaje(producto, emoji, busqueda):
    titulo = producto.get("title", "")[:70]
    precio = producto.get("price", 0)
    precio_original = producto.get("original_price")
    url = producto.get("permalink", "")
    vendedor = producto.get("seller", {}).get("nickname", "")
    
    link = build_affiliate_link(url)
    
    descuento_txt = ""
    if precio_original and precio_original > precio:
        pct = int((1 - precio / precio_original) * 100)
        precio_original_fmt = formatear_precio(precio_original)
        descuento_txt = f"🔻 -{pct}% OFF (antes {precio_original_fmt})\n"
    
    hora = datetime.now().strftime("%H:%M")
    
    msg = (
        f"{emoji} {titulo}\n\n"
        f"💰 {formatear_precio(precio)}\n"
        f"{descuento_txt}"
        f"✅ Producto nuevo\n"
        f"{'🏪 ' + vendedor + chr(10) if vendedor else ''}\n"
        f"👉 [Ver en Mercado Libre]({link})\n\n"
        f"🕐 {hora} hs — Radar Ventas ML"
    )
    return msg

def send_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL,
        "text": mensaje,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()
        log.info("✅ Mensaje enviado")
        return True
    except Exception as e:
        log.error(f"Error Telegram: {e}")
        return False

def run():
    log.info("🚀 Radar Ventas ML Bot arrancando...")
    
    if not TELEGRAM_TOKEN:
        log.error(" Falta TELEGRAM_TOKEN")
        return
    if not AFFILIATE_ID:
        log.error(" Falta AFFILIA
