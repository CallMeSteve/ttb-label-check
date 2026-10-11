from app.models import Box, Line

WARN = ("GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic "
        "beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic "
        "beverages impairs your ability to drive a car or operate machinery, and may cause health problems.")


def mk(texts, image=0, conf=0.95, heights=None):
    out = []
    for i, t in enumerate(texts):
        h = (heights or {}).get(i, 30)
        y = 40 + i * 60
        out.append(Line(t, conf, Box(image, 20, y, 20 + 12 * len(t), y + h)))
    return out


def wrap(text, width=45):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return lines
