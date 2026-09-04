import os
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading

class NestedZipExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("Nested ZIP Extractor")
        self.root.geometry("620x520")
        self.root.minsize(500, 450)

        # Variables
        self.zip_path = tk.StringVar()
        self.dest_path = tk.StringVar()
        self.delete_zips = tk.BooleanVar(value=True)  # Default: delete zips
        self.is_extracting = False

        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = ttk.Label(main_frame, text="Nested ZIP Extractor", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(0, 15))

        # ZIP file selection
        zip_frame = ttk.LabelFrame(main_frame, text="ZIP File", padding="10")
        zip_frame.pack(fill=tk.X, pady=5)

        ttk.Entry(zip_frame, textvariable=self.zip_path, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(zip_frame, text="Browse...", command=self.browse_zip).pack(side=tk.RIGHT)

        # Destination folder
        dest_frame = ttk.LabelFrame(main_frame, text="Extract To", padding="10")
        dest_frame.pack(fill=tk.X, pady=5)

        ttk.Entry(dest_frame, textvariable=self.dest_path, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(dest_frame, text="Browse...", command=self.browse_dest).pack(side=tk.RIGHT)

        # Toggle switch for deleting ZIP files
        toggle_frame = ttk.Frame(main_frame)
        toggle_frame.pack(fill=tk.X, pady=12)

        self.delete_check = ttk.Checkbutton(
            toggle_frame,
            text="Delete ZIP files after extraction (including nested ones)",
            variable=self.delete_zips
        )
        self.delete_check.pack(anchor=tk.W)

        # Extract button
        self.extract_btn = ttk.Button(main_frame, text="Extract Nested ZIPs", command=self.start_extraction)
        self.extract_btn.pack(pady=10, ipadx=10, ipady=4)

        # Progress / Log area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="8")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, state="disabled", wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(8, 0))

    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")
        self.root.update_idletasks()

    def browse_zip(self):
        path = filedialog.askopenfilename(
            title="Select ZIP file",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        if path:
            self.zip_path.set(path)
            # Auto-suggest destination as the folder containing the zip
            if not self.dest_path.get():
                self.dest_path.set(os.path.dirname(path))

    def browse_dest(self):
        path = filedialog.askdirectory(title="Select destination folder")
        if path:
            self.dest_path.set(path)

    def start_extraction(self):
        if self.is_extracting:
            return

        zip_file = self.zip_path.get()
        dest = self.dest_path.get()

        if not zip_file:
            messagebox.showwarning("Missing ZIP", "Please select a ZIP file.")
            return
        if not dest:
            messagebox.showwarning("Missing Destination", "Please select a destination folder.")
            return
        if not os.path.isfile(zip_file):
            messagebox.showerror("Error", "Selected ZIP file does not exist.")
            return
        if not zipfile.is_zipfile(zip_file):
            messagebox.showerror("Error", "Selected file is not a valid ZIP archive.")
            return

        self.is_extracting = True
        self.extract_btn.configure(state="disabled")
        self.status_var.set("Extracting...")
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state="disabled")

        # Run extraction in a background thread so the GUI stays responsive
        thread = threading.Thread(target=self.extract_nested, args=(zip_file, dest), daemon=True)
        thread.start()

    def extract_nested(self, zip_file, to_folder):
        """Recursively extract nested ZIP files."""
        try:
            self.log(f"Starting extraction of: {os.path.basename(zip_file)}")
            self.log(f"Destination: {to_folder}")
            self.log("-" * 50)

            # Extract the main ZIP
            with zipfile.ZipFile(zip_file, 'r') as zf:
                zf.extractall(path=to_folder)
            self.log(f"✓ Extracted: {os.path.basename(zip_file)}")

            if self.delete_zips.get():
                try:
                    os.remove(zip_file)
                    self.log(f"  → Deleted: {os.path.basename(zip_file)}")
                except Exception as e:
                    self.log(f"  ⚠ Could not delete original ZIP: {e}")

            # Walk the destination and extract any nested ZIPs
            extracted_count = 1
            while True:
                found_zip = False
                for root, dirs, files in os.walk(to_folder):
                    for filename in files:
                        if filename.lower().endswith('.zip'):
                            found_zip = True
                            file_path = os.path.join(root, filename)
                            try:
                                self.log(f"Found nested ZIP: {filename}")
                                with zipfile.ZipFile(file_path, 'r') as zf:
                                    zf.extractall(path=root)
                                self.log(f"✓ Extracted nested: {filename}")
                                extracted_count += 1

                                if self.delete_zips.get():
                                    os.remove(file_path)
                                    self.log(f"  → Deleted: {filename}")
                            except Exception as e:
                                self.log(f"✗ Failed to extract {filename}: {e}")
                if not found_zip:
                    break

            self.log("-" * 50)
            self.log(f"Done! Extracted {extracted_count} ZIP archive(s).")
            self.status_var.set("Extraction completed successfully")
            messagebox.showinfo("Success", f"Extraction finished!\n\nExtracted {extracted_count} ZIP archive(s).")

        except Exception as e:
            self.log(f"✗ Error: {e}")
            self.status_var.set("Error occurred")
            messagebox.showerror("Error", f"Extraction failed:\n{e}")

        finally:
            self.is_extracting = False
            self.root.after(0, lambda: self.extract_btn.configure(state="normal"))

if __name__ == "__main__":
    root = tk.Tk()
    # Optional: use a modern theme if available
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    app = NestedZipExtractor(root)
    root.mainloop()