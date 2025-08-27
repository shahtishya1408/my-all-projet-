# This script provides a GUI for converting various file formats including TXT, DOCX, XLSX, CSV, PDF, and PY to their respective formats.
# It uses Tkinter for the GUI, pandas for data manipulation, and PyMuPDF for PDF handling.
# It also includes error handling and user prompts for file selection and conversion.
#     """Handle deposit action."""
#    
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import pandas as pd
import fitz  # PyMuPDF
from docx import Document
from reportlab.pdfgen import canvas
import pyinstaller
# Text to PDF Conversion
def txt_to_pdf(input_file, output_file):
    c = canvas.Canvas(output_file)
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    y = 800
    for line in lines:
        c.drawString(100, y, line.strip())
        y -= 20
    c.save()

# Docx to PDF Conversion
def docx_to_pdf(input_file, output_file):
    doc = Document(input_file)
    c = canvas.Canvas(output_file)
    y = 800
    for para in doc.paragraphs:
        c.drawString(100, y, para.text)
        y -= 20
    c.save()

#bat to EXE Conversion
def bat_to_exe(input_file, output_file):
    messagebox.showinfo("Info", "Use 'pyinstaller --onefile yourfile.bat' in CMD to convert .bat to .exe")
# Note: The above function is a placeholder as converting .bat to .exe is not straightforward in Python.
                                                                                                                                                                                                                                                                                                    

# Python to EXE Conversion
def py_to_exe(input_file, output_file):
    messagebox.showinfo("Info", "Use 'pyinstaller --onefile yourfile.py' in CMD to convert .py to .exe")
# Note: The above function is a placeholder as converting .py to .exe is not straightforward in Python.

# DOCX to PDF Conversion

    
# Excel to CSV Conversion
def excel_to_csv(input_file, output_file):
    df = pd.read_excel(input_file)
    df.to_csv(output_file, index=False)

# CSV to Excel Conversion
def csv_to_excel(input_file, output_file):
    df = pd.read_csv(input_file)
    df.to_excel(output_file, index=False)

# CSV to JSON Conversion
def csv_to_json(input_file, output_file):
    df = pd.read_csv(input_file)
    df.to_json(output_file, orient="records", indent=4)

# PDF to Text Conversion
def pdf_to_text(input_file, output_file):
    pdf_doc = fitz.open(input_file)
    text = "\n".join([page.get_text() for page in pdf_doc])
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text)

# Main Conversion Handler
def convert_file():
    file_path = filedialog.askopenfilename(title="Select a File")
    if not file_path:
        return
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    conversion_options = {
        ".txt": ["PDF"],
        ".docx": ["PDF"],
        ".xlsx": ["CSV"],
        ".csv": ["Excel", "JSON"],
        ".pdf": ["Text"],
        ".py": ["EXE"]  # Optional: For Py to Exe
    }
    
    if file_ext not in conversion_options:
        messagebox.showerror("Error", "Unsupported file format!")
        return
    
    output_format = conversion_options[file_ext]
    output_format_choice = tk.StringVar(value=output_format[0])
    
    output_window = tk.Toplevel(root)
    output_window.title("Choose Output Format")
    
    tk.Label(output_window, text="Select Output Format:", font=("Arial", 10)).pack(pady=5)
    
    for option in output_format:
        tk.Radiobutton(output_window, text=option, variable=output_format_choice, value=option).pack(anchor="w")
    
    def process_conversion():
        selected_format = output_format_choice.get()
        
        if file_ext == ".py" and selected_format == "EXE":
            messagebox.showinfo("Info", "Use 'pyinstaller --onefile yourfile.py' in CMD to convert .py to .exe")
            output_window.destroy()
            return
        
        output_file = filedialog.asksaveasfilename(defaultextension=f".{selected_format.lower()}")
        if not output_file:
            return
        
        try:
            if file_ext == ".txt" and selected_format == "PDF":
                txt_to_pdf(file_path, output_file)
            elif file_ext == ".docx" and selected_format == "PDF":
                docx_to_pdf(file_path, output_file)
            elif file_ext == ".xlsx" and selected_format == "CSV":
                excel_to_csv(file_path, output_file)
            elif file_ext == ".csv" and selected_format == "Excel":
                csv_to_excel(file_path, output_file)
            elif file_ext == ".csv" and selected_format == "JSON":
                csv_to_json(file_path, output_file)
            elif file_ext == ".pdf" and selected_format == "Text":
                pdf_to_text(file_path, output_file)
            
            messagebox.showinfo("Success", f"File converted successfully to:\n{output_file}")
            output_window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed:\n{e}")
    
    tk.Button(output_window, text="Convert", command=process_conversion).pack(pady=10)

# GUI Setup
root = tk.Tk()
root.title("File Format Converter")
root.geometry("400x200")

tk.Label(root, text="Select a file to convert:", font=("Arial", 12)).pack(pady=10)
tk.Button(root, text="Select File", command=convert_file, font=("Arial", 12)).pack(pady=10)

root.mainloop()