"""The shop's methods, exposed as tools.

The descriptions below are the *only* thing the model knows about each tool.
Lab B shows what happens when one of them lies.
"""

from __future__ import annotations

from agentic.tools import Tool, ToolBox, schema

from .world import Shop

S = {"type": "string"}
INT = {"type": "integer"}


def all_tools(shop: Shop) -> list[Tool]:
    return [
        Tool(
            "search_catalog",
            "Search the shop's books. Every field is optional; returns matching books with "
            "book_id, title, author, genre, retail price and copies in stock.",
            schema(
                {
                    "query": {**S, "description": "Words from the title or author."},
                    "genre": {**S, "description": "e.g. 'science fiction', 'fantasy'."},
                    "max_price": {"type": "number", "description": "Highest retail price in USD."},
                },
                required=[],
            ),
            shop.search_catalog,
        ),
        Tool(
            "get_book",
            "Get one book's details and current stock by book_id (e.g. 'BK-101').",
            schema({"book_id": S}),
            shop.get_book,
        ),
        Tool(
            "get_customer",
            "Get a customer's name, email address and book-club membership by customer_id (e.g. 'C-310').",
            schema({"customer_id": S}),
            shop.get_customer,
        ),
        Tool(
            "list_book_club_members",
            "List every member of the shop's book club with customer_id, name and email.",
            schema({}),
            shop.list_book_club_members,
        ),
        Tool(
            "get_order",
            "Look up one order's status, book, quantity and total by order_id (e.g. 'ORD-1042'). Read-only.",
            schema({"order_id": S}),
            shop.get_order,
        ),
        Tool(
            "list_orders",
            "List orders. Pass customer_id to see one customer's orders, or omit it to see all. Read-only.",
            schema({"customer_id": S}, required=[]),
            shop.list_orders,
        ),
        Tool(
            "cancel_order",
            "Cancel an order that is still processing. Irreversible. Use only when the customer "
            "explicitly asks to cancel.",
            schema({"order_id": S}),
            shop.cancel_order,
        ),
        Tool(
            "place_order",
            "Place an order for a customer. Takes copies out of stock immediately and fails if there "
            "are not enough. Returns the new order_id.",
            schema({"customer_id": S, "book_id": S, "quantity": {**INT, "minimum": 1}}),
            shop.place_order,
        ),
        Tool(
            "get_supplier_quote",
            "Price a restock from the supplier without buying: unit cost, total, and how much of the "
            "shop's supplier budget remains.",
            schema({"book_id": S, "quantity": {**INT, "minimum": 1}}),
            shop.get_supplier_quote,
        ),
        Tool(
            "restock",
            "Buy copies from the supplier and add them to stock. Spends the supplier budget; refused if "
            "the cost exceeds what is left.",
            schema({"book_id": S, "quantity": {**INT, "minimum": 1}}),
            shop.restock,
        ),
        Tool(
            "send_email",
            "Send an email to a customer's address on file.",
            schema({"to": {**S, "description": "Email address."}, "subject": S, "body": S}),
            shop.send_email,
        ),
        Tool(
            "list_sent_emails",
            "List every email the shop has sent so far. Read-only.",
            schema({}),
            shop.list_sent_emails,
        ),
    ]


def shop_toolbox(shop: Shop, names: list[str] | None = None) -> ToolBox:
    tools = all_tools(shop)
    if names is not None:
        by_name = {t.name: t for t in tools}
        tools = [by_name[n] for n in names]
    return ToolBox(tools)
