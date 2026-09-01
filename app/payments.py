"""
Mock Razorpay checkout (Phase 8).

This is a SIMULATION. It does not talk to Razorpay, it does not move
money, and no real card details are ever entered or stored - the user
picks from a fixed list of well-known test cards, so there is no field
a real card number could even go into.

The shapes returned here (order_/pay_ ids, amounts in paise, a
captured/failed status) deliberately mirror Razorpay's real API, so
swapping in the live SDK later is a small, contained change: replace
create_order and capture_payment with the razorpay client calls and
everything downstream - the database schema, the UI, the recorded
history - keeps working unchanged.

Per the brief: test mode only, and a simulated payment is never
presented to the user as a real one.
"""

import random
import string
from dataclasses import dataclass

MOCK_MODE = True  # Never flip this on without swapping in the real SDK below.


@dataclass(frozen=True)
class TestCard:
    label: str
    number: str
    outcome: str  # "captured" or "failed"
    note: str


# Mirrors Razorpay's documented test cards. These are publicly published
# dummy numbers that only work in test mode - they are not real cards.
TEST_CARDS = [
    TestCard(
        label="Success card",
        number="4111 1111 1111 1111",
        outcome="captured",
        note="Payment goes through.",
    ),
    TestCard(
        label="Failure card",
        number="4000 0000 0000 0002",
        outcome="failed",
        note="Payment is declined - use this to test the error path.",
    ),
]


def _mock_id(prefix: str) -> str:
    suffix = "".join(random.choices(string.ascii_letters + string.digits, k=14))
    return f"{prefix}_{suffix}"


def create_order(amount_rupees: float, receipt: str) -> dict:
    """Create a simulated Razorpay order. Amount is in paise, as Razorpay does it."""
    return {
        "id": _mock_id("order"),
        "amount": int(round(amount_rupees * 100)),
        "amount_rupees": amount_rupees,
        "currency": "INR",
        "receipt": receipt,
        "status": "created",
        "simulated": True,
    }


def capture_payment(order: dict, card: TestCard) -> dict:
    """Simulate the checkout result for a given test card.

    Returns a payment dict either way - a declined card is a normal
    outcome to be recorded and shown, not an exception to be handled.
    """
    captured = card.outcome == "captured"
    return {
        "id": _mock_id("pay"),
        "order_id": order["id"],
        "amount": order["amount"],
        "amount_rupees": order["amount_rupees"],
        "currency": order["currency"],
        "status": "captured" if captured else "failed",
        "method": "card",
        "card_last4": card.number.replace(" ", "")[-4:],
        "error_description": None if captured else "Payment was declined by the test issuer.",
        "simulated": True,
    }
