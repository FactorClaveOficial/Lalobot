import subprocess
import sys


def setup():
    try:
        import phonenumbers  # noqa: F401
    except ImportError:
        print("[*] Instalando phonenumbers...")
        subprocess.run([sys.executable, "-m", "pip", "install", "phonenumbers"], check=True)


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
