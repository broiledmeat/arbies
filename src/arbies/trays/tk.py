from __future__ import annotations
import asyncio
import tkinter
from PIL import Image, ImageTk
from . import Tray
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from arbies.drawing.geometry import Box
    from arbies.manager import Manager


class TkTray(Tray):
    def __init__(self, manager: Manager):
        super().__init__(manager)

        self._supports_partial_serve = True

        self._window: Optional[tkinter.Tk] = None
        self._canvas: Optional[tkinter.Canvas] = None

    async def startup(self):
        self._window = tkinter.Tk()
        self._window.geometry(f'{self._manager.size[0]}x{self._manager.size[1]}')
        self._canvas = tkinter.Canvas(self._window, width=self._manager.size[0], height=self._manager.size[1])
        self._canvas.pack()
        self._window.update()

    async def shutdown(self):
        await asyncio.sleep(5)
        self._window.destroy()

    async def serve(self, image: Image.Image, updated_boxes: Optional[list[Box]] = None):
        print(updated_boxes)

        tk_image = ImageTk.PhotoImage(image)
        self._canvas.create_image(0, 0, image=tk_image, anchor=tkinter.NW)
        self._window.update()
