"""
Main program
"""

from typing import List
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from escpos.printer import Win32Raw
from pydantic import BaseModel
from config_parser import Config


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


class OrderItem(BaseModel):
    """
    Representation of OrderItem model
    """

    name: str
    price: int
    quantity: int


class Order(BaseModel):
    """
    Representation of Order model
    """

    order_id: int
    items: List[OrderItem]


class OrderNumber(BaseModel):
    """
    Representation of OrderNumber model
    """

    order_id: int


app = FastAPI()
config = Config.load()
printer = Win32Raw(printer_name="POS-58")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origin,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


@app.post("/print_receipt")
async def print_receipt(order: Order):
    """
    Print the receipt
    """
    try:
        printer.set(align="center", bold=True, width=3, height=3, custom_size=True)
        printer.textln("PictoPoint\n")

        printer.set_with_default(align="left", bold=False)
        printer.text("No. Pesanan: ")
        printer.set(bold=True)
        printer.textln(f"{order.order_id}")
        printer.textln()

        printer.set(bold=False)
        for item in order.items:
            name_qty = f"{item.name} x{item.quantity}"
            total = format_rupiah(item.price * item.quantity)

            if len(name_qty) > 20:
                name_qty = name_qty[:20]

            line = f"{name_qty:<20}{total:>12}\n"
            printer.text(line)

        printer.textln()

        total_all = sum(item.price * item.quantity for item in order.items)
        printer.textln("-" * 32)
        printer.set(bold=True)
        printer.text(f"{'Total':<20}{format_rupiah(total_all):>12}\n")
        printer.set(bold=False)
        printer.textln("-" * 32)

        printer.set(align="center")
        printer.textln("Terima kasih!")
        printer.cut()

        printer.close()
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, 500)

    return JSONResponse({"message": "Struk berhasil dibuat"}, 201)


@app.post("/print_number")
async def print_number(order: OrderNumber):
    """
    Print the receipt
    """
    try:
        printer.set(align="center", bold=True, width=3, height=3, custom_size=True)
        printer.textln("PictoPoint")
        printer.textln()

        printer.set(width=8, height=8, custom_size=True)
        printer.textln(f"{order.order_id}")
        printer.textln()

        printer.set(
            width=4, height=4, custom_size=True
        )
        printer.textln("Harap bawa nomor ke kasir!")
        printer.cut()

        printer.close()
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, 500)

    return JSONResponse({"message": "Struk berhasil dibuat"}, 201)


if __name__ == "__main__":
    uvicorn.run(app, host=config.host, port=config.port)
