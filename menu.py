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
                text_bg=(0.2, 0.2, 0.2, 1),
                text_fg=(0.4, 0.4, 1, 1),
                relief=DDG.GROOVE,
                frameColor=(0.2, 0.2, 0.2, 1),
                text_shadow=(0.9, 0.9, 0.9, 1),
            )
            for text, (func, (x, z)) in reversed(list(menu_items.items()))

        ]
        self.hide()

    def show(self):
        for button in self.buttons:
            button.show()

    def hide(self):
        for button in self.buttons:
            button.hide()

    def dispatch(self, func):
        func()
        self.hide()
