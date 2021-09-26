from typing import Callable, Dict, Tuple

from direct.gui.DirectButton import DirectButton
from direct.gui import DirectGuiGlobals as DDG


class Menu:
    def __init__(self, menu_items: Dict[str, Tuple[Callable, Tuple[float, float]]]):

        self.buttons = [
            DirectButton(
                text=text,
                command=self.dispatch,
                extraArgs=[func],
                pos=(x, 0, z),
                scale=(0.12, 1, 0.12),
                text_scale=(0.9, 0.9),
                text_bg=(0, 0.085, 0.125, 1),
                text_fg=(0, 0.7, 1, 1),
                relief=DDG.GROOVE,
                frameColor=(0, 0.35, 0.5, 1),
                text_shadow=(0, 0.0425, 0.0625, 1),
            )
            for text, (func, (x, z)) in reversed(list(menu_items.items()))

        ]

    def destroy(self):
        for button in self.buttons:
            button.destroy()

    def dispatch(self, func):
        func()
        self.destroy()
