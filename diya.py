import tkinter as tk
from tkinter import messagebox
import sqlite3
import random
import pywhatkit as kit
import datetime

root=tk.Tk()
root.title("BHAVIKA OPHARMACY")
root.geometry("400x300")
root.configure(bg="lightblue")
root.resizable(False, False)

# Function to check if the window is in fullscreen mode
def is_fullscreen():
    return root.attributes("-fullscreen")

def toggle_fullscreen(event=True):
    current_state = is_fullscreen()
    root.attributes("-fullscreen", not current_state)
    root.bind("<Escape>", lambda event: root.attributes("-fullscreen", False))  # Escape to exit fullscreen

import os
icon_path = os.path.join(os.path.dirname(__file__), "1.ico")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)
else:
    messagebox.showwarning("Warning", "Icon file '1.ico' not found. Default icon will be used.")


# Database setup
conn = sqlite3.connect('pharmacy.db')
c = conn.cursor()

# Create tables if not exist
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS delivery_partners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        stock INTEGER
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        medicine_name TEXT,
        quantity INTEGER,
        total_price REAL,
        upi_id TEXT,
        payment_status TEXT,
        status TEXT,
        delivery_address TEXT,
        otp TEXT,
        phone_number TEXT,
        delivery_partner TEXT
    )
''')
conn.commit()
role_var = tk.StringVar(value="user", name="role")
# Function to add a new user    
def add_user(username, password, role):
    try:
        if role == "user":
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        elif role == "admin":
            c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, password))
        elif role == "delivery":
            c.execute("INSERT INTO delivery_partners (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        messagebox.showinfo("Success", f"{role.capitalize()} added successfully!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))


# Function to delete all data
def delete_all_data():
    confirm = messagebox.askyesno(
        "Confirm Deletion", 
        "Are you sure you want to delete ALL data from the database?"
    )
    if not confirm:
        return
    try:
        for table in ("users", "admins", "delivery_partners", "medicines", "orders"):
            c.execute(f"DELETE FROM {table}")
        conn.commit()
        messagebox.showinfo("Success", "All data deleted successfully.")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))

# ================= LOGIN FUNCTION ======================

def login():
    username = user_entry.get()
    password = pass_entry.get()
    role = role_var.get()

    if role == "user":
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        if user:
            messagebox.showinfo("Login Success", f"Welcome {username}!")
            open_user_dashboard(username)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    elif role == "admin":
        c.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password))
        admin = c.fetchone()
        if admin:
            messagebox.showinfo("Login Success", f"Welcome Admin {username}!")
            open_admin_dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    elif role == "delivery":
        c.execute("SELECT * FROM delivery_partners WHERE username=? AND password=?", (username, password))
        delivery_partner = c.fetchone()
        if delivery_partner:
            messagebox.showinfo("Login Success", f"Welcome Delivery Partner {username}!")
            open_delivery_dashboard(username)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

# ================= USER DASHBOARD ======================
def open_user_dashboard(username):
    win = tk.Tk()
    win.title(f"User Dashboard - {username}")
    win.geometry("500x600")

    tk.Label(win, text="Medicine Name").grid(row=0, column=0)
    name_entry = tk.Entry(win)
    name_entry.grid(row=0, column=1)

    tk.Label(win, text="Quantity").grid(row=1, column=0)
    qty_entry = tk.Entry(win)
    qty_entry.grid(row=1, column=1)

    tk.Label(win, text="UPI ID").grid(row=2, column=0)
    upi_entry = tk.Entry(win)
    upi_entry.grid(row=2, column=1)

    tk.Label(win, text="Delivery Address").grid(row=3, column=0)
    address_entry = tk.Entry(win)
    address_entry.grid(row=3, column=1)

    tk.Label(win, text="Phone Number").grid(row=4, column=0)
    phone_entry = tk.Entry(win)
    phone_entry.grid(row=4, column=1)

    tk.Label(win, text="Payment Status").grid(row=5, column=0)
    payment_status = tk.StringVar(value="Pending")
    payment_menu = tk.OptionMenu(win, payment_status, "Pending", "Paid")
    payment_menu.grid(row=5, column=1)

    def place_order():
        name = name_entry.get()
        qty = qty_entry.get()
        upi = upi_entry.get()
        address = address_entry.get()
        phone = phone_entry.get()
        payment = payment_status.get()

        if not (name and qty and upi and address and phone):
            messagebox.showerror("Error", "Please fill all fields")
            return

        c.execute("SELECT * FROM medicines WHERE name=?", (name,))
        medicine = c.fetchone()

        if medicine:
            med_id, med_name, med_price, med_stock = medicine
            if int(qty) <= med_stock:
                total = med_price * int(qty)
                otp = str(random.randint(1000, 9999))

                c.execute("UPDATE medicines SET stock = stock - ? WHERE id=?", (int(qty), med_id))
                c.execute('''INSERT INTO orders 
                    (customer_name, medicine_name, quantity, total_price, upi_id, payment_status, status, delivery_address, otp, phone_number) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                    (username, name, qty, total, upi, payment, "Pending", address, otp, phone))
                conn.commit()

                # WhatsApp Message Send
                try:
                    now = datetime.datetime.now()
                    send_time_hour = now.hour
                    send_time_min = now.minute + 2
                    if send_time_min >= 60:
                        send_time_min -= 60
                        send_time_hour = (send_time_hour + 1) % 24

                    whatsapp_number = "+91" + phone  # India code
                    message_text = f"Hello {username},\nYour order for {qty} {name}(s) is placed.\nTotal Price: ₹{total}\nDelivery OTP: {otp}\nPayment Status: {payment}\nThank you for shopping with us! 🚑💊"
                    kit.sendwhatmsg(whatsapp_number, message_text, send_time_hour, send_time_min, wait_time=10, tab_close=True)
                    messagebox.showinfo("Order Placed", f"Order placed successfully!\nOTP sent on WhatsApp!\nYour OTP: {otp}")
                except Exception as e:
                    messagebox.showwarning("Order Placed", f"Order placed but WhatsApp failed.\nReason: {e}\nYour OTP: {otp}")

            else:
                messagebox.showerror("Error", "Insufficient stock")
        else:
            messagebox.showerror("Error", "Medicine not found")

    tk.Button(win, text="Place Order", command=place_order).grid(row=6, column=0, columnspan=2)

# ================ ADMIN DASHBOARD =======================
def open_admin_dashboard():
    win = tk.Tk()
    win.title("Admin Dashboard")
    win.geometry("600x500")

    tk.Label(win, text="Medicine Name").grid(row=0, column=0)
    med_name_entry = tk.Entry(win)
    med_name_entry.grid(row=0, column=1)

    tk.Label(win, text="Price").grid(row=1, column=0)
    price_entry = tk.Entry(win)
    price_entry.grid(row=1, column=1)

    tk.Label(win, text="Stock").grid(row=2, column=0)
    stock_entry = tk.Entry(win)
    stock_entry.grid(row=2, column=1)

    def add_medicine():
        name = med_name_entry.get()
        price = price_entry.get()
        stock = stock_entry.get()
        if name and price and stock:
            c.execute("INSERT INTO medicines (name, price, stock) VALUES (?, ?, ?)", (name, price, stock))
            conn.commit()
            messagebox.showinfo("Success", "Medicine Added Successfully!")
        else:
            messagebox.showerror("Error", "Please enter all fields")

    tk.Button(win, text="Add Medicine", command=add_medicine).grid(row=3, column=0, columnspan=2)

    def view_orders():
        orders_win = tk.Toplevel(win)
        orders_win.title("View Orders")
        orders_win.geometry("500x400")

        c.execute("SELECT * FROM orders")
        orders = c.fetchall()

        for i, order in enumerate(orders):
            tk.Label(orders_win, text=f"Order {i+1} - {order[1]} ordered {order[2]} x {order[3]}").grid(row=i, column=0)

    tk.Button(win, text="View Orders", command=view_orders).grid(row=4, column=0, columnspan=2)
   # ================= DELIVERY PARTNER DASHBOARD =======================
def open_delivery_dashboard(username):
    win = tk.Tk()
    win.title(f"Delivery Partner Dashboard - {username}")
    win.geometry("600x500")

    c.execute("SELECT * FROM orders WHERE delivery_partner IS NULL")
    orders = c.fetchall()

    for i, order in enumerate(orders):
        order_id, customer_name, medicine_name, qty, total, upi_id, payment_status, status, delivery_address, otp, phone_number, _ = order
        tk.Label(win, text=f"Order {i+1} - {medicine_name} x {qty} - Total: ₹{total}").grid(row=i, column=0)

        def complete_order(order_id, otp_entered):
            c.execute("UPDATE orders SET otp=? WHERE id=?", (otp_entered, order_id))
            conn.commit()
            messagebox.showinfo("Order Completed", f"Order {order_id} is completed!")

        tk.Entry(win).grid(row=i, column=1)  # OTP Entry
        tk.Button(win, text="Complete Order", command=lambda order_id=order_id: complete_order(order_id, otp_entered=win.winfo_children()[2*i + 1].get())).grid(row=i, column=2)

# ================= OTP ENTRY =======================
def show_order_details(order_id):
    win = tk.Tk()
    win.title(f"Order Details - {order_id}")

    c.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    order = c.fetchone()

    if order:
        order_id, customer_name, medicine_name, qty, total, upi_id, payment_status, status, delivery_address, otp, phone_number, _ = order

        c.execute("SELECT * FROM medicines WHERE name=?", (medicine_name,))
        medicine = c.fetchone()

    
    
    
    # Main menu for user

tk.Label(root, text="Username").pack(pady=5)
user_entry = tk.Entry(root)
user_entry.pack()

tk.Label(root, text="Password").pack(pady=5)
pass_entry = tk.Entry(root, show="*")
pass_entry.pack()

tk.Button(root, text="Login", command=login).pack(pady=10)
root.mainloop()


