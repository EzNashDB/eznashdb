import threading

from django.db import close_old_connections


def run_in_background(func, *args, **kwargs):
    """
    Run func in a daemon thread so callers (e.g. request handlers) never block on it.

    Centralizes DB connection cleanup here so call sites don't each need to
    remember it: a thread gets its own DB connection, and Django only closes
    those automatically at the end of a request - never for a thread it doesn't
    know about.
    """

    def _run():
        try:
            func(*args, **kwargs)
        finally:
            close_old_connections()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread
