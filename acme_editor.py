"""
ACME Travels — local visit data editor.

Downloads the latest acme-travels.json from GitHub, lets you tick/untick
who has visited each country in a scrollable grid, and saves your edits
to a local file of your choosing. Committing that file back to GitHub is
a manual step, left up to you (e.g. via GitHub Desktop, VS Code, or git).

Requires only the Python standard library — no pip installs needed.
Run with:  python acme_editor.py
"""

import json
import urllib.request
import tkinter as tk
from tkinter import filedialog, messagebox

GITHUB_JSON_URL = "https://raw.githubusercontent.com/footsen/ACMETravels/main/docs/acme-travels.json"
PEOPLE = ["chris", "maggie", "allyson", "edward"]
PEOPLE_LABELS = ["Chris", "Maggie", "Allyson", "Edward"]


class AcmeEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ACME Travels — Edit Visit Data")
        self.geometry("720x680")

        self.visits = []       # source of truth, original array order preserved
        self.row_widgets = []  # (frame, name_lower) per row, for search filtering
        self.dirty = False

        self._build_ui()
        self.after(100, self.load_data)  # load after window is shown

    # ---------- UI construction ----------

    def _build_ui(self):
        toolbar = tk.Frame(self, padx=8, pady=8)
        toolbar.pack(fill="x")

        tk.Label(toolbar, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.apply_filter())
        tk.Entry(toolbar, textvariable=self.search_var, width=28).pack(side="left", padx=(4, 12))

        self.status_label = tk.Label(toolbar, text="", fg="#b45309", font=("Segoe UI", 9, "bold"))
        self.status_label.pack(side="left")

        tk.Button(toolbar, text="Save As...", command=self.save_as,
                  bg="#2d7d46", fg="white", padx=10).pack(side="right", padx=4)
        tk.Button(toolbar, text="Reload from GitHub", command=self.load_data).pack(side="right", padx=4)

        header = tk.Frame(self, padx=8)
        header.pack(fill="x")
        tk.Label(header, text="Country", width=36, anchor="w",
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        for col, label in enumerate(PEOPLE_LABELS, start=1):
            tk.Label(header, text=label, width=8, anchor="center",
                     font=("Segoe UI", 9, "bold")).grid(row=0, column=col)

        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=8, pady=(4, 4))

        self.canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.rows_frame = tk.Frame(self.canvas)

        self.rows_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.rows_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self.row_count_label = tk.Label(self, text="", anchor="w", padx=8, fg="#666")
        self.row_count_label.pack(fill="x")

    # ---------- data loading ----------

    def load_data(self):
        try:
            with urllib.request.urlopen(GITHUB_JSON_URL, timeout=10) as resp:
                self.visits = json.loads(resp.read().decode("utf-8"))
            self.dirty = False
            self.status_label.config(text="")
            self._build_rows()
        except Exception as e:
            open_local = messagebox.askyesno(
                "Couldn't reach GitHub",
                f"Couldn't download the latest data from GitHub:\n{e}\n\n"
                "Open a local acme-travels.json file instead?"
            )
            if open_local:
                path = filedialog.askopenfilename(
                    title="Select acme-travels.json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
                )
                if path:
                    with open(path, encoding="utf-8") as f:
                        self.visits = json.load(f)
                    self.dirty = False
                    self._build_rows()

    # ---------- grid rendering ----------

    def _build_rows(self):
        for w in self.rows_frame.winfo_children():
            w.destroy()
        self.row_widgets = []

        # Display alphabetically for easy browsing, but each checkbox stays tied
        # to its original index in self.visits so the saved file's row order
        # doesn't shuffle (keeps future diffs clean when you commit).
        order = sorted(range(len(self.visits)), key=lambda idx: self.visits[idx]["name"])

        for display_row, i in enumerate(order):
            v = self.visits[i]
            row = tk.Frame(self.rows_frame)
            row.grid(row=display_row, column=0, sticky="w")

            name_text = f'{v["name"]}  ({v["status"]})'
            tk.Label(row, text=name_text, width=36, anchor="w").grid(row=0, column=0, sticky="w")

            for col, person in enumerate(PEOPLE, start=1):
                var = tk.BooleanVar(value=bool(v.get(person, False)))
                cb = tk.Checkbutton(
                    row, variable=var, width=6,
                    command=lambda idx=i, person=person, var=var: self.on_toggle(idx, person, var)
                )
                cb.grid(row=0, column=col)

            self.row_widgets.append((row, v["name"].lower()))

        self.apply_filter()

    def on_toggle(self, i, person, var):
        self.visits[i][person] = var.get()
        self.dirty = True
        self.status_label.config(text="Unsaved changes — remember to Save As!")

    def apply_filter(self):
        query = self.search_var.get().strip().lower()
        visible = 0
        for row, name_lower in self.row_widgets:
            if not query or query in name_lower:
                row.grid()
                visible += 1
            else:
                row.grid_remove()
        self.row_count_label.config(text=f"{visible} of {len(self.visits)} shown")
        self.canvas.yview_moveto(0)

    # ---------- saving ----------

    def save_as(self):
        if not self.visits:
            messagebox.showwarning("Nothing to save", "No data is loaded yet.")
            return
        path = filedialog.asksaveasfilename(
            title="Save acme-travels.json",
            defaultextension=".json",
            initialfile="acme-travels.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.visits, f, indent=2, ensure_ascii=False)
        self.dirty = False
        self.status_label.config(text="")
        messagebox.showinfo("Saved", f"Saved to:\n{path}\n\nDon't forget to commit this to GitHub.")


if __name__ == "__main__":
    app = AcmeEditor()
    app.mainloop()
