from typing import Callable, Dict

from direct.gui.DirectButton import DirectButton


class Menu:
    def __init__(self, menu_items: Dict[str, Callable]):
        self.buttons = [
            DirectButton(
                text=text,
                command=self.dispatch,
                extraArgs=[func],
                pos=(0, 0, 2 * i / (1 + len(menu_items)) - 1),
                scale=(0.1, 1, 0.1)
            )
            for i, (text, func) in enumerate(reversed(list(menu_items.items())), start=1)
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
