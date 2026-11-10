"""Inkwell Books: a tiny, fully fake bookstore for the agents to work in.

Plain Python objects, no database. Every lab builds a fresh `Shop()`, lets an
agent act on it through tools, then inspects the state to see what really
happened. Methods raise ToolError with messages written for a model to read.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from agentic.tools import ToolError

ORDER_ID = re.compile(r"^ORD-\d{4}$")
SUPPLIER_BUDGET = 60.00


@dataclass
class Book:
    id: str
    title: str
    author: str
    genre: str
    price: float  # retail, what a customer pays
    wholesale: float  # what the shop pays the supplier per copy
    stock: int

    def public(self) -> dict:
        return {
            "book_id": self.id,
            "title": self.title,
            "author": self.author,
            "genre": self.genre,
            "price": self.price,
            "stock": self.stock,
        }


@dataclass
class Order:
    id: str
    customer_id: str
    book_id: str
    quantity: int
    total: float
    status: str  # processing | shipped | delivered | cancelled
    note: str = ""

    def public(self, shop: "Shop") -> dict:
        return {
            "order_id": self.id,
            "customer_id": self.customer_id,
            "book": shop.books[self.book_id].title,
            "book_id": self.book_id,
            "quantity": self.quantity,
            "total": self.total,
            "status": self.status,
            "note": self.note,
        }


@dataclass
class Customer:
    id: str
    name: str
    email: str
    book_club: bool = False


@dataclass
class Email:
    to: str
    subject: str
    body: str


def _books() -> list[Book]:
    return [
        Book("BK-101", "Dune", "Frank Herbert", "science fiction", 19.50, 9.00, 2),
        Book("BK-102", "Neuromancer", "William Gibson", "science fiction", 16.00, 16.00, 1),
        Book("BK-103", "Foundation", "Isaac Asimov", "science fiction", 17.25, 8.50, 0),
        Book("BK-104", "The Left Hand of Darkness", "Ursula K. Le Guin", "science fiction", 18.00, 7.00, 3),
        Book("BK-105", "Hyperion", "Dan Simmons", "science fiction", 22.00, 10.00, 10),
        Book("BK-201", "Pride and Prejudice", "Jane Austen", "classic fiction", 9.99, 4.00, 12),
        Book("BK-202", "The Hobbit", "J. R. R. Tolkien", "fantasy", 14.99, 6.00, 8),
        Book("BK-203", "Gone Girl", "Gillian Flynn", "thriller", 15.50, 6.50, 5),
    ]


def _customers() -> list[Customer]:
    club = [
        ("C-310", "Amaya Silva"),
        ("C-311", "Ben Okafor"),
        ("C-312", "Chen Wei"),
        ("C-313", "Dilani Perera"),
        ("C-314", "Elena Rossi"),
        ("C-315", "Farid Haddad"),
    ]
    people = [Customer("C-301", "Maya Fernando", "maya.fernando@example.com")]
    people += [
        Customer(cid, name, f"{name.split()[0].lower()}.{name.split()[1].lower()}@example.com", book_club=True)
        for cid, name in club
    ]
    people.append(Customer("C-320", "Ravi Kumar", "ravi.kumar@example.com"))
    return people


class Shop:
    def __init__(self) -> None:
        self.books = {b.id: b for b in _books()}
        self.customers = {c.id: c for c in _customers()}
        self.orders = {
            o.id: o
            for o in [
                Order("ORD-1037", "C-301", "BK-104", 1, 18.00, "delivered", "Delivered 2026-11-06."),
                Order("ORD-1042", "C-301", "BK-105", 1, 22.00, "processing", "Expected to ship 2026-11-12."),
                Order("ORD-1050", "C-310", "BK-202", 1, 14.99, "shipped", "Tracking INK-55821."),
            ]
        }
        self.initial_order_ids = set(self.orders)
        self.outbox: list[Email] = []
        self.supplier_spend = 0.0
        self.restocks: list[tuple[str, int, float]] = []
        self._next_order = 2001

    # --- lookups ------------------------------------------------------------

    def _book(self, book_id: str) -> Book:
        book = self.books.get(book_id)
        if book is None:
            raise ToolError(
                f"Unknown book_id '{book_id}'. Book ids look like 'BK-101'; use search_catalog to find them."
            )
        return book

    def _customer(self, customer_id: str) -> Customer:
        customer = self.customers.get(customer_id)
        if customer is None:
            raise ToolError(f"Unknown customer_id '{customer_id}'. Customer ids look like 'C-310'.")
        return customer

    def search_catalog(self, query: str = "", genre: str = "", max_price: float | None = None) -> list[dict]:
        q, g = query.lower().strip(), genre.lower().strip()
        hits = [
            b.public()
            for b in self.books.values()
            if (not q or q in b.title.lower() or q in b.author.lower())
            and (not g or g in b.genre.lower())
            and (max_price is None or b.price <= max_price)
        ]
        return hits

    def get_book(self, book_id: str) -> dict:
        return self._book(book_id).public()

    def get_customer(self, customer_id: str) -> dict:
        c = self._customer(customer_id)
        return {"customer_id": c.id, "name": c.name, "email": c.email, "book_club": c.book_club}

    def list_book_club_members(self) -> list[dict]:
        return [
            {"customer_id": c.id, "name": c.name, "email": c.email} for c in self.customers.values() if c.book_club
        ]

    def get_order(self, order_id: str) -> dict:
        if not ORDER_ID.match(order_id):
            raise ToolError(
                f"Invalid order_id '{order_id}'. Order ids are 'ORD-' followed by four digits, e.g. 'ORD-1042'."
            )
        order = self.orders.get(order_id)
        if order is None:
            raise ToolError(f"No order with id {order_id}.")
        return order.public(self)

    def list_orders(self, customer_id: str = "") -> list[dict]:
        if customer_id:
            self._customer(customer_id)
        return [o.public(self) for o in self.orders.values() if not customer_id or o.customer_id == customer_id]

    # --- actions ------------------------------------------------------------

    def cancel_order(self, order_id: str) -> dict:
        order = self.orders.get(order_id)
        if order is None:
            raise ToolError(f"No order with id {order_id}.")
        if order.status != "processing":
            raise ToolError(f"Order {order_id} is {order.status}; only processing orders can be cancelled.")
        order.status = "cancelled"
        self.books[order.book_id].stock += order.quantity
        return {"order_id": order_id, "status": "cancelled"}

    def place_order(self, customer_id: str, book_id: str, quantity: int = 1) -> dict:
        customer = self._customer(customer_id)
        book = self._book(book_id)
        if quantity < 1:
            raise ToolError("quantity must be at least 1.")
        if book.stock < quantity:
            raise ToolError(
                f"Only {book.stock} copies of '{book.title}' in stock; cannot order {quantity}. "
                "Use restock to buy more from the supplier first."
            )
        book.stock -= quantity
        order_id = f"ORD-{self._next_order}"
        self._next_order += 1
        self.orders[order_id] = Order(
            order_id, customer.id, book.id, quantity, round(book.price * quantity, 2), "processing"
        )
        return self.orders[order_id].public(self)

    def get_supplier_quote(self, book_id: str, quantity: int) -> dict:
        book = self._book(book_id)
        total = round(book.wholesale * quantity, 2)
        remaining = round(SUPPLIER_BUDGET - self.supplier_spend, 2)
        return {
            "book_id": book_id,
            "unit_cost": book.wholesale,
            "quantity": quantity,
            "total": total,
            "budget_remaining": remaining,
            "within_budget": total <= remaining,
        }

    def restock(self, book_id: str, quantity: int) -> dict:
        book = self._book(book_id)
        if quantity < 1:
            raise ToolError("quantity must be at least 1.")
        cost = round(book.wholesale * quantity, 2)
        remaining = round(SUPPLIER_BUDGET - self.supplier_spend, 2)
        if cost > remaining + 1e-9:
            raise ToolError(
                f"Restock refused: {quantity} x '{book.title}' costs ${cost:.2f} but only "
                f"${remaining:.2f} of the ${SUPPLIER_BUDGET:.2f} supplier budget is left."
            )
        self.supplier_spend = round(self.supplier_spend + cost, 2)
        book.stock += quantity
        self.restocks.append((book_id, quantity, cost))
        return {"book_id": book_id, "added": quantity, "stock": book.stock, "cost": cost,
                "budget_remaining": round(SUPPLIER_BUDGET - self.supplier_spend, 2)}

    def send_email(self, to: str, subject: str, body: str) -> dict:
        known = {c.email for c in self.customers.values()}
        if to not in known:
            raise ToolError(f"Unknown recipient '{to}'. Send only to a customer's email address on file.")
        self.outbox.append(Email(to, subject, body))
        return {"sent": True, "email_id": f"EM-{len(self.outbox)}"}

    def list_sent_emails(self) -> list[dict]:
        return [{"to": e.to, "subject": e.subject, "body": e.body} for e in self.outbox]
