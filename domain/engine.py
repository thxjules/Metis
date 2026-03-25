# domain/engine.p
import re
import unicodedata

RISK_THRESHOLD = 5
INTEREST_THRESHOLD = 10

INTEREST_PHRASES = {
    "interesante":3,
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
    "joder": 5, 
    "pendejo": 5,
}

AGGRESSION_PHRASES = {
    "no me joda": 5, 
    "hijo de": 5,
    "vayase a la": 5, 
    "quitese": 5, 
    "no sea":5 , 
    "callese": 5,
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
def calculate_risk_delta(text_window: list[str]) -> tuple[int, int]:
    text = normalize(" ".join(text_window))
    risk_delta = 0
    interest_delta = 0

    for phrase, weight in RISK_PHRASES.items():
        if re.search(rf"\b{phrase}\b", text):
            risk_delta += weight

    for phrase, weight in INTEREST_PHRASES.items():
        if phrase == "me interesa" and re.search(r"\bno\s+me\s+interesa\b", text):
            continue
            
        if re.search(rf"\b{phrase}\b", text):
            interest_delta += abs(weight)

    return risk_delta, interest_delta


#cierre por hostilidad
def detect_extreme_hostility(text: str) -> tuple[str, int] | None:
    text_norm = normalize(text)
    for phrase in INSULT_PHRASES.keys():
        if re.search(rf"\b{phrase}\b", text_norm):
            return ("insult", INSULT_PHRASES[phrase])
    for phrase in AGGRESSION_PHRASES.keys():
        if re.search(rf"\b{phrase}\b", text_norm):
            return ("aggression", AGGRESSION_PHRASES[phrase])
    for phrase in REFUSAL_PHRASES.keys():
        if re.search(rf"\b{phrase}\b", text_norm):
            return ("refusal", REFUSAL_PHRASES[phrase])
    return None

# SOLO detecta cierre
def is_call_closing(text: str) -> str | None:
    text_norm = normalize(text)

    for phrase in CLOSING_PHRASES:
        if phrase in text_norm:
            return phrase

    return None