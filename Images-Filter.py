# Images-Filter-Modern.py
# Requirements: customtkinter, pandas, openpyxl

import os
import shutil
import threading
import base64
import sys
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, PhotoImage
import customtkinter as ctk
import time

try:
    import winsound
    HAVE_WINSOUND = True
except Exception:
    HAVE_WINSOUND = False


APP_ICON_BASE64 = """
R0lGODlhEAAQAMQAAOR5Af/OAAAA/+jL0P/GgP/do//z5//SoP/UqP/38P/MgP/Xsv/NmP/Q
pf/imP/clP/58//Ytf/Gfv+fJ//txv/owf/Gf//Ys//17f/Ll/+aHf///////////yH/C05F
VFNDQVBFMi4wAwEAAAAh+QQJBgA/ACwAAAAAEAAQAAAFhiAljmRpaWk6y3M81gJg1gmY5XHm
Ow==
"""

def _load_icon_from_base64(b64string):
    try:
        data = base64.b64decode(b64string)
        return PhotoImage(data=data)
    except Exception:
        return None


def excel_col_to_index(col_name):
    col_name = str(col_name).upper().strip()
    index = 0
    for ch in col_name:
        if not ('A' <= ch <= 'Z'):
            raise ValueError("Invalid column letter")
        index = index * 26 + (ord(ch) - ord('A')) + 1
    return index - 1


def filter_and_copy_worker(excel_path, images_folder, output_folder, column_name, no_header,
                           progress_cb, log_cb, finished_cb):
    try:
        log_cb("Reading Excel/CSV file...")
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Excel file not found: {excel_path}")

        if excel_path.lower().endswith('.csv'):
            try:
                df = pd.read_csv(excel_path, encoding='utf-8', header=None if no_header else 'infer')
            except UnicodeDecodeError:
                df = pd.read_csv(excel_path, encoding='cp1256', header=None if no_header else 'infer')
        else:
            df = pd.read_excel(excel_path, header=None if no_header else 0, engine='openpyxl')

        if no_header:
            col_idx = excel_col_to_index(column_name)
            target_series = df.iloc[:, col_idx].astype(str).str.strip().dropna()
        else:
            cols_str = [str(c) for c in df.columns]
            if column_name not in df.columns and column_name not in cols_str:
                raise KeyError(f"Column '{column_name}' not found.")
            if column_name in df.columns:
                target_series = df[column_name].astype(str).str.strip().dropna()
            else:
                idx = cols_str.index(column_name)
                target_series = df.iloc[:, idx].astype(str).str.strip().dropna()

        base_names = set(os.path.splitext(str(x))[0] for x in target_series if str(x).strip())
        if not base_names:
            raise ValueError("Empty name list in the column")

        log_cb(f"Found {len(base_names)} names in Excel column.")

        if not os.path.exists(images_folder):
            raise FileNotFoundError(f"Images folder not found: {images_folder}")
        os.makedirs(output_folder, exist_ok=True)

        log_cb("Searching for matching .tif/.tiff files recursively...")
        matches = []
        total_tif = 0
        for dirpath, _, filenames in os.walk(images_folder):
            for fname in filenames:
                if fname.lower().endswith(('.tif', '.tiff')):
                    total_tif += 1
                    base = os.path.splitext(fname)[0]
                    if base in base_names:
                        # NEW: Calculate the relative directory path
                        relative_dir = os.path.relpath(dirpath, images_folder)
                        # NEW: Store the full source path, relative dir, and filename
                        matches.append((os.path.join(dirpath, fname), relative_dir, fname))

        total_to_copy = len(matches)
        log_cb(f"Total .tif/.tiff files: {total_tif}. Matching files: {total_to_copy}")

        if total_to_copy == 0:
            progress_cb(1.0, 0, 0)
            finished_cb(0, total_tif)
            return

        copied = 0
        # NEW: Unpack src, relative_dir, and fname
        for i, (src, relative_dir, fname) in enumerate(matches, start=1):
            try:
                # NEW: Create the new destination sub-directory
                # Handle the case where the file is in the root (relative_dir == '.')
                if relative_dir == ".":
                    new_dest_dir = output_folder
                else:
                    new_dest_dir = os.path.join(output_folder, relative_dir)
                
                # NEW: Create the full final destination path
                dest = os.path.join(new_dest_dir, fname)

                # NEW: Ensure the sub-directory structure exists
                os.makedirs(new_dest_dir, exist_ok=True)

                shutil.copy2(src, dest)
                copied += 1
                if relative_dir == ".":
                    log_cb(f"Copied {i}/{total_to_copy}: {fname} (to root)")
                else:
                    log_cb(f"Copied {i}/{total_to_copy}: {fname} (to {relative_dir})")
            except Exception as e:
                log_cb(f"Error copying {fname}: {e}")
            fraction = copied / total_to_copy
            progress_cb(fraction, copied, total_to_copy)

        log_cb("Process completed successfully.")
        finished_cb(copied, total_tif)

    except Exception as e:
        log_cb(f"Error: {e}")
        finished_cb(None, None)


class ImageFilterTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Image Filter Tool")
        self.geometry("950x600")
        self.resizable(False, False)

        try:
            icon = _load_icon_from_base64(APP_ICON_BASE64)
            if icon:
                self.iconphoto(True, icon)
        except Exception:
            pass

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.var_excel = ctk.StringVar()
        self.var_images = ctk.StringVar()
        self.var_output = ctk.StringVar()
        self.var_column = ctk.StringVar(value="Image Name")
        self.var_no_header = ctk.BooleanVar(value=False)
        self.var_dark_mode = ctk.BooleanVar(value=True)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(10, 4))

        title_lbl = ctk.CTkLabel(top, text="GeoTIF Toolkit", font=ctk.CTkFont(size=18, weight="bold"))
        title_lbl.pack(side="left")

        self.theme_switch = ctk.CTkSwitch(top, text="Dark Mode", variable=self.var_dark_mode, command=self.toggle_theme)
        self.theme_switch.pack(side="right")

        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=14, pady=6)

        lbl_excel = ctk.CTkLabel(form, text="Excel or CSV File:")
        lbl_excel.grid(row=0, column=0, sticky="w", padx=6, pady=8)
        self.entry_excel = ctk.CTkEntry(form, width=640, textvariable=self.var_excel)
        self.entry_excel.grid(row=0, column=1, padx=6, pady=8)
        btn_excel = ctk.CTkButton(form, text="Browse", width=90, command=self.browse_excel)
        btn_excel.grid(row=0, column=2, padx=6, pady=8)

        lbl_images = ctk.CTkLabel(form, text="Images Folder:")
        lbl_images.grid(row=1, column=0, sticky="w", padx=6, pady=8)
        self.entry_images = ctk.CTkEntry(form, width=640, textvariable=self.var_images)
        self.entry_images.grid(row=1, column=1, padx=6, pady=8)
        btn_images = ctk.CTkButton(form, text="Browse", width=90, command=self.browse_images)
        btn_images.grid(row=1, column=2, padx=6, pady=8)

        lbl_output = ctk.CTkLabel(form, text="Output Folder:")
        lbl_output.grid(row=2, column=0, sticky="w", padx=6, pady=8)
        self.entry_output = ctk.CTkEntry(form, width=640, textvariable=self.var_output)
        self.entry_output.grid(row=2, column=1, padx=6, pady=8)
        btn_output = ctk.CTkButton(form, text="Browse", width=90, command=self.browse_output)
        btn_output.grid(row=2, column=2, padx=6, pady=8)

        lbl_col = ctk.CTkLabel(form, text="Column Name:")
        lbl_col.grid(row=3, column=0, sticky="w", padx=6, pady=8)
        self.entry_column = ctk.CTkEntry(form, width=360, textvariable=self.var_column)
        self.entry_column.grid(row=3, column=1, sticky="w", padx=6, pady=8)
        self.chk_no_header = ctk.CTkCheckBox(form, text="No Header", variable=self.var_no_header, command=self._on_header_toggle)
        self.chk_no_header.grid(row=3, column=2, padx=6, pady=8)

        self.start_btn = ctk.CTkButton(self, text="Start Filtering", width=180, height=40, fg_color="#1E90FF", hover_color="#1670d1", command=self.start_filter)
        self.start_btn.pack(pady=(6, 12))

        bottom = ctk.CTkFrame(self)
        bottom.pack(fill="both", expand=True, padx=14, pady=(0,14))

        self.progress_label = ctk.CTkLabel(bottom, text="Progress: 0%")
        self.progress_label.pack(anchor="w", padx=8, pady=(8,4))

        self.progress = ctk.CTkProgressBar(bottom, width=900)
        self.progress.set(0.0)
        self.progress.pack(padx=8, pady=(0,8))

        self.status_label = ctk.CTkLabel(bottom, text="Status: Ready")
        self.status_label.pack(anchor="w", padx=8, pady=(0,8))

        self.log_text_lines = []
        self.logbox = ctk.CTkTextbox(bottom, width=920, height=220, corner_radius=6)
        self.logbox.configure(state="disabled")
        self.logbox.pack(padx=8, pady=(0,8))

    def toggle_theme(self):
        if self.var_dark_mode.get():
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def _on_header_toggle(self):
        if self.var_no_header.get():
            self.entry_column.delete(0, "end")
            self.entry_column.insert(0, "A")
        else:
            self.entry_column.delete(0, "end")
            self.entry_column.insert(0, "Image Name")

    def browse_excel(self):
        path = filedialog.askopenfilename(title="Select Excel or CSV", filetypes=[("Excel files", "*.xlsx *.xls *.xlsm"), ("CSV files", "*.csv")])
        if path:
            self.var_excel.set(path)
            self.add_log(f"Selected Excel file: {os.path.basename(path)}")

    def browse_images(self):
        path = filedialog.askdirectory(title="Select Images Folder")
        if path:
            self.var_images.set(path)
            self.add_log(f"Selected images folder: {path}")

    def browse_output(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.var_output.set(path)
            self.add_log(f"Selected output folder: {path}")

    def start_filter(self):
        excel_path = self.var_excel.get().strip()
        images_folder = self.var_images.get().strip()
        output_folder = self.var_output.get().strip()
        column_name = self.var_column.get().strip()
        no_header = self.var_no_header.get()

        if not all([excel_path, images_folder, output_folder, column_name]):
            messagebox.showerror("Missing Information", "Please fill in all fields before starting.")
            return

        self.start_btn.configure(state="disabled")
        self.status_label.configure(text="Status: Running...")
        self.add_log("🚀 Filtering started...")

        self.progress.set(0.0)
        self.progress_label.configure(text="Progress: 0%")

        worker_thread = threading.Thread(
            target=filter_and_copy_worker,
            args=(excel_path, images_folder, output_folder, column_name, no_header,
                  self._progress_callback, self._log_callback, self._finished_callback),
            daemon=True
        )
        worker_thread.start()

    def _progress_callback(self, fraction, current, total):
        def _update():
            frac = max(0.0, min(1.0, fraction or 0.0))
            self.progress.set(frac)
            pct = int(frac * 100)
            self.progress_label.configure(text=f"Progress: {pct}% ({current}/{total})")
            self.status_label.configure(text=f"Copying {current}/{total}")
        self.after(10, _update)

    def _log_callback(self, message):
        def _append():
            if len(self.log_text_lines) >= 10:
                self.log_text_lines.pop(0)
            self.log_text_lines.append(message)
            self.logbox.configure(state="normal")
            self.logbox.delete("1.0", "end")
            for ln in self.log_text_lines:
                self.logbox.insert("end", ln + "\n")
            self.logbox.see("end")
            self.logbox.configure(state="disabled")
        self.after(10, _append)

    def _finished_callback(self, copied_count, total_found):
        def _on_finish():
            self.start_btn.configure(state="normal")
            if copied_count is None:
                self.status_label.configure(text="Status: Finished with errors.")
                messagebox.showerror("Error", "Process finished with errors. Check the log.")
            else:
                self.status_label.configure(text="Status: Completed")
                self.add_log(f"✅ Completed. Copied {copied_count} files.")
                
                # --- NEW: Update progress bar *BEFORE* showing the dialog ---
                self.progress.set(1.0)
                self.progress_label.configure(text="Progress: 100%")

                if HAVE_WINSOUND:
                    try:
                        winsound.MessageBeep(winsound.MB_OK)
                    except Exception:
                        pass
                
                # --- NEW: Improved "Done" message ---
                messagebox.showinfo("Done", f"Copied {copied_count} files.\n"
                                          f"Total tif found: {total_found}\n\n"
                                          f"Files were copied to:\n{self.var_output.get()}\n"
                                          f"(Note: The original folder structure was preserved.)")
                
        self.after(10, _on_finish)

    def add_log(self, msg):
        self._log_callback(msg)


def main():
    app = ImageFilterTool()
    app.mainloop()


if __name__ == "__main__":
    main()