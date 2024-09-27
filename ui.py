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
        self.root.bind("g", self.jump_to_image_prompt)

        self.image_folder = image_folder
        self.selects_folder = selects_folder
        self.db_file = db_file

        # Sidebar width (to be considered when centering the image)
        self.sidebar_width = 200

        # Initialize database in /tmp
        self.init_db()

        # Get total image count from the folder (for progressive loading)
        self.image_files = [f for f in sorted(os.listdir(image_folder)) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        self.total_images = len(self.image_files)
        
        self.current_image_index = -1  # Start before the first image
        self.selected_files = []  # List to hold selected file indexes

        # Create sidebar for selected images (on the left)
        self.sidebar = tk.Frame(root, width=self.sidebar_width, bg='lightgrey')
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT)
        self.listbox = Listbox(self.sidebar, width=30, height=50)
        self.listbox.pack(side=tk.TOP, fill=tk.Y)
        self.listbox.bind('<<ListboxSelect>>', self.on_sidebar_select)

        # Create canvas to display images (on the right)
        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)

        # Create a label for image counter
        self.image_counter_label = tk.Label(self.canvas, text="", bg="white", font=("Helvetica", 14))
        self.image_counter_label.place(relx=0.95, rely=0.05, anchor=tk.NE)

        # Load selected images in the sidebar on start
        self.load_selected_images()

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
        file_name = self.image_files[image_index]
        self.cursor.execute('SELECT id FROM images WHERE file_name = ?', (file_name,))
        if self.cursor.fetchone() is not None:
            return  # Image already in the database

        # If not, load the image and store it in the database
        file_path = os.path.join(self.image_folder, file_name)
        try:
            with open(file_path, 'rb') as file:
                binary_data = file.read()
                self.cursor.execute('INSERT INTO images (file_name, image_data) VALUES (?, ?)', (file_name, binary_data))
                self.conn.commit()
        except Exception as e:
            print(f"Error loading image {file_name}: {e}")

    def get_image_data(self, image_index):
        """Get the binary data and file name of the image at a given index from the database."""
        if image_index < 0 or image_index >= self.total_images:
            print(f"Invalid image index: {image_index}")
            return None, None
        
        self.load_image_data(image_index)  # Load the image data if not already in the database

        file_name = self.image_files[image_index]
        self.cursor.execute('SELECT file_name, image_data FROM images WHERE file_name = ?', (file_name,))
        result = self.cursor.fetchone()
        if result:
            return result
        else:
            print(f"Failed to retrieve image data for {file_name}")
            return None, None

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
            try:
                # Convert the binary data into a Pillow image
                image = Image.open(io.BytesIO(image_data))

                # Correct the orientation based on EXIF data
                image = self.correct_image_orientation(image)

                # Resize the image while keeping aspect ratio
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()

                # Available width for the image (subtract sidebar width)
                available_width = screen_width - self.sidebar_width

                image = self.resize_image(image, available_width, screen_height)

                # Display the image in the center of the available area (to the right of the sidebar)
                # center_x = self.sidebar_width + available_width // 2
                center_x = available_width // 2
                center_y = screen_height // 2

                self.tk_image = ImageTk.PhotoImage(image)
                self.canvas.delete("all")
                self.canvas.create_image(center_x, center_y, image=self.tk_image, anchor=tk.CENTER)

                # Update image counter
                self.update_image_counter()
            except Exception as e:
                print(f"Error displaying image {file_name}: {e}")

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
        else:
            print("Already at the last image.")

    def show_previous_image(self, event=None):
        """Show the previous image in the folder when navigating backward."""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_image()
        else:
            print("Already at the first image.")

    def pick_image(self, event=None):
        """Create a symlink in the 'selects' folder for the current image."""
        file_name, _ = self.get_image_data(self.current_image_index)
        if file_name:
            link_path = os.path.join(self.selects_folder, file_name)
            source_path = os.path.join(self.image_folder, file_name)

            # Create symlink to the selected image
            if not os.path.exists(link_path):
                try:
                    os.symlink(source_path, link_path)
                    print(f"Selected: {file_name}")
                    if self.current_image_index not in self.selected_files:
                        self.selected_files.append(self.current_image_index)
                    self.update_sidebar()
                except Exception as e:
                    print(f"Error selecting image {file_name}: {e}")
            else:
                print(f"{file_name} is already selected.")

    def update_sidebar(self):
        """Update the sidebar with the selected images, displaying their actual index."""
        self.listbox.delete(0, tk.END)
        for index in self.selected_files:
            file_name = self.image_files[index]
            display_text = f"{index + 1} - {file_name}"  # Index is 1-based for display purposes
            self.listbox.insert(tk.END, display_text)

    def load_selected_images(self):
        """Load the already selected images from the selects folder."""
        if os.path.exists(self.selects_folder):
            selected_files = [f for f in sorted(os.listdir(self.selects_folder)) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            for selected_file in selected_files:
                if selected_file in self.image_files:
                    index = self.image_files.index(selected_file)
                    if index not in self.selected_files:
                        self.selected_files.append(index)
            self.update_sidebar()

    def on_sidebar_select(self, event):
        """Navigate to the image when a file is selected in the sidebar."""
        selected_index = self.listbox.curselection()
        if selected_index:
            # Strip off the index before the file name
            display_text = self.listbox.get(selected_index[0])
            index_str, file_name = display_text.split(' - ', 1)  # Get index from display text
            self.current_image_index = int(index_str) - 1  # Adjust back to 0-based index
            self.show_image()

    def update_image_counter(self):
        """Update the image counter label in the top-right corner."""
        self.image_counter_label.config(text=f"{self.current_image_index + 1}/{self.total_images}")

    def exit_fullscreen(self, event=None):
        """Exit full screen and close the application."""
        self.root.attributes('-fullscreen', False)
        self.root.quit()

    def jump_to_image(self, image_index):
        """Jump to a specific image by its index."""
        if 0 <= image_index < self.total_images:
            self.current_image_index = image_index
            self.show_image()
        else:
            print(f"Index {image_index} is out of bounds. Valid range is 1 to {self.total_images}.")
    
    def jump_to_image_prompt(self, event=None):
        """Prompt the user to enter an image index and jump to that image."""
        def on_submit():
            try:
                index = int(entry.get()) - 1  # Convert to 0-based index
                self.jump_to_image(index)
                prompt_window.destroy()
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        
        # Create a new window for the prompt
        prompt_window = tk.Toplevel(self.root)
        prompt_window.title("Go to Image")
        prompt_window.geometry("500x200")
        
        # Label with instructions
        label = tk.Label(prompt_window, text=f"Enter image index (1-{self.total_images}):")
        label.pack(pady=10)

        # Entry widget for the user to input the index
        entry = tk.Entry(prompt_window)
        entry.pack(pady=5)

        # Button to submit the input
        submit_button = tk.Button(prompt_window, text="Go", command=on_submit)
        submit_button.pack(pady=5)

        # Focus on the entry box automatically
        entry.focus_set()

if __name__ == "__main__":
    root = tk.Tk()

    # Choose the image folder and the "selects" folder
    image_folder = filedialog.askdirectory(title="Select the folder with images")
    selects_folder = filedialog.askdirectory(title="Select the 'selects' folder")

    if image_folder and selects_folder:
        viewer = ImageViewer(root, image_folder, selects_folder)
        root.mainloop()
