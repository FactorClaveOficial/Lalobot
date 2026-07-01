# Lalobot — Suite OSINT

Herramienta de investigación OSINT que unifica múltiples fuentes bajo un CLI y una interfaz web. Detecta automáticamente si la consulta es un **email**, **usuario** o **teléfono** y ejecuta las herramientas correspondientes.

## Herramientas integradas

| Tipo de consulta | Herramientas |
|---|---|
| **Usuario** | Sherlock, Maigret, **Instagram (instaloader)** |
| **Email** | Holehe, GHunt |
| **Teléfono** | phonenumbers (validación local) + **PhoneInfoga** (dorks OSINT) |
| **Directorio** | awesome-osint (búsqueda de herramientas) |

Herramientas adicionales como submódulos: `TorBot`, `Zen`, `changedetection.io`.

## Instalación

```bash
cd /root/Lalobot
python3 -m venv venv
venv/bin/pip install -r requirements.txt
git submodule update --init --recursive   # sherlock, awesome-osint, etc.
bash tools/fetch_phoneinfoga.sh           # binario de PhoneInfoga (~30MB)
```

## Uso

### CLI

```bash
venv/bin/python main.py scan --user juanito98      # usuario en redes + Instagram
venv/bin/python main.py scan --email juan@gmail.com
venv/bin/python main.py search "phone"             # busca en awesome-osint
venv/bin/python main.py web                         # interfaz web en :5001
```

### Web

```bash
venv/bin/python main.py web    # http://localhost:5001
```

Ingresás email / usuario / teléfono y Lalobot detecta el tipo y ejecuta todas las herramientas.

## Instagram: sesión requerida

Instagram bloquea las consultas anónimas desde IPs de servidor (403). Para que el
módulo de Instagram funcione, creá una sesión autenticada **una sola vez**:

```bash
venv/bin/instaloader --login TU_USUARIO
# Guardá/movéla a datastore/ig_sessions/session-TU_USUARIO
```

Las sesiones viven en `datastore/ig_sessions/` y **están gitignoradas** (contienen
cookies de autenticación). Sin sesión, el módulo degrada con un aviso claro.

## Estructura

```
main.py                     # CLI (scan / search / web)
lalobot/modules/
  scanner.py                # detección de tipo + Sherlock + Holehe + dorks
  maigret_scan.py           # Maigret (usuarios)
  ghunt_scan.py             # GHunt (Google)
  phoneinfooga.py           # phonenumbers + PhoneInfoga (footprint)
  instagram_scan.py         # Instagram (instaloader, con sesión)
  osint_search.py           # búsqueda en awesome-osint
  web.py                    # interfaz web Flask + API
tools/phoneinfoga           # binario (gitignored, se baja con fetch script)
datastore/ig_sessions/      # sesiones IG (gitignored)
```

> **Uso responsable:** herramienta para investigación OSINT sobre fuentes públicas.
> Respetá las leyes de privacidad y los términos de servicio de cada plataforma.
