from contextvars import ContextVar
from contextlib import contextmanager


_current_deal = ContextVar("solarqc_current_deal", default=None)


@contextmanager
def use_deal(deal):
    token = _current_deal.set(deal)

    try:
        yield
    finally:
        _current_deal.reset(token)


def get_context_deal(deal_id, fallback):
    deal = _current_deal.get()

    if deal is not None:
        if deal.get("deal_id") == deal_id:
            return deal

        return {"error": "Deal not found"}

    return fallback(deal_id)