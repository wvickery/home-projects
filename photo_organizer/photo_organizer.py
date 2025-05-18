# Photo Organizer

import os
import shutil
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict
from PIL import Image
from PIL.ExifTags import TAGS
import tkinter as tk
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry
from tkinter import ttk  # for Progressbar
import threading         # to avoid freezing the UI

MEDIA_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.mp4', '.mov', '.avi', '.mkv')

@dataclass
class FolderStats:
    new_files: int
    updated_files: int
    existing_files: int

@dataclass
class OrganizerConfig:
    source_dir: str
    dest_dir: str
    action: str
    suffix: str
    status_label: tk.Label
    included_folders: set

def get_exif_date_taken(image_path):
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        if not exif_data:
            return None
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == 'DateTimeOriginal':
                return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
    except Exception:
        pass
    return None

def generate_preview(source_dir, dest_dir, suffix):
    from pathlib import Path

    preview = defaultdict(lambda: defaultdict(lambda: FolderStats(0, 0, 0)))
    touched_paths = defaultdict(set)  # (year, month) → full dest file paths (normalized)

    for root, _, files in os.walk(source_dir):
        for file in files:
            if not file.lower().endswith(MEDIA_EXTENSIONS):
                continue

            file_path = os.path.join(root, file)
            try:
                date_taken = get_exif_date_taken(file_path)
                if not date_taken:
                    date_taken = datetime.fromtimestamp(os.path.getmtime(file_path))

                year = str(date_taken.year)
                month = f"{date_taken.strftime('%m')} - {date_taken.strftime('%b').capitalize()} - {suffix}"
                stats = preview[year][month]

                dest_folder = os.path.join(dest_dir, year, month)
                dest_path = os.path.normpath(os.path.join(dest_folder, file))

                if os.path.exists(dest_path):
                    stats.updated_files += 1
                else:
                    stats.new_files += 1

                touched_paths[(year, month)].add(dest_path)

            except Exception:
                continue

    # Count truly untouched files (existing)
    for (year, month), touched in touched_paths.items():
        folder_path = os.path.join(dest_dir, year, month)
        if os.path.exists(folder_path):
            all_dest_paths = {
                os.path.normpath(os.path.join(folder_path, f))
                for f in os.listdir(folder_path)
                if f.lower().endswith(MEDIA_EXTENSIONS)
            }
            untouched = all_dest_paths - touched
            preview[year][month].existing_files = len(untouched)

    return preview

def build_preview_ui(parent_frame, preview_data):
    check_vars = {}
    year_vars = {}

    for widget in parent_frame.winfo_children():
        widget.destroy()

    def toggle_year(year):
        val = year_vars[year].get()
        for (y, m), var in check_vars.items():
            if y == year:
                var.set(val)

    row = 0
    for year, months in sorted(preview_data.items()):
        year_vars[year] = tk.BooleanVar(value=True)
        year_check = tk.Checkbutton(parent_frame, text=f"{year}/", variable=year_vars[year], fg="black",
                                    command=lambda y=year: toggle_year(y), font=("Consolas", 10, "bold"))
        year_check.grid(row=row, column=0, sticky="w", padx=5, pady=(5, 2))
        row += 1
        for month, stats in sorted(months.items()):
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(parent_frame, text=month, variable=var, anchor="w", font=("Consolas", 10), fg="black")
            cb.grid(row=row, column=0, sticky="w", padx=20)
            summary_frame = tk.Frame(parent_frame)
            summary_frame.grid(row=row, column=1, sticky="w")

            def colorize(count, color):
                return color if count > 0 else "gray"

            tk.Label(summary_frame, text="[", fg="black", font=("Consolas", 10)).pack(side="left")
            tk.Label(summary_frame, text=f"{stats.new_files} new", fg=colorize(stats.new_files, "green"), font=("Consolas", 10)).pack(side="left")
            tk.Label(summary_frame, text=", ", fg="black", font=("Consolas", 10)).pack(side="left")
            tk.Label(summary_frame, text=f"{stats.updated_files} updated", fg=colorize(stats.updated_files, "blue"), font=("Consolas", 10)).pack(side="left")
            tk.Label(summary_frame, text=", ", fg="black", font=("Consolas", 10)).pack(side="left")
            tk.Label(summary_frame, text=f"{stats.existing_files} existing", fg=colorize(stats.existing_files, "black"), font=("Consolas", 10)).pack(side="left")
            tk.Label(summary_frame, text="]", fg="black", font=("Consolas", 10)).pack(side="left")

            check_vars[(year, month)] = var
            row += 1
            continue
            cb.grid(row=row, column=0, sticky="w", padx=20)
            row += 1
    return check_vars

def create_gui():
    root = tk.Tk()
    root.title("Photo Organizer - Toggle Years + Months")
    root.columnconfigure(1, weight=1)
    root.rowconfigure(5, weight=1)
    status_label = tk.Label(root, text="Status: Set both folders to generate preview...", fg="blue")
    status_label.grid(row=0, column=0, columnspan=3, pady=5)

    tk.Label(root, text="Source Folder:").grid(row=1, column=0, sticky="w", padx=10)
    source_entry = tk.Entry(root, width=75)
    source_entry.grid(row=1, column=1, sticky="we", padx=(0, 5))
    tk.Button(root, text="Browse", command=lambda: [source_entry.delete(0, tk.END), source_entry.insert(0, filedialog.askdirectory()), try_load_preview()]).grid(row=1, column=2, sticky="e", padx=5)

    tk.Label(root, text="Destination Folder:").grid(row=2, column=0, sticky="w", padx=10)
    dest_entry = tk.Entry(root, width=75)
    dest_entry.grid(row=2, column=1, sticky="we", padx=(0, 5))
    tk.Button(root, text="Browse", command=lambda: [dest_entry.delete(0, tk.END), dest_entry.insert(0, filedialog.askdirectory()), try_load_preview()]).grid(row=2, column=2, sticky="e", padx=5)

    tk.Label(root, text="Folder Suffix:").grid(row=3, column=0, sticky="w", padx=10)
    suffix_entry = tk.Entry(root, width=30)
    suffix_entry.insert(0, "Misc")
    suffix_entry.grid(row=3, column=1, sticky="w")

    tk.Label(root, text="Action:").grid(row=4, column=0, sticky="w", padx=10)
    action_var = tk.StringVar(value="Copy")
    action_menu = tk.OptionMenu(root, action_var, "Copy", "Move")
    action_menu.grid(row=4, column=1, sticky="w")

    # Scrollable preview frame setup
    canvas = tk.Canvas(root, height=300)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
    scrollbar.grid(row=5, column=2, sticky="ns")

    check_vars = {}
    cancel_requested = [False]  # Mutable flag to allow canceling mid-thread

    def set_inputs_enabled(enabled: bool):
        state = "normal" if enabled else "disabled"
        source_entry.config(state=state)
        dest_entry.config(state=state)
        suffix_entry.config(state=state)
        action_menu.config(state=state)

    def organize_photos_thread(config: OrganizerConfig):
        # Step 1: Hide start button and show spinner immediately
        root.after(0, lambda: start_button.grid_remove())
        root.after(0, lambda: set_inputs_enabled(False))
        root.after(0, lambda: spinner_label.config(text="🗂 Preparing to organize..."))
        root.after(0, lambda: spinner_label.grid(row=6, column=0, columnspan=2, pady=5))
        root.after(0, lambda: cancel_requested.__setitem__(0, False))  # Reset flag
        root.after(0, lambda: cancel_button.grid())  # Show cancel button

        # Step 2: Build file list
        files_to_process = []
        for root_dir, _, files in os.walk(config.source_dir):
            if cancel_requested[0]:
                break
            for file in files:
                if cancel_requested[0]:
                    break
                if not file.lower().endswith(MEDIA_EXTENSIONS):
                    continue
                file_path = os.path.join(root_dir, file)
                date_taken = get_exif_date_taken(file_path)
                if not date_taken:
                    date_taken = datetime.fromtimestamp(os.path.getmtime(file_path))
                year = str(date_taken.year)
                month = f"{date_taken.strftime('%m')} - {date_taken.strftime('%b').capitalize()} - {config.suffix}"
                if (year, month) not in config.included_folders:
                    continue
                dest_folder = os.path.join(config.dest_dir, year, month)
                dest_path = os.path.join(dest_folder, file)
                files_to_process.append((file_path, dest_path, year, month))

        if not files_to_process:
            root.after(0, lambda: spinner_label.grid_remove())
            root.after(0, lambda: messagebox.showinfo("No Files", "No matching files to organize."))
            root.after(0, lambda: start_button.grid())
            return

        # Step 3: Hide spinner and show progress bar + count
        root.after(0, lambda: spinner_label.grid_remove())
        root.after(0, lambda: progress.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="we"))
        root.after(0, lambda: count_label.grid(row=7, column=0, columnspan=2))

        total = len(files_to_process)

        def update_progress(i, total, current_file):
            progress["value"] = int((i / total) * 100)
            count_label.config(text=f"{i} / {total}")
            config.status_label.config(text=f"{config.action}ed: {os.path.basename(current_file)}")
            root.update_idletasks()


        for i, (src, dest, year, month) in enumerate(files_to_process, 1):
            if cancel_requested[0]:
                break
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if config.action == 'Copy':
                shutil.copy2(src, dest)
            else:
                shutil.move(src, dest)
            root.after(0, update_progress, i, total, src)

        def finish():
            progress.grid_remove()
            count_label.grid_remove()
            cancel_button.grid_remove()
            start_button.grid()
            if cancel_requested[0]:
                messagebox.showinfo("Canceled", f"Operation was canceled. Some files may have been {config.action.lower()}ed.")
            else:
                messagebox.showinfo("Done", f"Photos {config.action.lower()}ed successfully!")
            try_load_preview()
            config.status_label.config(text='Complete.')
            set_inputs_enabled(True)

        root.after(0, finish)

    def try_load_preview():
        source = source_entry.get().strip()
        dest = dest_entry.get().strip()
        suffix = suffix_entry.get().strip() or "Misc"

        if os.path.isdir(source) and os.path.isdir(dest):
            spinner_label.config(text="⏳ Generating preview...")
            spinner_label.grid(row=5, column=0, columnspan=2, pady=5)
            root.update()  # refresh UI

            preview_data = generate_preview(source, dest, suffix)
            check_vars.clear()
            check_vars.update(build_preview_ui(scrollable_frame, preview_data))

            spinner_label.grid_remove()
            status_label.config(text="Preview ready. Select folders and start organizing.", fg="green")

    def start_organizing():
        source = source_entry.get().strip()
        dest = dest_entry.get().strip()
        if not os.path.isdir(source) or not os.path.isdir(dest):
            messagebox.showerror("Error", "Valid source and destination required.")
            return
        suffix = suffix_entry.get().strip() or "Misc"
        included = {k for k, v in check_vars.items() if v.get()}
        if not included:
            messagebox.showwarning("Nothing Selected", "No folders selected to organize.")
            return
        if action_var.get() == "Move" and not messagebox.askyesno("Confirm Move", "Are you sure you want to move files?"):
            return

        config = OrganizerConfig(
            source_dir=source,
            dest_dir=dest,
            action=action_var.get(),
            suffix=suffix,
            status_label=status_label,
            included_folders=included
        )

        threading.Thread(target=lambda: organize_photos_thread(config)).start()

    spinner_label = tk.Label(root, text="", fg="gray", font=("Consolas", 10))
    progress = ttk.Progressbar(root, orient="horizontal", mode="determinate", maximum=100)
    count_label = tk.Label(root, text="", fg="gray", font=("Consolas", 10))
    start_button = tk.Button(root, text="Start Organizing", bg="green", fg="white", command=start_organizing)
    start_button.grid(row=6, column=1, pady=10)

    cancel_button = tk.Button(root, text="Cancel", bg="red", fg="white", command=lambda: cancel_requested.__setitem__(0, True))
    cancel_button.grid(row=8, column=1, pady=(0, 10))
    cancel_button.grid_remove()  # Hide by default

    root.mainloop()


if __name__ == '__main__':
    create_gui()
