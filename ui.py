import os
import tkinter as tk
from tkinter import filedialog, Listbox, Scrollbar
from PIL import Image, ImageTk, ExifTags, ImageOps
import io
import json

def save_session(image_folder, selects_folder):
    """Save the session data (folder paths) to a file."""
    session_data = {
        "image_folder": image_folder,
        "selects_folder": selects_folder
    }
    with open('session.json', 'w') as session_file:
        json.dump(session_data, session_file)

def load_last_session():
    """Load the last session data if available."""
    try:
        with open('session.json', 'r') as session_file:
            session_data = json.load(session_file)
            return session_data.get("image_folder"), session_data.get("selects_folder")
    except FileNotFoundError:
        return None, None  # No session file found

class ImageViewer:
    def __init__(self, root, image_folder, selects_folder):
        self.root = root
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.bind("<Left>", self.show_previous_image)
        self.root.bind("<Right>", self.show_next_image)
        self.root.bind("<space>", self.pick_image)
        self.root.bind("g", self.jump_to_image_prompt)
        self.root.bind("<Shift-Left>", self.show_previous_selected_image)
        self.root.bind("<Shift-Right>", self.show_next_selected_image)
        self.root.bind("<BackSpace>", self.remove_image)

        self.image_folder = image_folder
        self.selects_folder = selects_folder

        # Sidebar width (to be considered when centering the image)
        self.sidebar_width = 200

        # Get total image count from the folder (for progressive loading)
        self.image_files = sorted([f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))],
                                  key=lambda x: os.path.getmtime(os.path.join(image_folder, x)))
        self.total_images = len(self.image_files)
        
        self.current_image_index = 0  # Start before the first image
        self.selected_files = []  # List to hold selected file indexes

        # Create sidebar for selected images (on the left)
        self.sidebar = tk.Frame(root, width=self.sidebar_width, bg='lightgrey')
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT)

        # Add scrollbar to sidebar
        self.scrollbar = Scrollbar(self.sidebar)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = Listbox(self.sidebar, width=30, height=50, yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind('<<ListboxSelect>>', self.on_sidebar_select)
        self.scrollbar.config(command=self.listbox.yview)

        # Create canvas to display images (on the right)
        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)

        # Create a label for image counter
        self.image_counter_label = tk.Label(self.canvas, text="", bg="white", font=("Helvetica", 14))
        self.image_counter_label.place(relx=0.95, rely=0.05, anchor=tk.NE)

        # Load selected images in the sidebar on start
        self.load_selected_images()

        # Load the first image when the user presses 'Right' or 'Next'
        self.root.after(100, self.show_image)

    def load_image_data(self, image_index):
        """Read the image data from local files (no database)."""
        file_name = self.image_files[image_index]
        file_path = os.path.join(self.image_folder, file_name)
        try:
            with open(file_path, 'rb') as file:
                binary_data = file.read()
                return binary_data
        except Exception as e:
            print(f"Error loading image {file_name}: {e}")
            return None

    def get_image_data(self, image_index):
        """Get the binary data and file name of the image at a given index."""
        if image_index < 0 or image_index >= self.total_images:
            print(f"Invalid image index: {image_index}")
            return None, None

        file_name = self.image_files[image_index]
        image_data = self.load_image_data(image_index)
        return file_name, image_data

    def correct_image_orientation(self, image):
        """Correct image orientation based on EXIF metadata."""
        try:
            exif = image._getexif()
            if exif:
                orientation = None
                for tag, value in ExifTags.TAGS.items():
                    if value == 'Orientation':
                        orientation = exif.get(tag)
                        break

                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError):
            pass
        return image

    def show_image(self):
        """Display the current image."""
        file_name, image_data = self.get_image_data(self.current_image_index)

        if image_data:
            try:
                image = Image.open(io.BytesIO(image_data))
                image = self.correct_image_orientation(image)

                # screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()

                available_width = self.canvas.winfo_width()
                image = self.resize_image(image, available_width, screen_height)

                center_x = available_width // 2
                center_y = screen_height // 2

                self.tk_image = ImageTk.PhotoImage(image)
                self.canvas.delete("all")
                self.canvas.create_image(center_x, center_y, image=self.tk_image, anchor=tk.CENTER)

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
            self.update_sidebar()  # Update sidebar after navigation
        else:
            print("Already at the last image.")

    def show_previous_image(self, event=None):
        """Show the previous image in the folder when navigating backward."""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_image()
            self.update_sidebar()  # Update sidebar after navigation
        else:
            print("Already at the first image.")


    def pick_image(self, event=None):
        """Create a symlink in the 'selects' folder for the current image."""
        file_name, _ = self.get_image_data(self.current_image_index)
        if file_name:
            link_path = os.path.join(self.selects_folder, file_name)
            source_path = os.path.join(self.image_folder, file_name)

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
            
            # If the current image is selected, highlight it in yellow
            if index == self.current_image_index:
                self.listbox.itemconfig(tk.END, {'bg': 'yellow'})
                self.listbox.see(tk.END)  # Scroll to this item
            else:
                self.listbox.itemconfig(tk.END, {'bg': 'white'})


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
            display_text = self.listbox.get(selected_index[0])
            index_str, file_name = display_text.split(' - ', 1)
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
        
        prompt_window = tk.Toplevel(self.root)
        prompt_window.title("Go to Image")
        prompt_window.geometry("500x200")
        
        label = tk.Label(prompt_window, text=f"Enter image index (1-{self.total_images}):")
        label.pack(pady=10)

        entry = tk.Entry(prompt_window)
        entry.pack(pady=5)

        submit_button = tk.Button(prompt_window, text="Go", command=on_submit)
        submit_button.pack(pady=5)

        entry.focus_set()
        self.update_sidebar()  # Update sidebar after navigation


    def show_previous_selected_image(self, event=None):
        """Go to the closest previous selected image from the current index."""
        if not self.selected_files:
            return  # No selected files

        # Find the closest previous selected image
        prev_index = None
        for idx in reversed(self.selected_files):
            if idx < self.current_image_index:
                prev_index = idx
                break

        if prev_index is not None:
            self.current_image_index = prev_index
            self.show_image()
        else:
            print("No previous selected image.")
        self.update_sidebar()  # Update sidebar after navigation


    def show_next_selected_image(self, event=None):
        """Go to the closest next selected image from the current index."""
        if not self.selected_files:
            return  # No selected files

        # Find the closest next selected image
        next_index = None
        for idx in self.selected_files:
            if idx > self.current_image_index:
                next_index = idx
                break

        if next_index is not None:
            self.current_image_index = next_index
            self.show_image()
        else:
            print("No next selected image.")
        self.update_sidebar()  # Update sidebar after navigation

    def remove_image(self, event=None):
        """Remove the current image from the selected list and delete the symlink."""
        if self.current_image_index in self.selected_files:
            # Get the filename and symlink path
            file_name = self.image_files[self.current_image_index]
            link_path = os.path.join(self.selects_folder, file_name)

            # Remove the symlink if it exists
            if os.path.exists(link_path):
                try:
                    os.unlink(link_path)
                    print(f"Unselected and removed symlink for: {file_name}")
                except Exception as e:
                    print(f"Error removing symlink for {file_name}: {e}")
            
            # Remove the image from the selected files list
            self.selected_files.remove(self.current_image_index)
            
            # Update the sidebar to reflect the change
            self.update_sidebar()
        else:
            print("Image is not in the selected list.")

if __name__ == "__main__":
    root = tk.Tk()

    # Load the last session if available
    last_image_folder, last_selects_folder = load_last_session()

    if last_image_folder and last_selects_folder:
        # Prompt to resume the last session
        resume_prompt = tk.messagebox.askyesno("Resume Last Session", f"Would you like to resume your last session?\n"
                                                                      f"Images: {last_image_folder}\n"
                                                                      f"Selects: {last_selects_folder}")
        if resume_prompt:
            image_folder = last_image_folder
            selects_folder = last_selects_folder
        else:
            image_folder = filedialog.askdirectory(title="Select the folder with images")
            selects_folder = filedialog.askdirectory(title="Select the 'selects' folder")
    else:
        # No previous session, ask the user for folders
        image_folder = filedialog.askdirectory(title="Select the folder with images")
        selects_folder = filedialog.askdirectory(title="Select the 'selects' folder")

    if image_folder and selects_folder:
        # Save the session for future use
        save_session(image_folder, selects_folder)

        # Initialize the viewer with the selected folders
        viewer = ImageViewer(root, image_folder, selects_folder)
        root.mainloop()
