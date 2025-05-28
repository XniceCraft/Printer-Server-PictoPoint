"""
Main program
"""

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
    """
    return f"Rp{amount:,.0f}".replace(",", ".")


def create_justify_string(left: str, right: str, max_char_row: int) -> str:
    """
    Justify between two strings in a row

    Parameters
    ----------
    left : str
        Left string
    right : str
        Right string
    max_char_row : int
        Max characters in a row

    Returns
    -------
    str
    """
    right_len = len(right)
    left_max_len = max_char_row - right_len
    if len(left) > left_max_len:
        left = left[:left_max_len]
    return f"{left:<{left_max_len}}{right}"


def get_image(image_width: int) -> Image.Image:
    """
    Handle logo image

    Parameters
    ----------
    image_width : int
        Logo

    Returns
    -------
    Image.Image
    """
    image = Image.open("assets/Picto 7.png")
    w_percent = image_width / float(image.size[0])
    h_size = int((float(image.size[1]) * float(w_percent)))
    resized_image = image.resize((image_width, h_size))
    return resized_image.convert("1")


class Transaction(BaseModel):
    """
    Represent Transaction Model
    """

    cashier: str
    payment_method: Literal["cash", "e-wallet"]
    paid_amount: int
    change: int
    paid_at: str


class OrderItem(BaseModel):
    """
    Represent OrderItem model
    """

    name: str
    price: int
    quantity: int


class Order(BaseModel):
    """
    Represent Order model
    """

    order_id: int
    subtotal: int
    total: int
    transaction: Transaction
    items: List[OrderItem]


class OrderNumber(BaseModel):
    """
    Represent OrderNumber model
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
    """
    if printer_id < 1 or len(config.printers) < printer_id:
        raise HTTPException(status_code=422, detail="Printer id isn't valid")

    printer = Win32Raw(config.printers[printer_id - 1].printer_name)
    try:
        max_char_row = config.printers[printer_id - 1].profile["max_char_row"]
        image_width = config.printers[printer_id - 1].profile["image_width"]

        printer.image(get_image(image_width), center=True)
        printer.set_with_default(align="left", bold=False)
        printer.textln("-" * max_char_row)

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
                "Biaya Penanganan: ", format_rupiah(order.total - order.subtotal), max_char_row
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
        printer.cut()

        printer.close()
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, 500)

    return JSONResponse({"message": "Struk berhasil dibuat"}, 201)


@app.post("/print_number")
async def print_number(order: OrderNumber, printer_id: int):
    """
    Print the receipt
    """
    if printer_id < 1 or len(config.printers) < printer_id:
        raise HTTPException(status_code=422, detail="Printer id isn't valid")

    printer = Win32Raw(config.printers[printer_id - 1].printer_name)
    try:
        image_width = config.printers[printer_id - 1].profile["image_width"]

        printer.image(get_image(image_width), center=True)
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
