from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel

from fastapi.responses import HTMLResponse # make it prettier and use html

app = FastAPI()


class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <html>
        <head>
            <title>My Cool App</title>
        </head>
        <body style="font-family:Arial; text-align:center; margin-top:50px;">
            <h1 style="color:blue;">Goodbye, World! 👋</h1>
            <p>Thanks for visiting!</p>
        </body>
    </html>
    """
