# Main entry point for the Multispectral Analysis application.
# Initializes the MVC components and starts the Tkinter event loop.

from msa_model import MultispectralModel
from msa_view import MultispectralView
from msa_controller import MultispectralController
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    model = MultispectralModel()
    view = MultispectralView(root)
    controller = MultispectralController(model, view)
    root.mainloop()