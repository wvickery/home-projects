import os
import shutil
from datetime import datetime, timedelta
from PIL import Image
from PIL.ExifTags import TAGS
import tkinter as tk
from tkinter import filedialog, messagebox

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".tiff", ".bmp")

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

def organize_photos(source_dir, dest_dir, start_date, end_date, action, status_label):
    for root, _, files in os.walk(source_dir):
        for file in files:
            if not file.lower().endswith(IMAGE_EXTENSIONS):
                continue
            file_path = os.path.join(root, file)
            date_taken = get_exif_date_taken(file_path)
            if not date_taken:
                date_taken = datetime.fromtimestamp(os.path.getmtime(file_path))

            if not (start_date <= date_taken <= end_date):
                continue

            folder_name = f"{date_taken.year}-{date_taken.month:02d}"
            dest_folder = os.path.join(dest_dir, folder_name)
            os.makedirs(dest_folder, exist_ok=True)

            dest_path = os.path.join(dest_folder, file)
            base, ext = os.path.splitext(dest_path)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = f"{base}_{counter}{ext}"
                counter += 1

            if action == "Copy":
                shutil.copy2(file_path, dest_path)
            else:
                shutil.move(file_path, dest_path)

            status_label.config(text=f"{action}ed: {file}")
            status_label.update_idletasks()

    messagebox.showinfo("Done", f"Photos {action.lower()}ed successfully!")
    status_label.config(text="Complete.")

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
    tk.Label(root, text="Start Date (YYYY-MM-DD):").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    start_entry = tk.Entry(root, width=20)
    start_entry.grid(row=2, column=1, sticky="w")

    # End Date
    tk.Label(root, text="End Date (YYYY-MM-DD):").grid(row=3, column=0, sticky="w", padx=10, pady=5)
    end_entry = tk.Entry(root, width=20)
    end_entry.grid(row=3, column=1, sticky="w")

    # Action (Copy or Move)
    tk.Label(root, text="Action:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
    action_var = tk.StringVar(value="Move")
    action_menu = tk.OptionMenu(root, action_var, "Move", "Copy")
    action_menu.grid(row=4, column=1, sticky="w")

    # Month Folder Suffix
    tk.Label(root, text="Month Folder Suffix:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
    suffix_entry = tk.Entry(root, width=30)
    suffix_entry.insert(0, "Misc")
    suffix_entry.grid(row=5, column=1, sticky="w")

    # Status Label
    status_label = tk.Label(root, text="Status: Waiting to start.", fg="blue")
    status_label.grid(row=6, column=0, columnspan=3, pady=10)

    def start_organizing():
        source = source_entry.get()
        dest = dest_entry.get()
        try:
            start_date = datetime.strptime(start_entry.get(), "%Y-%m-%d")
            end_date = datetime.strptime(end_entry.get(), "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
            return

        if not os.path.isdir(source) or not os.path.isdir(dest):
            messagebox.showerror("Error", "Both source and destination folders must be valid.")
            return

        action = action_var.get()
        organize_photos(source, dest, start_date, end_date, action, status_label)

    # Start Button
    tk.Button(root, text="Start Organizing", command=start_organizing, bg="green", fg="white").grid(row=5, column=1, pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
