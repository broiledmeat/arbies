from __future__ import annotations
import asyncio
import re
from PIL import Image, ImageDraw
from arbies.drawing import HorizontalAlignment, VerticalAlignment
from arbies.drawing.font import aligned_wrapped_text
from arbies.manager import Manager
from arbies.workers import LoopIntervalWorker
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from arbies.workers.text.runs import Run


class TextWorker(LoopIntervalWorker):
    _parser_re = re.compile(r"({{|}}|{\w*(?:\.\w+|\[[^]]+])*(?:\|[^}]+)?})")

    def __init__(self, manager: Manager, **kwargs):
        from arbies.workers.text.runs.raw import Raw

        super().__init__(manager, **kwargs)

        self._runs: list[Run] = self._parse(kwargs.get('Text', ''))

        # If there are no variables, the text can never change, so the worker only needs to render once.
        if all(isinstance(chunk, Raw) for chunk in self._runs):
            self.render_loop = self.render_once

    async def _render_internal(self) -> Image.Image:
        image = Image.new('RGBA', self._size)
        draw = ImageDraw.Draw(image)

        text_tasks = [asyncio.create_task(chunk.render(self.manager)) for chunk in self._runs]
        texts = await asyncio.gather(*text_tasks)
        text = ''.join(texts)

        aligned_wrapped_text(draw,
                             self.font,
                             text,
                             self.font_fill,
                             self.size,
                             horizontal_alignment=HorizontalAlignment.LEFT,
                             vertical_alignment=VerticalAlignment.TOP)

        del draw
        return image

    @staticmethod
    def _parse(value: str) -> list[Run]:
        from arbies.workers.text.runs.raw import Raw

        named_types = TextWorker._get_named_run_types()
        runs: list[Run] = []

        for part in TextWorker._parser_re.split(value):
            if len(part) == 0:
                continue
            elif part == '{{':
                runs.append(Raw('{'))
            elif part == '}}':
                runs.append(Raw('}'))
            elif part[0] == '{' and part[-1] == '}':
                tokens = part[1:-1].split('|')
                name: str = tokens[0]
                params: list[str] = tokens[1:]
                class_ = named_types.get(name, None)

                if class_ is None:
                    runs.append(Raw(f'!{name}!'))
                else:
                    runs.append(class_(*params))
            else:
                runs.append(Raw(part))

        return runs

    _cached_named_run_types: dict[str, Type] = {}

    @staticmethod
    def _get_named_run_types() -> dict[str, Type]:
        if len(TextWorker._cached_named_run_types) > 0:
            return TextWorker._cached_named_run_types

        import importlib.util
        import inspect
        import pkgutil
        from arbies.workers.text import runs

        types = set()

        for module_info in pkgutil.walk_packages(runs.__path__, 'arbies.workers.text.runs.'):
            module = importlib.import_module(module_info.name)
            for _, member in inspect.getmembers(module):
                if (not inspect.isabstract(member) and
                        inspect.isclass(member) and
                        member != runs.Run and
                        issubclass(member, runs.Run) and
                        getattr(member, 'name', None) is not None):
                    types.add(member)

        TextWorker._cached_named_run_types = {
            type_.name: type_
            for type_ in types
        }

        return TextWorker._cached_named_run_types
