import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

BASE_DIR = Path(__file__).resolve().parents[2]
PHONEINFOGA_BIN = BASE_DIR / "tools" / "phoneinfoga"


def setup():
    try:
        import phonenumbers  # noqa: F401
    except ImportError:
        print("[*] Instalando phonenumbers...")
        subprocess.run([sys.executable, "-m", "pip", "install", "phonenumbers"], check=True)


def footprint(phone: str) -> list:
    """Ejecuta el binario real de PhoneInfoga y devuelve los dorks OSINT
    (búsquedas Google por redes sociales, proveedores desechables, etc.)."""
    if not PHONEINFOGA_BIN.exists():
        return []
    try:
        result = subprocess.run(
            [str(PHONEINFOGA_BIN), "scan", "-n", phone],
            capture_output=True, text=True, timeout=40
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []

    links, category = [], "PhoneInfoga"
    for line in result.stdout.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.endswith(":") and not s.startswith("URL"):
            category = s.rstrip(":")
            continue
        m = re.match(r"URL:\s*(https?://\S+)", s)
        if m:
            url = m.group(1)
            site = re.search(r"site:([^\s+&|]+)", unquote(url))
            name = f"{category} · {site.group(1)}" if site else category
            links.append({"name": name, "url": url})
    return links


def _type_name(t) -> str:
    import phonenumbers
    return {
        phonenumbers.PhoneNumberType.MOBILE: "Móvil",
        phonenumbers.PhoneNumberType.FIXED_LINE: "Fijo",
        phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fijo o Móvil",
        phonenumbers.PhoneNumberType.TOLL_FREE: "Sin cargo",
        phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium",
        phonenumbers.PhoneNumberType.VOIP: "VoIP",
        phonenumbers.PhoneNumberType.UNKNOWN: "Desconocido",
    }.get(t, "Desconocido")


def capture(phone: str) -> dict:
    try:
        import phonenumbers
        from phonenumbers import geocoder, carrier, timezone

        parsed = phonenumbers.parse(phone, None)

        if not phonenumbers.is_valid_number(parsed):
            return {"error": "Número no válido o formato incorrecto"}

        return {
            "valid": True,
            "international": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            ),
            "national": phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.NATIONAL
            ),
            "country": geocoder.description_for_number(parsed, "es"),
            "carrier": carrier.name_for_number(parsed, "es"),
            "timezones": list(timezone.time_zones_for_number(parsed)),
            "type": _type_name(phonenumbers.number_type(parsed)),
            "possible": phonenumbers.is_possible_number(parsed),
        }
    except Exception as e:
        return {"error": str(e)}
