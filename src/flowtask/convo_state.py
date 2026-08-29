"""Estado de conversación en curso, por (platform, chat_id).

ponytail: en memoria. Si el proceso reinicia a mitad de un /proyecto, el usuario
lo reinicia. Un flujo dura segundos; no vale una tabla.
"""
_state: dict[tuple[str, str], dict] = {}


def get(platform: str, chat_id) -> dict | None:
    return _state.get((platform, str(chat_id)))


def set(platform: str, chat_id, data: dict) -> None:
    _state[(platform, str(chat_id))] = data


def clear(platform: str, chat_id) -> None:
    _state.pop((platform, str(chat_id)), None)
