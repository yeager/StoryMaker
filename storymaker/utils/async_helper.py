"""Helpers for running async operations without blocking the GTK main loop."""

import threading
from functools import wraps

from gi.repository import GLib


def run_in_thread(callback, error_callback=None):
    """Decorator that runs a function in a background thread.

    Results are dispatched back to the GTK main loop via GLib.idle_add.

    Usage:
        @run_in_thread(on_result, on_error)
        def fetch_data():
            return some_blocking_call()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def thread_target():
                try:
                    result = func(*args, **kwargs)
                    if callback:
                        GLib.idle_add(callback, result)
                except Exception as e:
                    if error_callback:
                        GLib.idle_add(error_callback, e)
            thread = threading.Thread(target=thread_target, daemon=True)
            thread.start()
            return thread
        return wrapper
    return decorator


def idle_add(func, *args):
    """Schedule a function to run on the main GTK thread."""
    GLib.idle_add(func, *args)


def run_async(func, callback, error_callback=None, *args, **kwargs):
    """Run func in a thread, call callback with result on main thread."""
    def thread_target():
        try:
            result = func(*args, **kwargs)
            GLib.idle_add(callback, result)
        except Exception as e:
            if error_callback:
                GLib.idle_add(error_callback, e)
    thread = threading.Thread(target=thread_target, daemon=True)
    thread.start()
    return thread
