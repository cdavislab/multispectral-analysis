# Main entry point for the Multispectral Analysis application.
# Initializes the MVC components and starts the Tkinter event loop.

from msagui.model.model import MultiSpectralModel
from msagui.model.logging_utils import configure_logging, get_log_file_path
from msagui.view.main_view import MultispectralView
from msagui.controller.main_controller import ControllerDispatcher
import tkinter as tk
import logging

def setup_logging():
    configure_logging(level=logging.INFO)

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Application startup initiated")
    logger.info("Active log file: %s", get_log_file_path())
    root = tk.Tk()
    model = MultiSpectralModel()
    view = MultispectralView(root)
    controller = ControllerDispatcher(model, view)
    root.mainloop()