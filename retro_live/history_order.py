"""Stable linear partition of the bounded history, newest first within groups."""

DEFAULT_AVAILABLE_FIRST = True

def order_history(items, state, available_first=DEFAULT_AVAILABLE_FIRST):
    if not available_first:
        return tuple(reversed(items))
    groups = ([], [])
    for url in reversed(items):
        status = state(url)
        groups[0 if status == 'online' else 1].append(url)
    return tuple(groups[0] + groups[1])
