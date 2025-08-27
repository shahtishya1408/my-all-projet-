from flask import Flask, request, redirect, session
import sqlite3, random

app = Flask(__name__)
app.secret_key = 'secret'

# ------------------ Database Connection ------------------
def get_db_connection():
    conn = sqlite3.connect('pharmacy.db')
    conn.row_factory = sqlite3.Row
    return conn

# ------------------ Helper: HTML Template ------------------
def render(body):
    return f"""
    <html><head><title>Pharmacy Kiosk</title></head>
    <body style='font-family:sans-serif; padding:20px;'>{body}</body></html>
    """

# ------------------ Home Page ------------------
@app.route('/')
def home():
    if 'uid' in session:
        role = session['role']
        return redirect(f'/{role}_dashboard')
    return render("""
        <h2>Pharmacy Kiosk System</h2>
        <a href='/register'>Register</a> | 
        <a href='/login'>Login</a>
    """)

# ------------------ Register ------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        conn.close()
        return redirect('/login')
    return render("""
        <h3>Register</h3>
        <form method='post'>
            <input name='username' placeholder='Username' required><br>
            <input name='password' type='password' placeholder='Password' required><br>
            <select name='role'>
                <option value='admin'>Admin</option>
                <option value='customer'>Customer</option>
                <option value='delivery'>Delivery Partner</option>
            </select><br>
            <button>Register</button>
        </form>
    """)

# ------------------ Login ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
        conn.close()
        if user:
            session['uid'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(f"/{user['role']}_dashboard")
        else:
            return render("<p>Invalid credentials.</p><a href='/login'>Try again</a>")
    return render("""
        <h3>Login</h3>
        <form method='post'>
            <input name='username' placeholder='Username' required><br>
            <input name='password' type='password' placeholder='Password' required><br>
            <button>Login</button>
        </form>
    """)

# ------------------ Logout ------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ------------------ Admin Dashboard ------------------
@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'uid' not in session or session['role'] != 'admin': return redirect('/')
    conn = get_db_connection()

    if request.method == 'POST':
        if 'medname' in request.form:
            conn.execute("INSERT INTO medicines (name, price, stock) VALUES (?, ?, ?)", 
                         (request.form['medname'], request.form['price'], request.form['stock']))
        elif 'assign' in request.form:
            conn.execute("UPDATE orders SET assigned_to=?, status='Assigned' WHERE id=?", 
                         (request.form['dp'], request.form['assign']))
        conn.commit()

    meds = conn.execute("SELECT * FROM medicines").fetchall()
    customers = conn.execute("SELECT * FROM users WHERE role='customer'").fetchall()
    dps = conn.execute("SELECT * FROM users WHERE role='delivery'").fetchall()
    orders = conn.execute("""
        SELECT o.*, u.username AS customer, m.name AS medicine 
        FROM orders o 
        JOIN users u ON o.user_id = u.id 
        JOIN medicines m ON o.med_id = m.id
    """).fetchall()
    conn.close()

    medlist = "".join([f"<li>{m['name']} - ₹{m['price']} ({m['stock']})</li>" for m in meds])
    orderrows = ""
    for o in orders:
        assign_form = ""
        if o['status'] == 'Placed':
            assign_form = f"<form method='post'><input type='hidden' name='assign' value='{o['id']}'><select name='dp'>" + \
                "".join([f"<option value='{d['id']}'>{d['username']}</option>" for d in dps]) + "</select><button>Assign</button></form>"
        orderrows += f"<tr><td>{o['id']}</td><td>{o['customer']}</td><td>{o['medicine']}</td><td>{o['qty']}</td><td>{o['status']}</td><td>{assign_form}</td></tr>"

    return render(f"""
        <h3>Admin Dashboard ({session['username']})</h3>
        <h4>Add Medicine</h4>
        <form method='post'>
            <input name='medname' placeholder='Medicine Name' required>
            <input name='price' type='number' placeholder='Price' required>
            <input name='stock' type='number' placeholder='Stock' required>
            <button>Add</button>
        </form>
        <h4>Medicines</h4><ul>{medlist}</ul>
        <h4>Orders</h4>
        <table border=1><tr><th>ID</th><th>Customer</th><th>Medicine</th><th>Qty</th><th>Status</th><th>Action</th></tr>{orderrows}</table>
        <a href='/logout'>Logout</a>
    """)

# ------------------ Customer Dashboard ------------------
@app.route('/customer_dashboard', methods=['GET', 'POST'])
def customer_dashboard():
    if 'uid' not in session or session['role'] != 'customer': return redirect('/')
    conn = get_db_connection()
    if request.method == 'POST':
        mid, qty = request.form['med'], int(request.form['qty'])
        med = conn.execute("SELECT stock FROM medicines WHERE id=?", (mid,)).fetchone()
        if med and med['stock'] >= qty:
            otp = str(random.randint(1000, 9999))
            conn.execute("INSERT INTO orders (user_id, med_id, qty, otp, status) VALUES (?, ?, ?, ?, 'Placed')", 
                         (session['uid'], mid, qty, otp))
            conn.execute("UPDATE medicines SET stock = stock - ? WHERE id=?", (qty, mid))
            conn.commit()
    meds = conn.execute("SELECT * FROM medicines").fetchall()
    orders = conn.execute("""
        SELECT o.id, m.name, o.qty, o.status 
        FROM orders o 
        JOIN medicines m ON o.med_id = m.id 
        WHERE o.user_id=?
    """, (session['uid'],)).fetchall()
    conn.close()

    med_dropdown = "".join([f"<option value='{m['id']}'>{m['name']} - ₹{m['price']} ({m['stock']})</option>" for m in meds])
    order_list = "".join([f"<li>#{o['id']} - {o['qty']} x {o['name']} - {o['status']}</li>" for o in orders])

    return render(f"""
        <h3>Customer Dashboard ({session['username']})</h3>
        <form method='post'>
            <select name='med'>{med_dropdown}</select>
            <input name='qty' type='number' placeholder='Quantity' required>
            <button>Place Order</button>
        </form>
        <h4>Your Orders</h4><ul>{order_list}</ul>
        <a href='/logout'>Logout</a>
    """)

# ------------------ Delivery Partner Dashboard ------------------
@app.route('/delivery_dashboard')
def delivery_dashboard():
    if 'uid' not in session or session['role'] != 'delivery': return redirect('/')
    conn = get_db_connection()
    orders = conn.execute("""
        SELECT o.id, m.name, o.qty, o.otp, u.username, o.status 
        FROM orders o 
        JOIN medicines m ON o.med_id = m.id 
        JOIN users u ON o.user_id = u.id 
        WHERE o.assigned_to = ? AND o.status = 'Assigned'
    """, (session['uid'],)).fetchall()
    conn.close()

    cards = ""
    for o in orders:
        cards += f"""
        <div style='border:1px solid #ccc;padding:10px;margin:10px;'>
            Order #{o['id']} - {o['qty']} x {o['name']} for {o['username']}<br>
            <form method='post' action='/verify_otp'>
                <input type='hidden' name='order_id' value='{o['id']}'>
                OTP: <input name='otp' required>
                <button>Verify & Deliver</button>
            </form>
        </div>
        """
    return render(f"<h3>Delivery Dashboard ({session['username']})</h3>{cards}<a href='/logout'>Logout</a>")

# ------------------ OTP Verification ------------------
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    if 'uid' not in session or session['role'] != 'delivery': return redirect('/')
    oid, otp_input = request.form['order_id'], request.form['otp']
    conn = get_db_connection()
    order = conn.execute("SELECT otp FROM orders WHERE id=? AND assigned_to=?", (oid, session['uid'])).fetchone()
    if order and order['otp'] == otp_input:
        conn.execute("UPDATE orders SET status='Delivered' WHERE id=?", (oid,))
        conn.commit()
        msg = "<p>Order marked as Delivered!</p>"
    else:
        msg = "<p>Incorrect OTP!</p>"
    conn.close()
    return msg + redirect('/delivery_dashboard')

# ------------------ Run App ------------------
if __name__ == '__main__':
    conn = get_db_connection()
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS medicines (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, stock INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, med_id INTEGER, qty INTEGER, otp TEXT, assigned_to INTEGER, status TEXT)")
    conn.commit()
    conn.close()
    app.run(debug=True)
