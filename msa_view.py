import tkinter as tk
import tkinter.font as tkFont
from pathlib import Path

# View class to handle the GUI components
class MultispectralView:
    def __init__(self, root):
        self.root = root
        self.setup_ui()

    # Function to setup the GUI layout and components
    def setup_ui(self):
        self.root.title("Multispectral Analysis")
        width = 800
        height = 500
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.root.geometry(alignstr)
        self.root.resizable(True, True)

        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(3, weight=1)
        self.root.columnconfigure(3, weight=1)
        self.root.rowconfigure(5, weight=1)
        self.root.columnconfigure(5, weight=1)

        self.build_file_viewer()
        self.build_image_viewer()
        self.build_user_buttons()
        self.build_wavenumber_inputs()
        self.build_menubar()
        self.set_defaults()

    def build_file_viewer(self):
        frm = tk.Frame(self.root)
        frm.grid(row=0, column=0, rowspan=7, columnspan=2, sticky="nsew", padx=2, pady=2)
        scrollbar = tk.Scrollbar(frm, orient="horizontal")
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.ListBox_1 = tk.Listbox(frm, xscrollcommand=scrollbar.set, borderwidth="1px", fg="#333333",
                                    justify="center", font=('Times', 10))
        self.ListBox_1.pack(expand=True, fill=tk.BOTH)
        scrollbar.config(command=self.ListBox_1.xview)

    def build_image_viewer(self):
        self.img_panel = tk.Label(self.root)
        self.panel_img = ""
        self.img_panel.grid(row=0, column=2, rowspan=9, columnspan=4, sticky="nsew", padx=2, pady=2)

    def build_user_buttons(self):
        self.Button_Add = tk.Button(self.root, bg="#e9e9ed", fg="#000000", justify="center",
                                    font=('Times', 10), text="Add Files")
        self.Button_Add.grid(row=7, column=0, rowspan=1, columnspan=2, sticky="nsew", padx=2)

        self.Button_Delete = tk.Button(self.root, bg="#e9e9ed", fg="#000000", justify="center",
                                       font=('Times', 10), text="Delete Files")
        self.Button_Delete.grid(row=8, column=0, rowspan=1, columnspan=2, sticky="nsew", padx=2)

        self.Button_Analyze = tk.Button(self.root, bg="#e9e9ed", fg="#000000", justify="center",
                                        font=('Times', 10), text="Analyze")
        self.Button_Analyze.grid(row=9, column=0, rowspan=2, columnspan=2, sticky="nsew", padx=2)

        self.Button_Filename = tk.Button(self.root, bg="#e9e9ed", fg="#000000",
                                         justify="center", font=('Times', 10),
                                         text="Filename")
        self.Button_Filename.grid(row=9, column=2, rowspan=1, columnspan=4, sticky="nsew", padx=2)

        self.Button_Statistics = tk.Button(self.root, bg="#e9e9ed", fg="#000000",
                                           justify="center", font=('Times', 10),
                                           text="Statistics")
        self.Button_Statistics.grid(row=10, column=2, rowspan=1, columnspan=4, sticky="nsew", padx=2)

    def build_wavenumber_inputs(self):
        # Natural Wavenumber
        nw_text = tk.Label(self.root, bg="#e9e9ed", fg="#333333",
                           justify="left", font=('Times', 10),
                           text="Natural (cm-1):")
        nw_text.grid(row=11, column=0, rowspan=1, columnspan=1, sticky="nsew")
        
        nw = tk.StringVar()
        self.nw_entry = tk.Entry(self.root, textvariable=nw, font=('Times', 10, 'normal'))
        self.nw_entry.grid(row=11, column=1, rowspan=1, columnspan=1, sticky="nsew")

        # Natural Correction Wavenumber
        ncw_text = tk.Label(self.root, bg="#e9e9ed", fg="#333333", justify="left",
                            font=tkFont.Font(family='Times', size=10),
                            text="Natural Correction (cm-1):")
        ncw_text.grid(row=11, column=2, rowspan=1, columnspan=1, sticky="nsew")

        ncw = tk.StringVar()
        self.ncw_entry = tk.Entry(self.root, textvariable=ncw, font=('Times', 10, 'normal'))
        self.ncw_entry.grid(row=11, column=3, rowspan=1, columnspan=1, sticky="nsew")

        # Natural Correction Factor
        ncf_text = tk.Label(self.root, bg="#e9e9ed", fg="#333333", justify="left",
                            font=tkFont.Font(family='Times', size=10),
                            text="Natural Correction Factor:")
        ncf_text.grid(row=11, column=4, rowspan=1, columnspan=1, sticky="nsew")

        natural_cf = tk.StringVar()
        self.ncf_entry = tk.Entry(self.root, textvariable=natural_cf,
                                  font=('Times', 10, 'normal'))
        self.ncf_entry.grid(row=11, column=5, rowspan=1, columnspan=1, sticky="nsew")

        # Label Wavenumber
        lw_text = tk.Label(self.root, bg="#e9e9ed", fg="#333333", justify="left",
                           font=tkFont.Font(family='Times', size=10),
                           text="Label (cm-1):")
        lw_text.grid(row=12, column=0, rowspan=1, columnspan=1, sticky="nsew")

        label_wavenum = tk.StringVar()
        self.lw_entry = tk.Entry(self.root, textvariable=label_wavenum,
                                 font=('Times', 10, 'normal'))
        self.lw_entry.grid(row=12, column=1, rowspan=1, columnspan=1, sticky="nsew")

        # Label Correction Wavenumber
        lcw_text = tk.Label(self.root, bg="#e9e9ed", fg="#333333", justify="left",
                            font=tkFont.Font(family='Times', size=10),
                            text="Label Correction (cm-1):")
        lcw_text.grid(row=12, column=2, rowspan=1, columnspan=1, sticky="nsew")

        lcw = tk.StringVar()
        self.lcw_entry = tk.Entry(self.root, textvariable=lcw,
                                  font=('Times', 10, 'normal'))
        self.lcw_entry.grid(row=12, column=3, rowspan=1, columnspan=1, sticky="nsew")

        # Label Correction Factor
        lcf_text = tk.Label(self.root, bg="#e9e9ed", fg="#333333", justify="left",
                            font=tkFont.Font(family='Times', size=10),
                            text="Label Correction Factor:")
        lcf_text.grid(row=12, column=4, rowspan=1, columnspan=1, sticky="nsew")

        lcf = tk.StringVar()
        self.lcf_entry = tk.Entry(self.root, textvariable=lcf,
                                  font=('Times', 10, 'normal'))
        self.lcf_entry.grid(row=12, column=5, rowspan=1, columnspan=1, sticky="nsew")

        # Threshold
        threshold_text = tk.Label(self.root, bg="#e9e9ed", fg="#333333", justify="left",
                                  font=tkFont.Font(family='Times', size=10),
                                  text="Threshold")
        threshold_text.grid(row=13, column=4, rowspan=1, columnspan=1, sticky="nsew")

        threshold = tk.StringVar()
        self.threshold_entry = tk.Entry(self.root, textvariable=threshold,
                                        font=('Times', 10, 'normal'))
        self.threshold_entry.grid(row=13, column=5, rowspan=1, columnspan=1, sticky="nsew")

        # Export Folder
        Button_ExportFolder = tk.Button(self.root, bg="#e9e9ed", fg="#333333", justify="center",
                                        font=tkFont.Font(family='Times', size=10),
                                        text="Export Folder:")
        Button_ExportFolder.grid(row=13, column=0, rowspan=1, columnspan=1, sticky="nsew")
        self.Button_ExportFolder = Button_ExportFolder

        self.Listbox_ExportFolder = tk.Label(self.root, bg="#e9e9ed", fg="#333333",
                                             justify="left", font=('Times', 10),
                                             text="Export Folder Path")
        self.Listbox_ExportFolder.grid(row=13, column=1, rowspan=1, columnspan=3, sticky="nsew")

    def build_menubar(self):
        self.menubar = tk.Menu(self.root)
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.settings_menu.add_command(label="Open Config")
        self.settings_menu.add_command(label="Save Config")
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="Export Statistics")
        self.file_menu.add_command(label="Export File List")
        self.file_menu.add_command(label="Import File List")
        self.root.config(menu=self.menubar)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.menubar.add_cascade(label="Settings", menu=self.settings_menu)

    def set_defaults(self):
        self.nw_entry.insert(0, "1744")
        self.lw_entry.insert(0, "1703")
        self.ncw_entry.insert(0, "1655")
        self.lcw_entry.insert(0, "1655")
        self.ncf_entry.insert(0, ".31")
        self.lcf_entry.insert(0, ".61")
        self.threshold_entry.insert(0, "0.15")

