# Main entry point for the Multispectral Analysis application.
# Initializes the MVC components and starts the Tkinter event loop.

from msagui.model.model import MultiSpectralModel
from msagui.view.main_view import MultispectralView
from msagui.controller.main_controller import ControllerDispatcher
import tkinter as tk
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    root = tk.Tk()
    model = MultiSpectralModel()
    view = MultispectralView(root)
    controller = ControllerDispatcher(model, view)
    root.mainloop()