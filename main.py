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

app = FastAPI()
config = Config.load()
printer = Win32Raw(printer_name='POS-58')

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_domain,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

@app.post('/print_receipt')
async def print_receipt(order: Order):
    """
    Print the receipt
    """
    try:
        printer.set(align='center', bold=True, width=2, height=2)
        printer.textln("PictoPoint\n")

        printer.set(align='left', bold=False, width=1, height=1)
        printer.text("No. Pesanan: ")
        printer.set(bold=True)
        printer.textln(str(order.order_id))
        printer.textln()

        printer.set(bold=False)
        for item in order.items:
            line = f"{item.name} x{item.quantity}".ljust(20)
            total = item.price * item.quantity
            line += f"{total:>8}\n"
            printer.text(line)

        printer.textln()
        printer.set(align='center')
        printer.textln("Terima kasih!")
        printer.cut()

        printer.close()
    except Exception as exc:
        return JSONResponse({'error': str(exc)}, 500)

    return JSONResponse({'message': 'Struk berhasil dibuat'}, 201)

if __name__ == "__main__":
    uvicorn.run('main:app', host=config.host, port=config.port, reload=True)
