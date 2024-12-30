import json
import time
from hashlib import sha1

CLIENT_VERSION = "2.20220311.01.00"


def safely_get_value_from_key(*args, default=None):
    obj = args[0]
    keys = args[1:]

    for key in keys:
        try:
            obj = obj[key]
        except Exception:
            return default

    return obj

def parse_count_text(text: str) -> int:
    """
    Convierte un texto como '1.7 K', '3.5 M' o '10' a un número entero.
    
    Args:
        text (str): El texto a convertir.

    Returns:
        int: El valor numérico convertido.
    """
    text = text.replace("\xa0", "").strip()  # Eliminar caracteres especiales como '\xa0'

    if 'K' in text:  # Miles
        return int(float(text.replace('K', '')) * 1000)
    elif 'M' in text:  # Millones
        return int(float(text.replace('M', '')) * 1000000)
    elif 'B' in text:  # Billones (opcional)
        return int(float(text.replace('B', '')) * 1000000000)
    else:
        return int(text)  # Si es un número entero normal


def safely_pop_value_from_key(*args):
    obj = args[0]
    keys = args[1:-1]

    for key in keys:
        try:
            obj = obj[key]
        except Exception:
            return None

    pop_key = args[-1]

    if pop_key in obj:
        obj.pop(pop_key)


def search_key(key, data, current_key=[]):
    found = []

    if type(data).__name__ == "dict":
        keys = list(data.keys())
    elif type(data).__name__ == "list":
        keys = list(range(len(data)))
    else:
        return []

    if key in keys:
        found.append((current_key + [key], data[key]))
        keys.remove(key)

    for k in keys:
        found += search_key(key, data[k], current_key=current_key + [k])

    return found


def save_object_to_file(obj, path):
    with open(path, "w") as f:
        f.write(json.dumps(obj, indent=4))


def get_auth_header(sapisid):
    timestring = str(int(time.time()))
    return f"SAPISIDHASH {timestring}_" + sha1(" ".join([timestring, sapisid, "https://www.youtube.com"]).encode()).hexdigest()
