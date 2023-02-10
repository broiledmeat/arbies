from __future__ import annotations
import asyncio
import tkinter
from PIL import Image, ImageTk
from arbies.drawing.geometry import Box
from arbies.manager import Manager
from arbies.trays import Tray


class TkTray(Tray):
    def __init__(self, manager: Manager, **kwargs):
        super().__init__(manager, **kwargs)

        self._window: tkinter.Tk | None = None
        self._canvas: tkinter.Canvas | None = None

    async def startup(self):
        self._window = tkinter.Tk()
        self._window.geometry(f'{self.size.x}x{self.size.y}')
        self._canvas = tkinter.Canvas(self._window, width=self.size.x, height=self.size.y)
        self._canvas.pack()
        self._window.update()

    async def shutdown(self):
        await asyncio.sleep(5)
        self._window.destroy()

    async def _serve_internal(self, image: Image.Image, updated_boxes: list[Box] | None = None):
        tk_image = ImageTk.PhotoImage(image)
        self._canvas.create_image(0, 0, image=tk_image, anchor=tkinter.NW)
        self._window.update()
