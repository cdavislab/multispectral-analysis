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