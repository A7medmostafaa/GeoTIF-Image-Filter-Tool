# GeoTIF Image Filter Tool

A modern Python desktop tool for filtering and copying GeoTIFF (`.tif` / `.tiff`) images based on file names found in an Excel or CSV file.

Supports:
- Excel & CSV input (with or without header)
- Recursive folder scanning
- Auto-copying matched images
- Progress tracking
- Live logging (last 10 events)
- Dark/Light mode switch
- Clean modern UI (CustomTkinter)

---

## 🚀 Features

- Read Excel/CSV file and target a specific column.
- “No Header” mode (A, B, C...).
- Recursively search inside all subfolders for `.tif` / `.tiff` images.
- Progress bar with real-time updates.
- Log window showing last 10 operations.
- Saves settings automatically.
- Dark/Light mode toggle.
- Modern UI with improved spacing & window scaling.

---

## 📦 Installation

Install all required libraries:

```bash
pip install -r requirements.txt
```

or install them manually:

```bash
pip install pandas
pip install customtkinter
pip install sv-ttk
pip install openpyxl
```

---

## ▶️ Running the Tool

```
python ImageFilterTool.py
```

---

## 🛠️ Build EXE (Optional)

To build a standalone EXE:

```bash
pyinstaller --onefile --noconsole ImageFilterTool.py
```

Your EXE will appear inside the **dist** folder.

---

## 📁 Project Structure

```
GeoTIF Image Filter Tool/
│── ImageFilterTool.py
│── README.md
│── LICENSE
│── requirements.txt
│── .gitignore
│── assets/   (optional icons/screenshots)
```

---

## 📜 License

This project is licensed under the MIT License.  
See **LICENSE** file for details.

