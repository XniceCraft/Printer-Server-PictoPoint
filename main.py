"""
Main program
"""

# pylint: disable=no-member, protected-access
import os
import sys
from typing import Literal, List
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from escpos.printer import Win32Raw
from PIL import Image
from pydantic import BaseModel
from config_parser import Config

payment_method_str = {"cash": "Cash", "e-wallet": "E-Wallet"}


def format_rupiah(amount: int) -> str:
    """
    Format ke rupiah

    Parameters
    ----------
    amount : int
        Jumlah

    Returns
    -------
    str
        Formatted string in Rupiah currency format
    """
    return f"Rp{amount:,.0f}".replace(",", ".")


def create_justify_string(left: str, right: str, max_char_row: int) -> str:
    """
    Justify between two strings in a row

    Parameters
    ----------
    left : str
        Left string to be displayed
    right : str
        Right string to be displayed
    max_char_row : int
        Max characters in a row

    Returns
    -------
    str
        Justified string with left and right components
    """
    right_len = len(right)
    left_max_len = max_char_row - right_len
    if len(left) > left_max_len:
        left = left[:left_max_len]
    return f"{left:<{left_max_len}}{right}"


def asset(path: str) -> str:
    """
    Get the correct path for an asset file

    Parameters
    ----------
    path : str
        Relative path to the asset
    Returns
    -------
    str
        Full path to the asset file
    """
    try:
        base_path = sys._MEIPASS  # type: ignore
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, path)


def get_image(image_width: int, path: str) -> Image.Image:
    """
    Handle logo image

    Parameters
    ----------
    path : str
        Image path
    image_width : int
        Width to resize the image to

    Returns
    -------
    Image.Image
        Resized and converted image ready for printing
    """
    image = Image.open(path)
    w_percent = image_width / float(image.size[0])
    h_size = int((float(image.size[1]) * float(w_percent)))
    resized_image = image.resize((image_width, h_size))
    return resized_image.convert("1")


class Transaction(BaseModel):
    """
    Represent Transaction Model

    Attributes
    ----------
    cashier : str
        Name of the cashier
    payment_method : Literal["cash", "e-wallet"]
        Method of payment used
    paid_amount : int
        Amount paid by customer
    change : int
        Change given back to customer
    paid_at : str
        Timestamp of payment
    """

    cashier: str
    payment_method: Literal["cash", "e-wallet"]
    paid_amount: int
    change: int
    paid_at: str


class OrderItem(BaseModel):
    """
    Represent OrderItem model

    Attributes
    ----------
    name : str
        Name of the ordered item
    price : int
        Price per unit of the item
    quantity : int
        Quantity of items ordered
    """

    name: str
    price: int
    quantity: int


class Order(BaseModel):
    """
    Represent Order model

    Attributes
    ----------
    order_id : int
        Unique identifier for the order
    subtotal : int
        Subtotal amount before handling fees
    total : int
        Total amount including handling fees
    transaction : Transaction
        Transaction details for the order
    items : List[OrderItem]
        List of items in the order
    """

    order_id: int
    subtotal: int
    total: int
    transaction: Transaction
    items: List[OrderItem]


class OrderNumber(BaseModel):
    """
    Represent OrderNumber model

    Attributes
    ----------
    order_id : int
        Unique identifier for the order
    """

    order_id: int


app = FastAPI()
config = Config.load()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origin,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


@app.post("/print_receipt")
async def print_receipt(order: Order, printer_id: int):
    """
    Print the receipt

    Parameters
    ----------
    order : Order
        Order data to be printed
    printer_id : int
        ID of the printer to use

    Returns
    -------
    JSONResponse
        Success or error message

    Raises
    ------
    HTTPException
        If printer_id is invalid
    """
    if printer_id < 1 or len(config.printers) < printer_id:
        raise HTTPException(status_code=422, detail="Printer id isn't valid")

    printer = Win32Raw(config.printers[printer_id - 1].printer_name)
    try:
        max_char_row = config.printers[printer_id - 1].profile["max_char_row"]
        image_width = config.printers[printer_id - 1].profile["image_width"]

        printer.image(get_image(image_width, asset("assets/Picto 7.png")), center=True)
        printer.set_with_default(align="left", bold=False)
        printer.textln("-" * max_char_row)

        for i in range(3):
            printer.text("No. Pesanan: ")
            printer.set(bold=True)
            printer.textln(f"{order.order_id}")

            printer.set(bold=False)
            printer.textln(f"Waktu: {order.transaction.paid_at}")
            printer.textln(f"Kasir: {order.transaction.cashier}")

            printer.textln("-" * max_char_row)
            printer.textln()

            printer.set(bold=False)
            for item in order.items:
                name_qty = f"{item.name} x{item.quantity}"
                total = format_rupiah(item.price * item.quantity)
                printer.textln(create_justify_string(name_qty, total, max_char_row))

            printer.textln()

            printer.textln("-" * max_char_row)
            printer.textln(
                create_justify_string(
                    "Subtotal: ", format_rupiah(order.subtotal), max_char_row
                )
            )

            printer.textln(
                create_justify_string(
                    "Biaya Penanganan: ",
                    format_rupiah(order.total - order.subtotal),
                    max_char_row,
                )
            )

            printer.textln("-" * max_char_row)
            printer.set(bold=True)
            printer.textln(
                create_justify_string(
                    "Total: ", format_rupiah(order.total), max_char_row
                )
            )
            printer.textln("-" * max_char_row)

            printer.set(bold=False)
            printer.textln(
                create_justify_string(
                    "Metode Bayar: ",
                    payment_method_str[order.transaction.payment_method],
                    max_char_row,
                )
            )
            printer.textln(
                create_justify_string(
                    "Bayar: ",
                    format_rupiah(order.transaction.paid_amount),
                    max_char_row,
                )
            )

            if order.transaction.payment_method == "cash":
                printer.textln(
                    create_justify_string(
                        "Kembalian: ",
                        format_rupiah(order.transaction.change),
                        max_char_row,
                    )
                )

            printer.textln("-" * max_char_row)

            printer.set(align="center")
            printer.textln("Terima kasih!")

            if i == 0:
                printer.textln("\n")
                printer.textln("Scan QR di bawah untuk melihat AR")
                printer.textln()
                printer.image(get_image(image_width, asset("assets/AR QR.png")), center=True)
                printer.set_with_default(align="center", bold=False)

            printer.cut()

            printer.close()
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, 500)

    return JSONResponse({"message": "Struk berhasil dibuat"}, 201)


@app.post("/print_number")
async def print_number(order: OrderNumber, printer_id: int):
    """
    Print the order number

    Parameters
    ----------
    order : OrderNumber
        Order number data to be printed
    printer_id : int
        ID of the printer to use

    Returns
    -------
    JSONResponse
        Success or error message

    Raises
    ------
    HTTPException
        If printer_id is invalid
    """
    if printer_id < 1 or len(config.printers) < printer_id:
        raise HTTPException(status_code=422, detail="Printer id isn't valid")

    printer = Win32Raw(config.printers[printer_id - 1].printer_name)
    try:
        image_width = config.printers[printer_id - 1].profile["image_width"]

        printer.image(get_image(image_width, asset("assets/Picto 7.png")), center=True)
        printer.textln()

        printer.set_with_default(
            align="center", double_width=True, double_height=True, bold=True
        )
        printer.textln(f"{order.order_id}")
        printer.textln()

        printer.set_with_default(align="center")
        printer.textln("Harap bawa ke kasir!")
        printer.cut()

        printer.close()
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, 500)

    return JSONResponse({"message": "Struk berhasil dibuat"}, 201)


if __name__ == "__main__":
    uvicorn.run(app, host=config.host, port=config.port)
