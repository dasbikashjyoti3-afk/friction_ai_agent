"""Retry transient Gemini errors (5xx / 429) a few times before giving up."""
import logging
import time

log = logging.getLogger(__name__)
TRANSIENT_NAMES = ("ServerError", "ConnectError", "RemoteProtocolError", "ReadTimeout")


def generate_with_retry(client, attempts: int = 3, **kwargs):
    for i in range(attempts):
        try:
            return client.models.generate_content(**kwargs)
        except Exception as e:
            code = getattr(e, "code", None)
            transient = type(e).__name__ in TRANSIENT_NAMES or code in (429, 500, 502, 503, 504)
            if not transient or i == attempts - 1:
                raise
            wait = 3 * (i + 1)
            log.warning("Gemini transient error (%s); retrying in %ss", type(e).__name__, wait)
            time.sleep(wait)
