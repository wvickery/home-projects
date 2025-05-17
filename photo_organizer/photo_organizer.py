import os
import shutil
from datetime import datetime, timedelta
from dataclasses import dataclass
from PIL import Image
from PIL.ExifTags import TAGS
import tkinter as tk
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry  # 📅 Calendar picker

# Supported image formats
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".tiff", ".bmp")

@dataclass
class OrganizerConfig:
    source_dir: str
    dest_dir: str
    start_date: datetime
    end_date: datetime
    action: str  # "Copy" or "Move"
    suffix: str
    status_label: tk.Label

def get_exif_date_taken(image_path):
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        if not exif_data:
            return None
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == 'DateTimeOriginal':
                return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception as e:
        print(f"EXIF error on {image_path}: {e}")
    return None

def organize_photos(config: OrganizerConfig):
    for root, _, files in os.walk(config.source_dir):
        for file in files:
            if not file.lower().endswith(IMAGE_EXTENSIONS):
                continue

            file_path = os.path.join(root, file)
            date_taken = get_exif_date_taken(file_path)
            if not date_taken:
                date_taken = datetime.fromtimestamp(os.path.getmtime(file_path))

            if not (config.start_date <= date_taken <= config.end_date):
                continue

            year_folder = str(date_taken.year)
            month_name = date_taken.strftime("%b").capitalize()  # Abbreviated (Jan, Feb, etc.)
            month_number = date_taken.strftime("%m")
            month_folder = f"{month_number} - {month_name} - {config.suffix}"

            dest_folder = os.path.join(config.dest_dir, year_folder, month_folder)
            os.makedirs(dest_folder, exist_ok=True)

            dest_path = os.path.join(dest_folder, file)
            base, ext = os.path.splitext(dest_path)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = f"{base}_{counter}{ext}"
                counter += 1

            if config.action == "Copy":
                shutil.copy2(file_path, dest_path)
            else:
                shutil.move(file_path, dest_path)

            config.status_label.config(text=f"{config.action}ed: {file}")
            config.status_label.update_idletasks()

    messagebox.showinfo("Done", f"Photos {config.action.lower()}ed successfully!")
    config.status_label.config(text="Complete.")

def browse_directory(entry):
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        entry.delete(0, tk.END)
        entry.insert(0, folder_selected)

def create_gui():
    root = tk.Tk()
    root.title("Photo Organizer")

    # Source Folder
    tk.Label(root, text="Source Folder:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
    source_entry = tk.Entry(root, width=50)
    source_entry.grid(row=0, column=1, padx=10)
    tk.Button(root, text="Browse", command=lambda: browse_directory(source_entry)).grid(row=0, column=2)

    # Destination Folder
    tk.Label(root, text="Destination Folder:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    dest_entry = tk.Entry(root, width=50)
    dest_entry.grid(row=1, column=1, padx=10)
    tk.Button(root, text="Browse", command=lambda: browse_directory(dest_entry)).grid(row=1, column=2)

    # Start Date
    tk.Label(root, text="Start Date (optional):").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    start_entry = DateEntry(root, width=20, date_pattern="yyyy-mm-dd")
    start_entry.delete(0, tk.END)  # Allow blank
    start_entry.grid(row=2, column=1, sticky="w")

    tk.Button(root, text="Clear", command=lambda: start_entry.delete(0, tk.END)).grid(row=2, column=2, padx=5)

    # End Date
    tk.Label(root, text="End Date (optional):").grid(row=3, column=0, sticky="w", padx=10, pady=5)
    end_entry = DateEntry(root, width=20, date_pattern="yyyy-mm-dd")
    end_entry.delete(0, tk.END)  # Allow blank
    end_entry.grid(row=3, column=1, sticky="w")

    tk.Button(root, text="Clear", command=lambda: end_entry.delete(0, tk.END)).grid(row=3, column=2, padx=5)

    # Action (Copy or Move)
    tk.Label(root, text="Action:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
    action_var = tk.StringVar(value="Copy")
    action_menu = tk.OptionMenu(root, action_var, "Move", "Copy")
    action_menu.grid(row=4, column=1, sticky="w")

    # Month Folder Suffix
    tk.Label(root, text="Month Folder Suffix:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
    suffix_entry = tk.Entry(root, width=30)
    suffix_entry.insert(0, "Misc")
    suffix_entry.grid(row=5, column=1, sticky="w")

    # Status Label
    status_label = tk.Label(root, text="Status: Waiting to start.", fg="blue")
    status_label.grid(row=7, column=0, columnspan=3, pady=10)

    def start_organizing():
        source = source_entry.get().strip()
        dest = dest_entry.get().strip()

        if not os.path.isdir(source) or not os.path.isdir(dest):
            messagebox.showerror("Error", "Both source and destination folders must be valid.")
            return

        suffix = suffix_entry.get().strip() or "Misc"

        # Handle optional start/end date inputs
        try:
            start_input = start_entry.get().strip()
            end_input = end_entry.get().strip()

            start_date = datetime.strptime(start_input, "%Y-%m-%d") if start_input else datetime.min
            end_date = datetime.strptime(end_input, "%Y-%m-%d") + timedelta(days=1) if end_input else datetime.now()
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
            return

        config = OrganizerConfig(
            source_dir=source,
            dest_dir=dest,
            start_date=start_date,
            end_date=end_date,
            action=action_var.get(),
            suffix=suffix,
            status_label=status_label
        )

        organize_photos(config)

    # Start Button
    tk.Button(root, text="Start Organizing", command=start_organizing, bg="green", fg="white").grid(row=6, column=1, pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
