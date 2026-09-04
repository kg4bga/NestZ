import os
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading

# Drag & Drop support
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    print("tkinterdnd2 not installed. Drag & Drop disabled.")
    print("Install it with:  pip install tkinterdnd2")


class NestedZipExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("Nested ZIP Extractor")
        self.root.geometry("640x600")
        self.root.minsize(520, 520)

        # Variables
        self.zip_path = tk.StringVar()
        self.dest_path = tk.StringVar()
        self.delete_zips = tk.BooleanVar(value=True)
        self.is_extracting = False
        self.total_zips = 0
        self.processed_zips = 0

        self.create_widgets()
        self.setup_drag_and_drop()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = ttk.Label(main_frame, text="Nested ZIP Extractor", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(0, 8))

        # Drag & Drop hint
        if DND_AVAILABLE:
            hint = ttk.Label(main_frame, text="Drag & drop a ZIP file here", foreground="#555555")
            hint.pack(pady=(0, 10))
        else:
            hint = ttk.Label(main_frame, text="(Drag & Drop unavailable – install tkinterdnd2)", foreground="#aa0000")
            hint.pack(pady=(0, 10))

        # ZIP file selection
        zip_frame = ttk.LabelFrame(main_frame, text="ZIP File", padding="10")
        zip_frame.pack(fill=tk.X, pady=5)

        self.zip_entry = ttk.Entry(zip_frame, textvariable=self.zip_path, state="readonly")
        self.zip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(zip_frame, text="Browse...", command=self.browse_zip).pack(side=tk.RIGHT)

        # Destination folder
        dest_frame = ttk.LabelFrame(main_frame, text="Extract To", padding="10")
        dest_frame.pack(fill=tk.X, pady=5)

        ttk.Entry(dest_frame, textvariable=self.dest_path, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(dest_frame, text="Browse...", command=self.browse_dest).pack(side=tk.RIGHT)

        # Toggle
        toggle_frame = ttk.Frame(main_frame)
        toggle_frame.pack(fill=tk.X, pady=10)

        self.delete_check = ttk.Checkbutton(
            toggle_frame,
            text="Delete ZIP files after extraction (including nested ones)",
            variable=self.delete_zips
        )
        self.delete_check.pack(anchor=tk.W)

        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.pack(fill=tk.X, pady=8)

        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.pack(anchor=tk.W, pady=(0, 6))

        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X)

        # Extract button
        self.extract_btn = ttk.Button(main_frame, text="Extract Nested ZIPs", command=self.start_extraction)
        self.extract_btn.pack(pady=12, ipadx=12, ipady=5)

        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="8")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state="disabled", wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(8, 0))

    def setup_drag_and_drop(self):
        if not DND_AVAILABLE:
            return

        # Make the whole window accept drops
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

        # Also make the ZIP entry accept drops
        self.zip_entry.drop_target_register(DND_FILES)
        self.zip_entry.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        # event.data contains the dropped file path(s)
        files = self.root.tk.splitlist(event.data)

        if not files:
            return

        file_path = files[0]  # Take the first file

        # Clean up the path (sometimes has { } on Windows)
        file_path = file_path.strip("{}")

        if not file_path.lower().endswith(".zip"):
            messagebox.showwarning("Invalid file", "Please drop a .zip file.")
            return

        if not os.path.isfile(file_path):
            messagebox.showerror("Error", "File does not exist.")
            return

        self.zip_path.set(file_path)

        # Auto-fill destination if empty
        if not self.dest_path.get():
            self.dest_path.set(os.path.dirname(file_path))

        self.log(f"Dropped: {os.path.basename(file_path)}")
        self.status_var.set("ZIP file loaded via Drag & Drop")

    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")
        self.root.update_idletasks()

    def update_progress(self, value=None, text=None):
        if value is not None:
            self.progress["value"] = value
        if text is not None:
            self.progress_label.config(text=text)
        self.root.update_idletasks()

    def browse_zip(self):
        path = filedialog.askopenfilename(
            title="Select ZIP file",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        if path:
            self.zip_path.set(path)
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
            messagebox.showwarning("Missing ZIP", "Please select or drop a ZIP file.")
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
        self.status_var.set("Working...")
        self.progress["value"] = 0
        self.update_progress(0, "Starting...")

        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state="disabled")

        thread = threading.Thread(target=self.extract_nested, args=(zip_file, dest), daemon=True)
        thread.start()

    def count_nested_zips(self, folder):
        count = 0
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f.lower().endswith(".zip"):
                    count += 1
        return count

    def extract_nested(self, zip_file, to_folder):
        try:
            self.log(f"Starting extraction of: {os.path.basename(zip_file)}")
            self.log(f"Destination: {to_folder}")
            self.log("-" * 55)

            self.update_progress(5, "Extracting main archive...")
            with zipfile.ZipFile(zip_file, 'r') as zf:
                zf.extractall(path=to_folder)
            self.log(f"✓ Extracted main: {os.path.basename(zip_file)}")

            if self.delete_zips.get():
                try:
                    os.remove(zip_file)
                    self.log(f"  → Deleted: {os.path.basename(zip_file)}")
                except Exception as e:
                    self.log(f"  ⚠ Could not delete original ZIP: {e}")

            self.total_zips = self.count_nested_zips(to_folder)
            self.processed_zips = 0

            if self.total_zips == 0:
                self.update_progress(100, "Done — no nested ZIPs found")
                self.log("No nested ZIP files found.")
            else:
                self.log(f"Found {self.total_zips} nested ZIP file(s). Processing...")
                self.update_progress(10, f"Found {self.total_zips} nested ZIP(s)...")

            while True:
                found = False
                for root, dirs, files in os.walk(to_folder):
                    for filename in files:
                        if filename.lower().endswith(".zip"):
                            found = True
                            file_path = os.path.join(root, filename)

                            self.processed_zips += 1
                            percent = 10 + int((self.processed_zips / max(self.total_zips, 1)) * 85)
                            self.update_progress(percent, f"Extracting ({self.processed_zips}/{self.total_zips}): {filename}")

                            try:
                                self.log(f"→ Extracting nested: {filename}")
                                with zipfile.ZipFile(file_path, 'r') as zf:
                                    zf.extractall(path=root)
                                self.log(f"  ✓ Done: {filename}")

                                if self.delete_zips.get():
                                    os.remove(file_path)
                                    self.log(f"  → Deleted: {filename}")
                            except Exception as e:
                                self.log(f"  ✗ Failed: {filename} — {e}")

                if not found:
                    break

                remaining = self.count_nested_zips(to_folder)
                if remaining > 0:
                    self.total_zips = self.processed_zips + remaining

            self.update_progress(100, "Extraction complete!")
            self.log("-" * 55)
            self.log(f"Finished! Processed {self.processed_zips} nested ZIP archive(s).")
            self.status_var.set("Completed successfully")
            messagebox.showinfo("Success", f"Extraction finished!\n\nProcessed {self.processed_zips} nested ZIP(s).")

        except Exception as e:
            self.log(f"✗ Error: {e}")
            self.status_var.set("Error occurred")
            self.update_progress(0, "Failed")
            messagebox.showerror("Error", f"Extraction failed:\n{e}")

        finally:
            self.is_extracting = False
            self.root.after(0, lambda: self.extract_btn.configure(state="normal"))


if __name__ == "__main__":
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()          # Important: use TkinterDnD.Tk() instead of tk.Tk()
    else:
        root = tk.Tk()

    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    app = NestedZipExtractor(root)
    root.mainloop()