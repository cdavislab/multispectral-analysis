class StepsController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        
    def open_multi_corrections_dialog(self):
        """Open dialog to input multiple corrections and factors."""
        dialog = self.view.MultiCorrectionsDialog(self.view, self.model.get_steps())
        print(dialog.results)
        print(dialog.steps)
        if dialog.result is not None:
            # Store results for controller/model access
            self.model.set_steps(dialog.result)