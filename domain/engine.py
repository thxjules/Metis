# domain/engine.p
import re
import unicodedata

RISK_THRESHOLD = 2

INTEREST_PHRASES = {
    "interesante": -3,
    "me gusta": -2,
    "me interesa": -1,
    "eso suena bien": -1,
    "es justo lo que necesito": -3,
    "es lo que busco": -3,
    "exactamente lo que necesito": -3,
    "me parece bien": -2,
    "perfecto": -2,
    "genial": -2,
}

RISK_PHRASES = {
    "no gracias": 1,
    "no estoy seguro": 2,
    "no me interesa": 3,
    "no le puedo entender": 2,
    "no quiero": 3,
    "no es lo que busco": 2,
    "no es para mi": 2,
    "no es lo que necesito": 2,
    "no es lo que quiero": 2,
}

CLOSING_PHRASES = [
    "adios",
    "hasta luego",
    "chao",
    "nos vemos",
    "espero la informacion",
    "llamame luego",
    "gracias por tu tiempo",
    "gracias por la informacion",
    "gracias por tu ayuda",
]


def normalize(text: str) -> str:
    text = text.lower()
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    return re.sub(r"[^\w\s]", "", text)


# SOLO calcula delta (no toca estado)
def calculate_risk_delta(text_window: list[str]) -> int:
    text = normalize(" ".join(text_window))

    risk_delta = 0
    interest_delta = 0

    for phrase, weight in RISK_PHRASES.items():
        if phrase in text:
            risk_delta += weight

    for phrase, weight in INTEREST_PHRASES.items():
        if phrase in text:
            interest_delta += abs(weight)

    return risk_delta - interest_delta


# SOLO detecta cierre
def is_call_closing(text: str) -> str | None:
    text_norm = normalize(text)

    for phrase in CLOSING_PHRASES:
        if phrase in text_norm:
            return phrase

    return None