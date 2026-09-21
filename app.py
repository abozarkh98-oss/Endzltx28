import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "zlt_x28_super_secret_key"

# دیتابیس کاربران
users_db = {
    "user123": {
        "password": "123",
        "username": "user123",
        "total": 50.0,
        "used": 18.4,
        "remaining": 31.6,
        "percent": 36,
        "days": 14,
        "private_message": ""
    }
}

ADMIN_CREDS = {"username": "admin", "password": "adminpassword123"}

@app.route('/')
def index():
    return render_template('index.html')

# --- بخش API کاربران ---
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if username in users_db and users_db[username]['password'] == password:
        user_info = users_db[username].copy()
        user_info['remaining'] = round(user_info['total'] - user_info['used'], 2)
        user_info['percent'] = int((user_info['used'] / user_info['total']) * 100) if user_info['total'] > 0 else 0
        user_info['success'] = True
        return jsonify(user_info)
    
    return jsonify({"success": False, "message": "نام کاربری یا رمز عبور اشتباه است!"}), 401

@app.route('/api/order', methods=['POST'])
def api_order():
    data = request.get_json() or {}
    pkg_name = data.get('packageName')
    price = data.get('price')
    return jsonify({
        "success": True,
        "message": f"درخواست خرید {pkg_name} به مبلغ {price} تومان ثبت شد."
    })

# --- بخش مدیریت (Admin Routes) ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_CREDS['username'] and password == ADMIN_CREDS['password']:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return "نام کاربری یا رمز عبور ادمین اشتباه است."
    return render_template('admin_login.html')

@app.route('/admin')
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html', users=users_db)

@app.route('/admin/update_user/<user_id>', methods=['POST'])
def update_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    if user_id in users_db:
        users_db[user_id]['total'] = float(request.form.get('total', 0))
        users_db[user_id]['used'] = float(request.form.get('used', 0))
        users_db[user_id]['days'] = int(request.form.get('days', 0))
        users_db[user_id]['remaining'] = round(users_db[user_id]['total'] - users_db[user_id]['used'], 2)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/private_msg/<user_id>', methods=['POST'])
def private_msg(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    if user_id in users_db:
        users_db[user_id]['private_message'] = request.form.get('private_message', '')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/broadcast', methods=['POST'])
def broadcast():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    msg = request.form.get('message', '')
    for u in users_db:
        users_db[u]['private_message'] = f"[اعلام عمومی]: {msg}"
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
