from msagui.view.steps_view import MultiCorrectionsDialog

class StepsController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        
    def open(self):
        print("Opening steps dialog...")
        """Open dialog to input multiple corrections and factors."""
        self.dialog = MultiCorrectionsDialog(self.view.root, self.model.get_steps())
        self.dialog.save_button.config(command=self.close)
        # print(dialog.results)
        # print(dialog.steps)
        
    def close(self):
        print("[Close] Saving steps and closing dialog...")
        """Collect all steps and close dialog."""
        steps = []
        for row in self.dialog.step_rows:
            _, keyword, operation, keyword2, value, output_key, _, _, _ = row
            step = {
                "keyword1": keyword.get().strip(),
                "operation": operation.get().strip(),
                "keyword2": keyword2.get().strip(),
                "value": value.get().strip(),
                "output_key": output_key.get().strip()
            }
            if step["keyword1"] and step["operation"] and step["output_key"]:
                steps.append(step)
        self.dialog.destroy()
        print("Collected steps:", steps)
        self.model.steps.set_steps(steps)