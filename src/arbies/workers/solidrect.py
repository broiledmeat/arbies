from PIL import Image
from arbies.workers import Worker


class SolidRectWorker(Worker):
    def render(self):
        image = Image.new('1', self.size, 0)
        self.serve(image)
