from collections import defaultdict

_THREAD_STORE: dict[str, list[dict]] = defaultdict(list)


def load_thread_context(thread_id: str | None, limit: int = 12) -> str:
    if not thread_id:
        return ""

    messages = _THREAD_STORE.get(thread_id, [])[-limit:]
    return "\n".join(f"{m['role']}: {m['content']}" for m in messages)


def save_message(thread_id: str | None, role: str, content: str) -> None:
    if not thread_id:
        return

    _THREAD_STORE[thread_id].append(
        {
            "role": role,
            "content": content,
        }
    )