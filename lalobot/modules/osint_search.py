import re
from pathlib import Path

README = Path(__file__).parent.parent.parent / "awesome-osint" / "README.md"

RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
DIM    = "\033[2m"


def parse_readme():
    entries = []
    section = "General"
    section_re = re.compile(r"^#{1,3} .*?([A-Za-z].+)$")
    link_re = re.compile(r"^\*\s+\[(.+?)\]\((https?://[^\)]+)\)\s*[-–]?\s*(.*)")

    with open(README, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()
            m = section_re.match(line)
            if m and line.startswith("#"):
                raw = re.sub(r"\[.*?\]\(.*?\)", "", m.group(1)).strip()
                if raw:
                    section = raw
                continue
            m = link_re.match(line)
            if m:
                entries.append((section, m.group(1), m.group(2), m.group(3).strip()))
    return entries


def search(term: str):
    entries = parse_readme()
    term_lower = term.lower()
    return [
        (sec, name, url, desc)
        for sec, name, url, desc in entries
        if term_lower in f"{name} {url} {desc} {sec}".lower()
    ]


def print_results(term: str, results):
    if not results:
        print(f"\n{YELLOW}Sin resultados para: '{term}'{RESET}\n")
        return

    print(f"\n{BOLD}{CYAN}Resultados para '{term}' — {len(results)} encontrados{RESET}\n")
    current_section = None
    for section, name, url, desc in results:
        if section != current_section:
            print(f"  {BOLD}{YELLOW}[ {section} ]{RESET}")
            current_section = section
        print(f"  {GREEN}{BOLD}{name}{RESET}")
        print(f"    {DIM}{url}{RESET}")
        if desc:
            print(f"    {desc}")
        print()


def run(term: str):
    results = search(term)
    print_results(term, results)
