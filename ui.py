import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

class ImageViewer:
    def __init__(self, root, image_folder, selects_folder):
        self.root = root
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.bind("<Left>", self.show_previous_image)
        self.root.bind("<Right>", self.show_next_image)
        self.root.bind("<Return>", self.pick_image)

        self.image_folder = image_folder
        self.selects_folder = selects_folder
        self.image_files = sorted([f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])
        self.current_image_index = 0
        self.cached_images = {}

        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Preload the first few images
        self.cache_images(3)
        self.show_image()

    def cache_images(self, lookahead=3):
        """Cache the current and next few images."""
        start = self.current_image_index
        end = min(self.current_image_index + lookahead, len(self.image_files))

        for i in range(start, end):
            if i not in self.cached_images:
                image_path = os.path.join(self.image_folder, self.image_files[i])
                image = Image.open(image_path)
                self.cached_images[i] = image

    def show_image(self):
        image = self.cached_images.get(self.current_image_index)
        if image is None:
            image_path = os.path.join(self.image_folder, self.image_files[self.current_image_index])
            image = Image.open(image_path)
            self.cached_images[self.current_image_index] = image

        # Resize the image while keeping aspect ratio
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        image = self.resize_image(image, screen_width, screen_height)

        # Display the image
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(screen_width//2, screen_height//2, image=self.tk_image, anchor=tk.CENTER)
        self.cache_images()  # Cache next images

    def resize_image(self, image, max_width, max_height):
        img_width, img_height = image.size
        ratio = min(max_width/img_width, max_height/img_height)
        new_size = (int(img_width * ratio), int(img_height * ratio))
        return image.resize(new_size, Image.LANCZOS)

    def show_next_image(self, event=None):
        if self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self.show_image()

    def show_previous_image(self, event=None):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_image()

    def pick_image(self, event=None):
        """Create a symlink in the 'selects' folder for the current image."""
        current_image = self.image_files[self.current_image_index]
        source_path = os.path.join(self.image_folder, current_image)
        link_path = os.path.join(self.selects_folder, current_image)

        # Create symlink to the selected image
        if not os.path.exists(link_path):
            os.symlink(source_path, link_path)
            print(f"Selected: {current_image}")

    def exit_fullscreen(self, event=None):
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
