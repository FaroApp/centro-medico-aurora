import pathlib
import re
import sys

CSS = pathlib.Path(__file__).resolve().parent.parent / "estilos.css"


def focus_rules(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for selectors, body in re.findall(r"([^{}]+)\{([^}]*)\}", css):
        for selector in selectors.split(","):
            if selector.strip() == "a:focus":
                yield body


def main():
    rules = list(focus_rules(CSS.read_text(encoding="utf-8")))
    if not rules:
        print("FAIL: no a:focus rule found in estilos.css")
        return 1
    for body in rules:
        outlines = re.findall(r"outline\s*:\s*([^;]+);", body)
        if not outlines or outlines[-1].strip() in ("none", "0"):
            print("FAIL: a:focus must keep a visible outline, got outline: %s"
                  % (outlines[-1].strip() if outlines else "(unset)"))
            return 1
    print("OK: a:focus keeps a visible outline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
