"""
Tramitly — RND Scraper (Registro Nacional de Detenciones - SSPC)
================================================================
Usa requests puro + BeautifulSoup. Sin Playwright.

Resolución de captcha (por orden de prioridad):
  1. pytesseract (OCR local, gratis)
  2. 2captcha    (servicio en la nube, fallback, ~$1/1000 captchas)

Instalar:
    pip install requests beautifulsoup4 pytesseract pillow python-dotenv
    # Tesseract en el sistema:
    # Windows: https://github.com/UB-Mannheim/tesseract/wiki
    # Linux:   sudo apt install tesseract-ocr
    # Mac:     brew install tesseract

Variables de entorno (.env):
    TWOCAPTCHA_API_KEY=tu_key_aqui   # solo si usas 2captcha
"""

import os
import re
import time
import base64
import logging
from io import BytesIO
from dataclasses import dataclass, asdict
from typing import Optional
from dotenv import load_dotenv

import requests
from bs4 import BeautifulSoup
import pytesseract
from PIL import Image, ImageEnhance

load_dotenv()
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_URL   = "https://consultasdetenciones.sspc.gob.mx"
CONSULTA   = f"{BASE_URL}/"
RESULTADOS = f"{BASE_URL}/Resultados.aspx"

TWOCAPTCHA_API_KEY = os.getenv("TWOCAPTCHA_API_KEY", "")

# Datos del solicitante (quien hace la búsqueda) — requeridos por el form
SOLICITANTE = {
    "nombre":   "Tramitly",
    "paterno":  "Sistemas",
    "materno":  "SA",
    "curp":     "",
    "telefono": "5500000000",
    "correo":   "contacto@tramitly.mx",
    "gps":      "",
}

DELAY = 2.0  # segundos entre búsquedas


# ─────────────────────────────────────────
#  MODELO DE DATOS
# ─────────────────────────────────────────

@dataclass
class ResultadoRND:
    nombre_buscado: str
    estado: str
    nombre: Optional[str] = None
    lugar_detencion: Optional[str] = None
    direccion: Optional[str] = None
    fecha_hora: Optional[str] = None
    autoridad_detiene: Optional[str] = None
    autoridad_resguarda: Optional[str] = None
    sin_resultados: bool = False
    error: Optional[str] = None


# ─────────────────────────────────────────
#  RESOLUCIÓN DE CAPTCHA
#  Estrategia 1: pytesseract (OCR local)
#  Estrategia 2: 2captcha (fallback cloud)
# ─────────────────────────────────────────

def _preprocesar_imagen(img_bytes: bytes) -> Image.Image:
    """Preprocesa la imagen para mejorar la precisión del OCR."""
    img = Image.open(BytesIO(img_bytes)).convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.5)
    img = img.point(lambda x: 0 if x < 140 else 255, "1")
    img = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
    return img


def resolver_captcha_ocr(img_bytes: bytes) -> str:
    """Resuelve el captcha localmente con pytesseract."""
    try:
        img = _preprocesar_imagen(img_bytes)
        texto = pytesseract.image_to_string(
            img,
            config=(
                "--psm 8 --oem 3 "
                "-c tessedit_char_whitelist="
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
            )
        ).strip()
        texto = re.sub(r"\s+", "", texto)
        log.info(f"[Captcha OCR] Texto detectado: '{texto}'")
        return texto
    except Exception as e:
        log.error(f"[Captcha OCR] Error: {e}")
        return ""


def resolver_captcha_2captcha(img_bytes: bytes, api_key: str) -> str:
    """
    Resuelve el captcha usando el servicio 2captcha.com.
    Costo aproximado: $1 USD por cada 1,000 captchas.
    Documentación: https://2captcha.com/2captcha-api
    """
    if not api_key:
        log.warning("[2captcha] No hay API key configurada")
        return ""

    try:
        # Paso 1: Enviar imagen a 2captcha
        img_b64 = base64.b64encode(img_bytes).decode()
        resp = requests.post(
            "https://2captcha.com/in.php",
            data={
                "key":    api_key,
                "method": "base64",
                "body":   img_b64,
                "json":   1,
            },
            timeout=15,
        )
        data = resp.json()
        if data.get("status") != 1:
            log.error(f"[2captcha] Error al enviar: {data}")
            return ""

        captcha_id = data["request"]
        log.info(f"[2captcha] Captcha enviado, ID: {captcha_id}")

        # Paso 2: Esperar y obtener resultado (polling)
        for _ in range(12):  # máximo ~60 segundos
            time.sleep(5)
            res = requests.get(
                "https://2captcha.com/res.php",
                params={"key": api_key, "action": "get", "id": captcha_id, "json": 1},
                timeout=10,
            ).json()

            if res.get("status") == 1:
                texto = res["request"].strip()
                log.info(f"[2captcha] Resuelto: '{texto}'")
                return texto

            if res.get("request") != "CAPCHA_NOT_READY":
                log.error(f"[2captcha] Error obteniendo resultado: {res}")
                return ""

        log.warning("[2captcha] Timeout esperando solución")
        return ""

    except Exception as e:
        log.error(f"[2captcha] Excepción: {e}")
        return ""


def resolver_captcha(img_bytes: bytes, forzar_2captcha: bool = False) -> str:
    """
    Resuelve el captcha con la mejor estrategia disponible:
      1. Si forzar_2captcha=True y hay API key → usa 2captcha directamente
      2. Intenta OCR local (pytesseract) primero
      3. Si el OCR falla o devuelve texto muy corto → fallback a 2captcha
    """
    if forzar_2captcha and TWOCAPTCHA_API_KEY:
        return resolver_captcha_2captcha(img_bytes, TWOCAPTCHA_API_KEY)

    # Intento 1: OCR local
    texto = resolver_captcha_ocr(img_bytes)

    # Si el resultado parece válido (mínimo 4 chars alfanuméricos) lo usamos
    if len(texto) >= 4 and texto.isalnum():
        return texto

    # Fallback a 2captcha si hay key disponible
    if TWOCAPTCHA_API_KEY:
        log.info(f"[Captcha] OCR inseguro ('{texto}'), usando 2captcha como fallback...")
        return resolver_captcha_2captcha(img_bytes, TWOCAPTCHA_API_KEY)

    log.warning(f"[Captcha] Solo OCR disponible, usando resultado: '{texto}'")
    return texto


# ─────────────────────────────────────────
#  SCRAPER RND
# ─────────────────────────────────────────

class RNDScraper:

    def __init__(self, solicitante: dict = None):
        self.sol = solicitante or SOLICITANTE
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/146.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
        })

    # ── Paso 1: GET inicial para obtener VIEWSTATE y captcha ──────────────

    def _get_pagina_inicial(self) -> tuple[dict, str]:
        """
        Carga la página de consulta y extrae:
          - Todos los campos hidden de ASP.NET (__VIEWSTATE, etc.)
          - URL de la imagen del captcha
        """
        resp = self.session.get(CONSULTA, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extraer campos hidden ASP.NET
        hidden = {}
        for inp in soup.select("input[type='hidden']"):
            name = inp.get("name", "")
            if name:
                hidden[name] = inp.get("value", "")

        # Buscar imagen del captcha
        # El captcha generalmente está en un <img> cerca del campo txtVerificacodigo
        captcha_url = ""
        img_captcha = (
            soup.select_one("img#MainContent_imgCaptcha") or
            soup.select_one("img[src*='captcha' i]") or
            soup.select_one("img[src*='Captcha' i]") or
            soup.select_one("img[src*='Codigo' i]") or
            soup.select_one("img[src*='codigo' i]")
        )
        if img_captcha:
            src = img_captcha.get("src", "")
            captcha_url = src if src.startswith("http") else f"{BASE_URL}/{src.lstrip('/')}"

        log.info(f"[RND] VIEWSTATE obtenido: {hidden.get('__VIEWSTATE', '')[:30]}...")
        log.info(f"[RND] Captcha URL: {captcha_url}")
        return hidden, captcha_url

    # ── Paso 2: Descargar y resolver captcha ─────────────────────────────

    def _obtener_captcha(self, captcha_url: str, forzar_2captcha: bool = False) -> str:
        if not captcha_url:
            log.warning("[RND] No se encontró URL del captcha")
            return ""
        resp = self.session.get(captcha_url, timeout=10)
        resp.raise_for_status()
        return resolver_captcha(resp.content, forzar_2captcha=forzar_2captcha)

    # ── Paso 3: POST con todos los campos ────────────────────────────────

    def _hacer_busqueda(
        self,
        hidden: dict,
        captcha_texto: str,
        nombre: str,
        paterno: str,
        materno: str,
        fecha_nac: str = "",
        curp_persona: str = "",
    ) -> str:
        """Envía el formulario y devuelve el HTML de resultados."""

        payload = {
            # Campos ASP.NET obligatorios
            "__EVENTTARGET":        "",
            "__EVENTARGUMENT":      "",
            "__LASTFOCUS":          "",
            "__VIEWSTATE":          hidden.get("__VIEWSTATE", ""),
            "__VIEWSTATEGENERATOR": hidden.get("__VIEWSTATEGENERATOR", ""),
            "__EVENTVALIDATION":    hidden.get("__EVENTVALIDATION", ""),
            "__VIEWSTATEENCRYPTED": hidden.get("__VIEWSTATEENCRYPTED", ""),

            # Datos del solicitante
            "ctl00$MainContent$txtNombre":        self.sol["nombre"],
            "ctl00$MainContent$txtApellidoPaterno": self.sol["paterno"],
            "ctl00$MainContent$txtApellidoMaterno": self.sol["materno"],
            "ctl00$MainContent$txtCurp":          self.sol.get("curp", ""),
            "ctl00$MainContent$txtTelefono":      self.sol["telefono"],
            "ctl00$MainContent$txtCorreo":        self.sol["correo"],
            "ctl00$MainContent$txtDireccionGPS":  self.sol.get("gps", ""),
            "ctl00$MainContent$txtDireccion2":    "",

            # Datos de la persona buscada
            "ctl00$MainContent$txtNombrePersona":    nombre,
            "ctl00$MainContent$txtAPaternoPersona":  paterno,
            "ctl00$MainContent$txtAMaternoPersona":  materno,
            "ctl00$MainContent$inputFechaNacimiento": fecha_nac,
            "ctl00$MainContent$txtCurpPersona":      curp_persona,

            # Captcha y submit
            "ctl00$MainContent$txtVerificacodigo": captcha_texto,
            "ctl00$MainContent$cbxTerminos":       "on",
            "ctl00$MainContent$btnBuscar":         "Buscar",

            # Campos de localización (vacíos)
            "ctl00$MainContent$Localizacion$txtColonia":               "",
            "ctl00$MainContent$Localizacion$txtcalle":                 "",
            "ctl00$MainContent$Localizacion$txtentrecalle":            "",
            "ctl00$MainContent$Localizacion$txtycalle":                "",
            "ctl00$MainContent$Localizacion$txtNumeroExterior":        "",
            "ctl00$MainContent$Localizacion$txtNumeroInterior":        "",
            "ctl00$MainContent$Localizacion$txtcodigopostal":          "",
            "ctl00$MainContent$Localizacion$HiddenFieldResultadoUrbana": "",
            "ctl00$MainContent$Localizacion$HiddenFieldDatosMapaUrbana": "",
        }

        headers_extra = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": CONSULTA,
            "Origin": BASE_URL,
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Upgrade-Insecure-Requests": "1",
        }

        resp = self.session.post(
            CONSULTA,
            data=payload,
            headers=headers_extra,
            allow_redirects=True,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.text

    # ── Paso 4: Parsear tabla de resultados ──────────────────────────────

    def _parsear_resultados(self, html: str, nombre_buscado: str, estado: str) -> list[ResultadoRND]:
        soup = BeautifulSoup(html, "html.parser")
        tabla = soup.select_one("#MainContent_gdvResultados")

        if not tabla:
            return [ResultadoRND(nombre_buscado=nombre_buscado, estado=estado, error="No se encontró tabla de resultados")]

        filas = tabla.select("tbody tr") or tabla.select("tr")[1:]  # skip header
        resultados = []

        for fila in filas:
            celdas = [td.get_text(strip=True) for td in fila.select("td")]

            # Fila de "no hay resultados"
            if len(celdas) == 1:
                resultados.append(ResultadoRND(
                    nombre_buscado=nombre_buscado,
                    estado=estado,
                    sin_resultados=True,
                ))
                continue

            if len(celdas) >= 6:
                resultados.append(ResultadoRND(
                    nombre_buscado=nombre_buscado,
                    estado=estado,
                    nombre=celdas[0],
                    lugar_detencion=celdas[1],
                    direccion=celdas[2],
                    fecha_hora=celdas[3],
                    autoridad_detiene=celdas[4],
                    autoridad_resguarda=celdas[5],
                ))

        return resultados or [ResultadoRND(nombre_buscado=nombre_buscado, estado=estado, sin_resultados=True)]

    # ── Método principal ─────────────────────────────────────────────────

    def buscar(
        self,
        nombre: str,
        paterno: str,
        materno: str = "",
        fecha_nac: str = "",   # formato DD/MM/YYYY
        curp: str = "",
        estado: str = "Nacional",
        reintentos: int = 3,
        forzar_2captcha: bool = False,
    ) -> list[ResultadoRND]:

        nombre_completo = f"{nombre} {paterno} {materno}".strip()
        log.info(f"[RND] Buscando: {nombre_completo}")

        for intento in range(1, reintentos + 1):
            try:
                hidden, captcha_url = self._get_pagina_inicial()

                # En el último intento, forzar 2captcha si está disponible
                usar_2captcha = forzar_2captcha or (intento == reintentos and TWOCAPTCHA_API_KEY)
                captcha_texto = self._obtener_captcha(captcha_url, forzar_2captcha=usar_2captcha)

                if not captcha_texto:
                    log.warning(f"[RND] Captcha vacío en intento {intento}, reintentando...")
                    time.sleep(2)
                    continue

                html = self._hacer_busqueda(hidden, captcha_texto, nombre, paterno, materno, fecha_nac, curp)

                # Verificar si hubo error de captcha
                if "código de verificación" in html.lower() or "captcha" in html.lower():
                    log.warning(f"[RND] Captcha incorrecto en intento {intento}: '{captcha_texto}'")
                    time.sleep(2)
                    continue

                return self._parsear_resultados(html, nombre_completo, estado)

            except requests.RequestException as e:
                log.error(f"[RND] Error de red en intento {intento}: {e}")
                time.sleep(3)

        return [ResultadoRND(nombre_buscado=nombre_completo, estado=estado, error=f"Falló tras {reintentos} intentos")]


# ─────────────────────────────────────────
#  USO DIRECTO
# ─────────────────────────────────────────

if __name__ == "__main__":
    import json

    scraper = RNDScraper()

    resultados = scraper.buscar(
        nombre="angel alessandro",
        paterno="acosta",
        materno="meza",
        fecha_nac="29/09/2007",
    )

    print(json.dumps([asdict(r) for r in resultados], ensure_ascii=False, indent=2))
