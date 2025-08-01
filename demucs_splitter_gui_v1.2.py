import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os
import threading
import subprocess
import re

class DemucsStemSplitterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Demucs Stem Splitter")
        self.geometry("500x280")
        self.resizable(False, False)

        # File selection
        tk.Label(self, text="1) Select an audio file:").pack(pady=(15, 5))
        tk.Button(self, text="Browse File…", command=self.browse_file).pack()
        self.file_label = tk.Label(self, text="No file selected", fg="gray")
        self.file_label.pack(pady=(0, 15))

        # Output folder selection
        tk.Label(self, text="2) Select an output folder:").pack(pady=(0, 5))
        tk.Button(self, text="Browse Folder…", command=self.browse_folder).pack()
        self.folder_label = tk.Label(self, text="No folder selected", fg="gray")
        self.folder_label.pack(pady=(0, 15))

        # Split button
        self.split_btn = tk.Button(self, text="Split Stems", command=self.start_split, state=tk.DISABLED)
        self.split_btn.pack(pady=(0, 10))

        # Progress bar
        self.progress = ttk.Progressbar(self, mode='determinate', maximum=100)
        self.progress.pack(fill='x', padx=20)
        self.progress_label = tk.Label(self, text="")
        self.progress_label.pack(pady=(5, 0))

        # Internal state
        self.audio_path = None
        self.out_dir = None

    def browse_file(self):
        f = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav *.flac *.ogg *.m4a")])
        if f:
            self.audio_path = f
            self.file_label.config(text=os.path.basename(f), fg="black")
        else:
            self.audio_path = None
            self.file_label.config(text="No file selected", fg="gray")
        self.update_split_button()

    def browse_folder(self):
        d = filedialog.askdirectory(title="Select output folder")
        if d:
            self.out_dir = d
            self.folder_label.config(text=d, fg="black")
        else:
            self.out_dir = None
            self.folder_label.config(text="No folder selected", fg="gray")
        self.update_split_button()

    def update_split_button(self):
        state = tk.NORMAL if (self.audio_path and self.out_dir) else tk.DISABLED
        self.split_btn.config(state=state)

    def start_split(self):
        # Reset progress
        self.progress['value'] = 0
        self.progress_label.config(text="Processing... 0%")
        self.split_btn.config(state=tk.DISABLED)
        # Start separation thread
        threading.Thread(target=self._run_demucs_cli, daemon=True).start()

    def _run_demucs_cli(self):
        try:
            # Use Popen to capture CLI progress
            proc = subprocess.Popen(
                ["demucs", "--two-stems=vocals", "-o", self.out_dir, self.audio_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors='ignore'
            )
            for line in proc.stdout:
                match = re.search(r"(\d{1,3})%", line)
                if match:
                    pct = int(match.group(1))
                    self.progress['value'] = pct
                    self.progress_label.config(text=f"Processing... {pct}%")
                    self.update_idletasks()
            proc.wait()
            if proc.returncode == 0:
                self.progress['value'] = 100
                self.progress_label.config(text="✅ Done! 100%")
                messagebox.showinfo(
                    "Success",
                    f"Stems written under:\n{self.out_dir}{os.sep}separated"
                )
            else:
                raise subprocess.CalledProcessError(proc.returncode, proc.args)
        except Exception as e:
            self.progress_label.config(text="❌ Error occurred.")
            messagebox.showerror("Error", f"Demucs failed:\n{e}")
        finally:
            self.split_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    app = DemucsStemSplitterApp()
    app.mainloop()
