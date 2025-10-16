import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

class MyNotepad:
    def __init__(self, root):
        self.root = root
        self.root.title("My Notepad - New File")
        self.current_file = None

        # Create the menu bar
        self.create_menu()

        # Create the TextBox
        self.text_area = tk.Text(self.root, wrap='word')
        self.text_area.pack(expand=1, fill='both')

        # Bind shortcuts
        self.root.bind('<Control-n>', lambda event: self.new_file())
        self.root.bind('<Control-o>', lambda event: self.open_file())
        self.root.bind('<Control-s>', lambda event: self.save_file())
        self.root.bind('<Control-q>', lambda event: self.quit_app())

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='New File', accelerator='Ctrl+N', command=self.new_file)
        file_menu.add_command(label='Open File', accelerator='Ctrl+O', command=self.open_file)
        file_menu.add_command(label='Save File', accelerator='Ctrl+S', command=self.save_file)
        file_menu.add_command(label='Save As', command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label='Quit', accelerator='Ctrl+Q', command=self.quit_app)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Help', menu=help_menu)
        help_menu.add_command(label='About', command=self.show_about)

    def new_file(self):
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("My Notepad - New File")

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, 'r') as file:
                content = file.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, content)
                self.current_file = file_path
                self.root.title(f"My Notepad - {file_path}")

    def save_file(self):
        if self.current_file:
            with open(self.current_file, 'w') as file:
                content = self.text_area.get(1.0, tk.END)
                file.write(content)
        else:
            self.save_as()

    def save_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                content = self.text_area.get(1.0, tk.END)
                file.write(content)
                self.current_file = file_path
                self.root.title(f"My Notepad - {file_path}")

    def quit_app(self):
        self.root.quit()

    def show_about(self):
        messagebox.showinfo("About", "My Notepad")

if __name__ == "__main__":
    root = tk.Tk()
    app = MyNotepad(root)
    root.mainloop()