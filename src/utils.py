from typing import Dict, Any


def safe_get(dictionary: Dict[str, Any], *keys, default=None) -> Any:
    """
    Safely get nested key values from a dictionary.
    """
    for key in keys:
        try:
            dictionary = dictionary[key]
        except KeyError:
            return default
    return dictionary or default
