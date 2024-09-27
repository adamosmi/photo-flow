import os
import sqlite3
import tkinter as tk
from tkinter import filedialog, Listbox
from PIL import Image, ImageTk, ExifTags, ImageOps
import io

class ImageViewer:
    def __init__(self, root, image_folder, selects_folder, db_file='/tmp/image_data.db'):
        self.root = root
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.bind("<Left>", self.show_previous_image)
        self.root.bind("<Right>", self.show_next_image)
        self.root.bind("<Return>", self.pick_image)

        self.image_folder = image_folder
        self.selects_folder = selects_folder
        self.db_file = db_file

        # Initialize database in /tmp
        self.init_db()

        # Get total image count from the folder (for progressive loading)
        self.image_files = [f for f in sorted(os.listdir(image_folder)) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        self.total_images = len(self.image_files)
        
        self.current_image_index = -1  # Start before the first image
        self.selected_files = []  # List to hold selected files

        # Create canvas to display images
        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Create sidebar for selected images
        self.sidebar = tk.Frame(root, width=200, bg='lightgrey')
        self.sidebar.pack(fill=tk.Y, side=tk.RIGHT)
        self.listbox = Listbox(self.sidebar, width=30, height=50)
        self.listbox.pack(side=tk.TOP, fill=tk.Y)
        self.listbox.bind('<<ListboxSelect>>', self.on_sidebar_select)

        # Create a label for image counter
        self.image_counter_label = tk.Label(self.canvas, text="", bg="white", font=("Helvetica", 14))
        self.image_counter_label.place(relx=0.95, rely=0.05, anchor=tk.NE)

        # Load the first image when the user presses 'Right' or 'Next'
        self.show_next_image()

    def init_db(self):
        """Initialize the SQLite database in /tmp to store image binary data."""
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()

        # Create table for storing image binary data
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY,
                file_name TEXT,
                image_data BLOB
            )
        ''')
        self.conn.commit()

    def load_image_data(self, image_index):
        """Load image binary data into the SQLite database progressively."""
        # Check if the image already exists in the database
        file_name = self.image_files[image_index]
        self.cursor.execute('SELECT id FROM images WHERE file_name = ?', (file_name,))
        if self.cursor.fetchone() is not None:
            return  # Image already in the database

        # If not, load the image and store it in the database
        file_path = os.path.join(self.image_folder, file_name)
        with open(file_path, 'rb') as file:
            binary_data = file.read()
            self.cursor.execute('INSERT INTO images (file_name, image_data) VALUES (?, ?)', (file_name, binary_data))
            self.conn.commit()

    def get_image_data(self, image_index):
        """Get the binary data and file name of the image at a given index from the database."""
        self.load_image_data(image_index)  # Load the image data if not already in the database

        file_name = self.image_files[image_index]
        self.cursor.execute('SELECT file_name, image_data FROM images WHERE file_name = ?', (file_name,))
        result = self.cursor.fetchone()
        return result if result else (None, None)

    def correct_image_orientation(self, image):
        """Correct image orientation based on EXIF metadata."""
        try:
            # Get EXIF data
            exif = image._getexif()
            if exif:
                for tag, value in ExifTags.TAGS.items():
                    if value == 'Orientation':
                        orientation = exif.get(tag)
                        break

                # Rotate or flip the image based on the orientation
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError):
            # Cases where there is no EXIF data or orientation tag
            pass

        return image

    def show_image(self):
        """Display the current image."""
        file_name, image_data = self.get_image_data(self.current_image_index)

        if image_data:
            # Convert the binary data into a Pillow image
            image = Image.open(io.BytesIO(image_data))

            # Correct the orientation based on EXIF data
            image = self.correct_image_orientation(image)

            # Resize the image while keeping aspect ratio
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            image = self.resize_image(image, screen_width, screen_height)

            # Display the image
            self.tk_image = ImageTk.PhotoImage(image)
            self.canvas.delete("all")
            self.canvas.create_image(screen_width // 2, screen_height // 2, image=self.tk_image, anchor=tk.CENTER)

            # Update image counter
            self.update_image_counter()

    def resize_image(self, image, max_width, max_height):
        """Resize image while preserving the aspect ratio."""
        img_width, img_height = image.size
        ratio = min(max_width / img_width, max_height / img_height)
        new_size = (int(img_width * ratio), int(img_height * ratio))
        return image.resize(new_size, Image.LANCZOS)

    def show_next_image(self, event=None):
        """Show the next image in the folder when navigating forward."""
        if self.current_image_index < self.total_images - 1:
            self.current_image_index += 1
            self.show_image()

    def show_previous_image(self, event=None):
        """Show the previous image in the folder when navigating backward."""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_image()

    def pick_image(self, event=None):
        """Create a symlink in the 'selects' folder for the current image."""
        file_name, _ = self.get_image_data(self.current_image_index)
        if file_name:
            link_path = os.path.join(self.selects_folder, file_name)
            source_path = os.path.join(self.image_folder, file_name)

            # Create symlink to the selected image
            if not os.path.exists(link_path):
                os.symlink(source_path, link_path)
                print(f"Selected: {file_name}")
                self.selected_files.append(file_name)
                self.update_sidebar()
            else:
                print(f"{file_name} is already selected.")

    def update_sidebar(self):
        """Update the sidebar with the selected images."""
        self.listbox.delete(0, tk.END)
        for file in self.selected_files:
            self.listbox.insert(tk.END, file)

    def on_sidebar_select(self, event):
        """Navigate to the image when a file is selected in the sidebar."""
        selected_index = self.listbox.curselection()
        if selected_index:
            file_name = self.listbox.get(selected_index[0])
            if file_name in self.image_files:
                self.current_image_index = self.image_files.index(file_name)
                self.show_image()

    def update_image_counter(self):
        """Update the image counter label in the top-right corner."""
        self.image_counter_label.config(text=f"{self.current_image_index + 1}/{self.total_images}")

    def exit_fullscreen(self, event=None):
        """Exit full screen and close the application."""
        self.root.attributes('-fullscreen', False)
        self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()

    # Choose the image folder and the "selects" folder
    image_folder = filedialog.askdirectory(title="Select the folder with images")
    selects_folder = filedialog.askdirectory(title="Select the 'selects' folder")

    if image_folder and selects_folder:
        viewer = ImageViewer(root, image_folder, selects_folder)
        root.mainloop()
