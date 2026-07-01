"""Módulo OSINT de Instagram (instaloader).

Instagram bloquea las consultas anónimas desde IPs de servidor (403), así que
este módulo usa una sesión autenticada si está disponible. Para crearla una vez:

    cd /root/Lalobot && venv/bin/instaloader --login TU_USUARIO
    # luego copiá/dejá la sesión en datastore/ig_sessions/session-TU_USUARIO

Si no hay sesión, intenta anónimo y degrada con un mensaje claro (no rompe).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
SESSION_DIR = BASE_DIR / "datastore" / "ig_sessions"


def setup():
    try:
        import instaloader  # noqa: F401
    except ImportError:
        import subprocess
        import sys
        print("[*] Instalando instaloader...")
        subprocess.run([sys.executable, "-m", "pip", "install", "instaloader"], check=True)


def _loader():
    import instaloader
    return instaloader.Instaloader(
        quiet=True,
        download_pictures=False, download_videos=False,
        download_video_thumbnails=False, download_geotags=False,
        download_comments=False, save_metadata=False,
        max_connection_attempts=1,
    )


def _try_session(L):
    """Carga la primera sesión disponible; devuelve el usuario o None."""
    import instaloader
    # 1) sesiones en datastore/ig_sessions/session-<user>
    candidates = []
    if SESSION_DIR.is_dir():
        candidates += sorted(SESSION_DIR.glob("session-*"))
    # 2) sesión por defecto de instaloader (~/.config/instaloader)
    env_user = os.environ.get("LALOBOT_IG_USER")
    for path in candidates:
        user = path.name.replace("session-", "")
        try:
            L.load_session_from_file(user, str(path))
            return user
        except Exception:
            continue
    if env_user:
        try:
            L.load_session_from_file(env_user)
            return env_user
        except Exception:
            pass
    return None


def capture(username: str) -> dict:
    """Devuelve metadatos públicos del perfil de Instagram."""
    import instaloader
    username = username.lstrip("@").strip()
    if not username:
        return {"error": "Usuario vacío"}
    try:
        L = _loader()
        session_user = _try_session(L)
        profile = instaloader.Profile.from_username(L.context, username)
        return {
            "found": True,
            "username": profile.username,
            "full_name": profile.full_name,
            "user_id": profile.userid,
            "followers": profile.followers,
            "following": profile.followees,
            "posts": profile.mediacount,
            "is_private": profile.is_private,
            "is_verified": profile.is_verified,
            "is_business": profile.is_business_account,
            "biography": profile.biography,
            "external_url": profile.external_url,
            "profile_pic": profile.profile_pic_url,
            "auth": "sesión" if session_user else "anónimo",
        }
    except instaloader.exceptions.ProfileNotExistsException:
        return {"found": False, "error": f"El perfil '@{username}' no existe."}
    except instaloader.exceptions.ConnectionException as e:
        msg = str(e)
        if "401" in msg or "403" in msg or "Please wait" in msg or "login" in msg.lower():
            return {
                "found": False,
                "error": "Instagram requiere sesión autenticada (bloqueo anónimo). "
                         "Creá una con: venv/bin/instaloader --login TU_USUARIO",
                "needs_login": True,
            }
        return {"found": False, "error": f"Error de conexión: {msg[:150]}"}
    except Exception as e:
        return {"found": False, "error": f"{type(e).__name__}: {str(e)[:150]}"}
