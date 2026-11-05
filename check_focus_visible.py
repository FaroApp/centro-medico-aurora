from html.parser import HTMLParser
from pathlib import Path
import re


class PageElements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.main_depth = 0
        self.form_depth = 0
        self.p_depth = 0
        self.div_depth = 0
        self.icon_depth = 0
        self.counts = {"form_input": 0, "form_button": 0, "link": 0, "icon_button": 0}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        in_main = self.main_depth > 0
        if tag == "main":
            self.main_depth += 1
            return
        if not in_main:
            return
        if tag == "form":
            self.form_depth += 1
        elif tag == "p":
            self.p_depth += 1
        elif tag == "div":
            self.div_depth += 1
            if "iconos" in attrs.get("class", "").split():
                self.icon_depth += 1
        elif tag == "input" and self.form_depth and attrs.get("type") == "text":
            self.counts["form_input"] += 1
        elif tag == "button":
            if self.form_depth:
                self.counts["form_button"] += 1
            if self.icon_depth:
                self.counts["icon_button"] += 1
        elif tag == "a" and self.p_depth >= 1:
            self.counts["link"] += 1

    def handle_endtag(self, tag):
        if tag == "main" and self.main_depth:
            self.main_depth -= 1
        elif self.main_depth:
            if tag == "form" and self.form_depth:
                self.form_depth -= 1
            elif tag == "p" and self.p_depth:
                self.p_depth -= 1
            elif tag == "div" and self.div_depth:
                self.div_depth -= 1
                if self.icon_depth:
                    self.icon_depth -= 1


page = PageElements()
page.feed(Path("index.html").read_text(encoding="utf-8"))
expected_counts = {"form_input": 2, "form_button": 1, "link": 1, "icon_button": 2}
assert page.counts == expected_counts, f"Expected the six affected controls in index.html, found {page.counts}"

css = Path("estilos.css").read_text(encoding="utf-8")
css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
rules = re.findall(r"([^{}]+)\{([^{}]*)\}", css, re.S)


def luminance_component(value):
    value /= 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def has_contrasting_outline(declarations):
    outline = re.search(r"outline\s*:\s*([^;]+)", declarations, re.I)
    if not outline or re.search(r"\bnone\b", outline.group(1), re.I):
        return False
    color = re.search(r"#([\da-f]{3}|[\da-f]{6})\b", outline.group(1), re.I)
    if not color:
        return False
    digits = color.group(1)
    rgb = [int(c * 2, 16) for c in digits] if len(digits) == 3 else [int(digits[i:i + 2], 16) for i in (0, 2, 4)]
    luminance = sum(weight * luminance_component(value) for weight, value in zip((0.2126, 0.7152, 0.0722), rgb))
    return 1.05 / (luminance + 0.05) >= 1.5


def covered(selector, declarations):
    selectors = [item.strip() for item in selector.split(",")]
    return any(
        re.fullmatch(r"(?:input|button|a):focus-visible", item, re.I)
        and has_contrasting_outline(declarations)
        and re.search(r"outline-offset\s*:\s*[^;]+", declarations, re.I)
        for item in selectors
    )


visible_rules = [selector for selector, declarations in rules if covered(selector, declarations)]
assert visible_rules, "Expected a visible :focus-visible rule, but none was found"

required_selectors = ["input:focus-visible", "button:focus-visible", "a:focus-visible"]
for required in required_selectors:
    assert any(
        required in [part.strip() for part in selector.split(",")]
        and covered(selector, declarations)
        for selector, declarations in rules
    ), f"Expected visible focus indicator for {required}, but none was found"
