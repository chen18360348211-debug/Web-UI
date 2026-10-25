"""Convert the Figma reference classes to ordinary CSS declarations.

There is no Tailwind runtime. Unknown utility tokens are retained in UNKNOWN
so the caller can fail its build instead of silently losing a design style.
"""

from __future__ import annotations

import re

UNKNOWN: set[str] = set()

_FIXED = {
    "absolute": "position:absolute", "relative": "position:relative",
    "fixed": "position:fixed", "sticky": "position:sticky",
    "block": "display:block", "inline-block": "display:inline-block",
    "flex": "display:flex", "inline-flex": "display:inline-flex",
    "grid": "display:grid", "inline-grid": "display:inline-grid",
    "contents": "display:contents", "hidden": "display:none",
    "flex-col": "flex-direction:column", "flex-row": "flex-direction:row",
    "flex-none": "flex:none", "flex-wrap": "flex-wrap:wrap",
    "shrink-0": "flex-shrink:0", "grow": "flex-grow:1",
    "content-stretch": "align-content:stretch",
    "items-center": "align-items:center", "items-start": "align-items:flex-start",
    "items-end": "align-items:flex-end", "items-stretch": "align-items:stretch",
    "justify-between": "justify-content:space-between",
    "justify-center": "justify-content:center", "justify-end": "justify-content:flex-end",
    "justify-start": "justify-content:flex-start",
    "justify-self-stretch": "justify-self:stretch", "self-stretch": "align-self:stretch",
    "place-items-start": "place-items:start",
    "overflow-clip": "overflow:clip", "overflow-hidden": "overflow:hidden",
    "pointer-events-none": "pointer-events:none", "object-cover": "object-fit:cover",
    "object-contain": "object-fit:contain", "not-italic": "font-style:normal",
    "italic": "font-style:italic", "capitalize": "text-transform:capitalize",
    "uppercase": "text-transform:uppercase", "lowercase": "text-transform:lowercase",
    "text-center": "text-align:center", "text-left": "text-align:left",
    "text-right": "text-align:right", "text-ellipsis": "text-overflow:ellipsis",
    "whitespace-nowrap": "white-space:nowrap", "whitespace-pre": "white-space:pre",
    "whitespace-pre-wrap": "white-space:pre-wrap",
    "line-through": "text-decoration-line:line-through",
    "underline": "text-decoration-line:underline",
    "decoration-from-font": "text-decoration-thickness:from-font",
    "decoration-solid": "text-decoration-style:solid",
    "border": "border-width:1px", "border-solid": "border-style:solid",
    "bg-clip-text": "background-clip:text;-webkit-background-clip:text",
    "max-w-none": "max-width:none", "min-w-full": "min-width:100%",
    "font-thin": "font-weight:100", "font-extralight": "font-weight:200",
    "font-light": "font-weight:300", "font-normal": "font-weight:400",
    "font-medium": "font-weight:500", "font-semibold": "font-weight:600",
    "font-bold": "font-weight:700", "font-extrabold": "font-weight:800",
    "font-black": "font-weight:900",
}

_COLOR_NAMES = {
    "white": "#fff", "black": "#000", "transparent": "transparent",
    "current": "currentColor", "inherit": "inherit",
}

_PROPERTIES = {
    "w": ("width",), "h": ("height",), "size": ("width", "height"),
    "min-w": ("min-width",), "max-w": ("max-width",),
    "min-h": ("min-height",), "max-h": ("max-height",),
    "left": ("left",), "right": ("right",), "top": ("top",),
    "bottom": ("bottom",), "inset": ("inset",),
    "inset-x": ("left", "right"), "inset-y": ("top", "bottom"),
    "p": ("padding",), "px": ("padding-left", "padding-right"),
    "py": ("padding-top", "padding-bottom"), "pt": ("padding-top",),
    "pb": ("padding-bottom",), "pl": ("padding-left",), "pr": ("padding-right",),
    "m": ("margin",), "mx": ("margin-left", "margin-right"),
    "my": ("margin-top", "margin-bottom"), "mt": ("margin-top",),
    "mb": ("margin-bottom",), "ml": ("margin-left",), "mr": ("margin-right",),
    "gap": ("gap",), "gap-x": ("column-gap",), "gap-y": ("row-gap",),
    "leading": ("line-height",), "tracking": ("letter-spacing",),
    "grid-cols": ("grid-template-columns",), "grid-rows": ("grid-template-rows",),
    "rounded": ("border-radius",), "text-shadow": ("text-shadow",),
    "shadow": ("box-shadow",), "z": ("z-index",),
}

_FONT_WEIGHTS = {
    "Thin": 100, "ExtraLight": 200, "Light": 300, "Regular": 400,
    "Normal": 400, "Medium": 500, "SemiBold": 600, "Semibold": 600,
    "Bold": 700, "ExtraBold": 800, "Black": 900,
}


def _arbitrary(raw: str) -> str:
    """Decode Figma/Tailwind arbitrary values without touching escaped slashes."""
    value = raw.replace("_", " ")
    # A + or - binary operator in calc() requires surrounding whitespace in CSS.
    # Figma's generated utility value omits it: calc(50%-0.24px).
    value = re.sub(r"(?<=[\d%)])([+-])(?=[\d.(])", r" \1 ", value)
    return value


def _dimension(raw: str) -> str | None:
    if raw.startswith("[") and raw.endswith("]"):
        return _arbitrary(raw[1:-1])
    if raw in {"full": "100%", "screen": "100vw", "auto": "auto", "px": "1px", "0": "0"}:
        return {"full": "100%", "screen": "100vw", "auto": "auto", "px": "1px", "0": "0"}[raw]
    if re.fullmatch(r"\d+/\d+", raw):
        numerator, denominator = (float(n) for n in raw.split("/"))
        return f"{numerator / denominator * 100:g}%"
    if re.fullmatch(r"\d+(?:\.\d+)?", raw):
        return f"{float(raw) * 0.25:g}rem"
    return None


def _color(raw: str) -> str | None:
    if raw in _COLOR_NAMES:
        return _COLOR_NAMES[raw]
    if raw.startswith("[") and raw.endswith("]"):
        value = _arbitrary(raw[1:-1])
        if value.startswith("color:"):
            return value[6:]
        if value.startswith(("#", "rgb(", "rgba(", "hsl(", "hsla(", "var(")) or value in _COLOR_NAMES:
            return value
    return None


def declarations(class_string: str) -> str:
    """Return semicolon-separated declarations; register unsupported tokens.

    Classes are evaluated in source order. CSS individual transform properties
    preserve Figma's combined rotate, translate and scale utilities.
    """
    result: list[str] = []
    gradient: dict[str, str] = {}
    for token in class_string.split():
        if token in _FIXED:
            result.append(_FIXED[token])
            continue

        if token.startswith("[") and token.endswith("]") and ":" in token:
            prop, value = token[1:-1].split(":", 1)
            result.append(f"{prop}:{_arbitrary(value)}")
            continue

        match = re.fullmatch(r"font-\[(['\"])(.+)\1\]", token)
        if match:
            family, separator, weight = match.group(2).partition(":")
            family = family.replace("_", " ")
            result.append(f"font-family:'{family}',sans-serif")
            if separator:
                if weight in _FONT_WEIGHTS:
                    result.append(f"font-weight:{_FONT_WEIGHTS[weight]}")
                else:
                    UNKNOWN.add(token)
            continue

        if token.startswith("bg-gradient-to-"):
            direction = token.removeprefix("bg-gradient-to-")
            directions = {"b": "to bottom", "t": "to top", "r": "to right", "l": "to left", "br": "to bottom right", "bl": "to bottom left", "tr": "to top right", "tl": "to top left"}
            if direction in directions:
                gradient["direction"] = directions[direction]
                continue

        match = re.fullmatch(r"(from|via|to)-(.+)", token)
        if match:
            stop, raw = match.groups()
            color = _color(raw)
            if color is not None:
                gradient[stop] = color
                continue
            if raw.startswith("[") and raw.endswith("]"):
                gradient[stop + "-position"] = _arbitrary(raw[1:-1])
                continue

        match = re.fullmatch(r"(bg|text|border)-(.+)", token)
        if match:
            prefix, raw = match.groups()
            color = _color(raw)
            if color is not None:
                prop = {"bg": "background-color", "text": "color", "border": "border-color"}[prefix]
                result.append(f"{prop}:{color}")
                continue
            if raw.startswith("[") and raw.endswith("]"):
                value = _arbitrary(raw[1:-1])
                if prefix == "text":
                    result.append(f"font-size:{value}")
                    continue
                if prefix == "border":
                    result.append(f"border-width:{value}")
                    continue
                if prefix == "bg" and value.startswith(("url(", "linear-gradient(", "radial-gradient(")):
                    result.append(f"background-image:{value}")
                    continue

        match = re.fullmatch(r"border-(t|b|l|r)-\[(.+)\]", token)
        if match:
            side = {"t": "top", "b": "bottom", "l": "left", "r": "right"}[match.group(1)]
            result.append(f"border-{side}-width:{_arbitrary(match.group(2))}")
            continue

        match = re.fullmatch(r"backdrop-blur-\[(.+)\]", token)
        if match:
            value = _arbitrary(match.group(1))
            result.append(f"backdrop-filter:blur({value});-webkit-backdrop-filter:blur({value})")
            continue

        match = re.fullmatch(r"opacity-(\d+(?:\.\d+)?)", token)
        if match:
            result.append(f"opacity:{float(match.group(1)) / 100:g}")
            continue

        match = re.fullmatch(r"(col|row)-(\d+)", token)
        if match:
            result.append(f"grid-{'column' if match.group(1) == 'col' else 'row'}:{match.group(2)}")
            continue

        match = re.fullmatch(r"(-?)rotate-(\d+(?:\.\d+)?)", token)
        if match:
            result.append(f"rotate:{match.group(1)}{match.group(2)}deg")
            continue

        match = re.fullmatch(r"(-?)translate-([xy])-(.+)", token)
        if match:
            negative, axis, raw = match.groups()
            value = _dimension(raw)
            if value is not None:
                value = negative + value
                result.append(f"translate:{value} 0" if axis == "x" else f"translate:0 {value}")
                continue

        match = re.fullmatch(r"(-?)scale-([xy])-(\d+(?:\.\d+)?)", token)
        if match:
            negative, axis, raw = match.groups()
            value = float(raw) / 100 * (-1 if negative else 1)
            result.append(f"scale:{value:g} 1" if axis == "x" else f"scale:1 {value:g}")
            continue

        # Longest names first (e.g. min-w before w, gap-x before gap).
        matched = False
        for prefix in sorted(_PROPERTIES, key=len, reverse=True):
            if token.startswith(prefix + "-"):
                raw = token[len(prefix) + 1:]
                value = _dimension(raw)
                if value is not None:
                    if prefix == "h" and raw == "screen":
                        value = "100vh"
                    result.extend(f"{prop}:{value}" for prop in _PROPERTIES[prefix])
                    matched = True
                break
        if matched:
            continue
        UNKNOWN.add(token)

    if "direction" in gradient:
        stops = []
        for stop, fallback in (("from", "transparent"), ("via", ""), ("to", "transparent")):
            color = gradient.get(stop, fallback)
            if color:
                position = gradient.get(stop + "-position", "")
                stops.append(color + (" " + position if position else ""))
        result.append(f"background-image:linear-gradient({gradient['direction']},{','.join(stops)})")
    return ";".join(result) + (";" if result else "")


if __name__ == "__main__":
    import argparse
    import glob
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("references", nargs="+", help="Figma reference text files or glob patterns")
    args = parser.parse_args()
    files = [Path(p) for pattern in args.references for p in glob.glob(pattern)]
    classes = [value for path in files for value in re.findall(r'className="([^"]+)"', path.read_text(encoding="utf-8"))]
    tokens = {token for value in classes for token in value.split()}
    for value in classes:
        declarations(value)
    print(f"Files: {len(files)}; class attributes: {len(classes)}; unique utilities: {len(tokens)}; supported: {len(tokens - UNKNOWN)}")
    print("Unsupported:", ", ".join(sorted(UNKNOWN)) if UNKNOWN else "none")
    raise SystemExit(bool(UNKNOWN))
