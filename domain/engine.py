# domain/engine.py
import re
import unicodedata

RISK_THRESHOLD = 5
INTEREST_THRESHOLD = 10

INTEREST_PHRASES = {
    "interesante": 3,
    "me gusta": 2,
    "me interesa": 3,
    "eso suena bien": 1,
    "es justo lo que necesito": 3,
    "es lo que busco": 3,
    "exactamente lo que necesito": 3,
    "me parece bien": 2,
    "perfecto": 2,
    "genial": 2,
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

INSULT_PHRASES = {
    "idiota": 5,
    "estupido": 5,
    "imbecil": 5,
    "inutil": 5,
    "mierda": 5,
    "pendejo": 5,
}
REFUSAL_PHRASES = {
    "no me llame mas": 5,
    "no quiero hablar": 3,
    "ya le dije que no": 3,
    "deje de llamarme": 5,
    "no quiero esta oferta": 2,
    "no quiero esta informacion": 2,
    "saquenme de esta lista": 5,
}

AGGRESSION_REGEX = re.compile(
    r"\b(no me joda|quitese|callese|hijo de (?:puta|perra)|vayase a la (?:mierda|porra|chingada))\b"
)

CLOSING_REGEX = re.compile(
    r"\b(adios|hasta luego|chao|nos vemos|espero la informacion|llamame luego|gracias por tu tiempo|gracias por la informacion|gracias por tu ayuda)\b"
)


def normalize(text: str) -> str:
    text = text.lower()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^\w\s]", "", text)


def calculate_risk_delta(text_window: list[str]) -> tuple[int, int]:
    text = normalize(" ".join(text_window))

    risk_delta = sum(
        weight
        for phrase, weight in RISK_PHRASES.items()
        if re.search(rf"\b{phrase}\b", text)
    )

    interest_delta = sum(
        weight
        for phrase, weight in INTEREST_PHRASES.items()
        if not (phrase == "me interesa" and "no me interesa" in text)
        and re.search(rf"\b{phrase}\b", text)
    )

    return risk_delta, interest_delta


def detect_extreme_hostility(text: str) -> tuple[str, int] | None:
    text_norm = normalize(text)

    for phrase, weight in INSULT_PHRASES.items():
        if re.search(rf"\b{phrase}\b", text_norm):
            return ("insult", weight)

    if AGGRESSION_REGEX.search(text_norm):
        return ("aggression", 5)

    for phrase, weight in REFUSAL_PHRASES.items():
        if re.search(rf"\b{phrase}\b", text_norm):
            return ("refusal", weight)

    return None


def is_call_closing(text: str) -> str | None:
    match = CLOSING_REGEX.search(normalize(text))
    return match.group(0) if match else None
