#!/usr/bin/env python3
"""Entrypoint para producción/pm2: sirve Lalobot en localhost (para túnel SSH)."""
from lalobot.modules.web import run

if __name__ == "__main__":
    run(host="127.0.0.1", port=5001)
