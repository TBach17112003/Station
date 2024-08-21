import customtkinter as ctk
from tkinter import messagebox
import home
import home_With_Cloud
class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Login")
        self.root.geometry("300x180")
        self.root.attributes("-topmost", True)

        # Set dark mode background color
        self.bg_color = "#2E2E2E"
        self.root.configure(bg=self.bg_color)
    
        self.frame = ctk.CTkFrame(root, bg_color=self.bg_color)
        self.frame.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

        self.username_label = ctk.CTkLabel(self.frame, text="Username", bg_color=self.bg_color, text_color="white", font=("MS Sans Serif", 14))
        self.username_label.pack(pady=5)

        self.username_entry = ctk.CTkEntry(self.frame)
        self.username_entry.pack(pady=5)

        self.password_label = ctk.CTkLabel(self.frame, text="Password", bg_color=self.bg_color, text_color="white", font=("MS Sans Serif", 14))
        self.password_label.pack(pady=5)

        self.password_entry = ctk.CTkEntry(self.frame, show="*")
        self.password_entry.pack(pady=5)

        self.login_button = ctk.CTkButton(self.frame, text="Login", command=self.validate_login, fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        self.login_button.pack(pady=10)

        # Bind the Enter key to the login function
        self.root.bind('<Return>', self.on_enter_key)

    def on_enter_key(self, event):
        self.validate_login()

    def validate_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if username == "admin" and password == "admin@@":
            self.root.destroy()
            main_window = ctk.CTk()
            home_With_Cloud.HomeWindow(main_window)
            main_window.mainloop()
        else:
            messagebox.showerror("Error", "Incorrect username or password")
             

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    root = ctk.CTk()
    app = home_With_Cloud.HomeWindow(root)
    root.mainloop()