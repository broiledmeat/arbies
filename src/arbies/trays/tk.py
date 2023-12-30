from __future__ import annotations
import asyncio
from asyncio.exceptions import CancelledError
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
        self._image = None
        self._loop_task: asyncio.Task | None = None
        self._is_destroying: bool = False

    async def startup(self):
        self._window = tkinter.Tk()
        self._window.bind('<KeyPress>', self._key_press)
        self._window.geometry(f'{self.size.x}x{self.size.y}')
        self._canvas = tkinter.Canvas(self._window, width=self.size.x, height=self.size.y)
        self._canvas.pack()
        self._loop_task = asyncio.create_task(self._update_loop())

    async def shutdown(self):
        await self._loop_task

    async def _serve_internal(self, image: Image.Image, updated_boxes: list[Box] | None = None):
        self._image = ImageTk.PhotoImage(image)
        self._canvas.create_image(0, 0, image=self._image, anchor=tkinter.NW)

    async def _update_loop(self):
        try:
            while not self._is_destroying:
                self._window.update_idletasks()
                self._window.update()
                await asyncio.sleep(0.2)
        except CancelledError:
            pass
        self._window.destroy()

    def _key_press(self, event):
        if event.keysym == 'Escape' or event.keysym == 'space':
            self._is_destroying = True
