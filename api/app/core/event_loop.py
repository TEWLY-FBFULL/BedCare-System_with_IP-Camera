import asyncio

_event_loop = None

def set_event_loop(loop):
    global _event_loop
    _event_loop = loop

def get_event_loop():
    return _event_loop