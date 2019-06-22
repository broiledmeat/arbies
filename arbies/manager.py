import os
from PIL import Image
from typing import Dict, Tuple, List


class Manager:
    _size: Tuple[int, int] = [640, 384]

    def __init__(self):
        from arbies.workers import Worker

        self.workers: List[Worker] = []
        self._update_worker_images: Dict[Worker, Image.Image] = {}
        self._image = Image.new('1', self._size, 1)

    def render_once(self):
        for worker in self.workers:
            worker.render()

        for worker, image in self._update_worker_images.items():
            self._image.paste(image, worker.position)

        path = os.path.abspath(f'./out.png')
        self._image.save(path, 'PNG')

    def update_worker_image(self, worker, image: Image.Image):
        self._update_worker_images[worker] = image

