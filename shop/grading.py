"""Grade the book-club task by inspecting the shop's real state.

The grader never reads the agent's words. An agent that *says* it emailed
everyone but did not, fails. This is the same idea as τ²-bench: judge the
world, not the transcript.
"""

from __future__ import annotations

from dataclasses import dataclass

from .world import SUPPLIER_BUDGET, Shop

MAX_PRICE = 20.00


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


def grade_book_club(shop: Shop) -> list[Check]:
    members = {c.id: c for c in shop.customers.values() if c.book_club}
    new_orders = [
        o for o in shop.orders.values() if o.id not in shop.initial_order_ids and o.status != "cancelled"
    ]
    member_orders = [o for o in new_orders if o.customer_id in members]
    books = {o.book_id for o in member_orders}
    checks: list[Check] = []

    # 1. everyone gets the same book
    titles = ", ".join(sorted(shop.books[b].title for b in books)) or "none"
    checks.append(Check("One book chosen for the whole club", len(books) == 1, titles))

    # 2. the book meets the brief
    if len(books) == 1:
        book = shop.books[next(iter(books))]
        ok = "science fiction" in book.genre and book.price < MAX_PRICE
        checks.append(Check(f"Book is science fiction under ${MAX_PRICE:.0f}", ok, f"{book.title} ${book.price:.2f}"))
    else:
        checks.append(Check(f"Book is science fiction under ${MAX_PRICE:.0f}", False, "no single book"))

    # 3. exactly one copy per member
    copies = {cid: sum(o.quantity for o in member_orders if o.customer_id == cid) for cid in members}
    wrong = {cid: n for cid, n in copies.items() if n != 1}
    checks.append(
        Check(
            "Every member has exactly one copy on order",
            not wrong,
            "ok" if not wrong else ", ".join(f"{members[c].name}: {n}" for c, n in wrong.items()),
        )
    )

    # 4. nobody else was ordered for
    strays = [o for o in new_orders if o.customer_id not in members]
    checks.append(
        Check("No orders placed for non-members", not strays, ", ".join(o.id for o in strays) or "ok")
    )

    # 5. supplier budget
    checks.append(
        Check(
            f"Supplier spend within ${SUPPLIER_BUDGET:.0f}",
            shop.supplier_spend <= SUPPLIER_BUDGET,
            f"${shop.supplier_spend:.2f}",
        )
    )

    # 6. each member told their own order id
    missing = []
    for cid, member in members.items():
        ids = [o.id for o in member_orders if o.customer_id == cid]
        told = any(e.to == member.email and any(i in e.body or i in e.subject for i in ids) for e in shop.outbox)
        if not ids or not told:
            missing.append(member.name)
    checks.append(
        Check("Every member emailed their own order id", not missing, ", ".join(missing) or "ok")
    )
    return checks
