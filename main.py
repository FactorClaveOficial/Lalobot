#!/usr/bin/env python3
"""Lalobot — Suite OSINT de búsqueda e investigación."""

import argparse
import sys


def cmd_scan(args):
    if not args.user and not args.email:
        print("[!] Debes indicar al menos --user o --email")
        sys.exit(1)
    from lalobot.modules.scanner import setup, scan
    setup()
    scan(username=args.user, email=args.email)


def cmd_search(args):
    from lalobot.modules.osint_search import run
    run(" ".join(args.term))


def cmd_web(args):
    from lalobot.modules.web import run
    run(port=args.port)


def main():
    parser = argparse.ArgumentParser(
        prog="lalobot",
        description="Lalobot — Suite OSINT de búsqueda e investigación",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="Buscar usuario y/o email en redes sociales")
    p_scan.add_argument("--user", "-u", metavar="USUARIO", help="Nombre de usuario para Sherlock")
    p_scan.add_argument("--email", "-e", metavar="EMAIL", help="Correo electrónico para Holehe")
    p_scan.set_defaults(func=cmd_scan)

    p_search = sub.add_parser("search", help="Buscar herramientas en el directorio awesome-osint")
    p_search.add_argument("term", nargs="+", help="Término de búsqueda")
    p_search.set_defaults(func=cmd_search)

    p_web = sub.add_parser("web", help="Lanzar la interfaz web")
    p_web.add_argument("--port", type=int, default=5001, metavar="PUERTO", help="Puerto (default: 5001)")
    p_web.set_defaults(func=cmd_web)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
