import os
import psutil
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "zlt_x28_super_secret_key"

ADMIN_CREDS = {"username": "admin", "password": "Khani_1396"}

# دیتابیس کاربران
users_db = {
    "user123": {
        "password": "123",
        "username": "user123",
        "total": 50.0,
        "used": 18.4,
        "days": 14,
        "private_message": "",
        "purchased_packages": []
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    # ورود ادمین
    if username == ADMIN_CREDS['username'] and password == ADMIN_CREDS['password']:
        session['admin_logged_in'] = True
        return jsonify({"success": True, "is_admin": True, "redirect": "/admin/dashboard"})

    # ورود کاربر عادی
    if username in users_db and users_db[username]['password'] == password:
        session['user'] = username
        u_data = users_db[username]
        has_service = u_data['total'] > 0
        remaining = round(u_data['total'] - u_data['used'], 2) if has_service else 0
        percent = int((u_data['used'] / u_data['total']) * 100) if (has_service and u_data['total'] > 0) else 0

        return jsonify({
            "success": True,
            "is_admin": False,
            "username": username,
            "total": u_data['total'],
            "used": u_data['used'],
            "remaining": remaining,
            "days": u_data['days'],
            "percent": percent,
            "has_service": has_service,
            "purchased_packages": u_data['purchased_packages'],
            "private_message": u_data.get('private_message', '')
        })
    
    return jsonify({"success": False, "message": "نام کاربری یا رمز عبور اشتباه است!"}), 401

@app.route('/api/order', methods=['POST'])
def api_order():
    data = request.get_json() or {}
    username = session.get('user')
    pkg_name = data.get('packageName')
    price = data.get('price')

    if not username or username not in users_db:
        return jsonify({"success": False, "message": "برای خرید بسته ابتدا باید وارد حساب کاربری خود شوید!"}), 401

    # افزودن بسته به خریدهای کاربر
    order_item = {"package": pkg_name, "price": price}
    users_db[username]['purchased_packages'].append(order_item)

    return jsonify({
        "success": True,
        "message": f"بسته {pkg_name} با موفقیت ثبت شد."
    })

# --- بخش مدیریت (Admin) ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == ADMIN_CREDS['username'] and password == ADMIN_CREDS['password']:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error="نام کاربری یا رمز عبور ادمین اشتباه است!")
    return render_template('admin_login.html')

@app.route('/admin')
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    system_stats = {
        "cpu_usage": psutil.cpu_percent(interval=0.3),
        "ram_usage": psutil.virtual_memory().percent,
        "ram_total": round(psutil.virtual_memory().total / (1024**3), 2),
        "ram_used": round(psutil.virtual_memory().used / (1024**3), 2)
    }

    return render_template('admin_dashboard.html', users=users_db, stats=system_stats)

@app.route('/admin/add_user', methods=['POST'])
def add_user():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    total = float(request.form.get('total', 0.0))
    days = int(request.form.get('days', 0))

    if username and username not in users_db:
        users_db[username] = {
            "password": password,
            "username": username,
            "total": total,
            "used": 0.0,
            "days": days,
            "private_message": "",
            "purchased_packages": []
        }
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_user/<user_id>', methods=['POST'])
def update_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    if user_id in users_db:
        users_db[user_id]['password'] = request.form.get('password', users_db[user_id]['password'])
        users_db[user_id]['total'] = float(request.form.get('total', 0))
        users_db[user_id]['used'] = float(request.form.get('used', 0))
        users_db[user_id]['days'] = int(request.form.get('days', 0))
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<user_id>')
def delete_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    if user_id in users_db:
        del users_db[user_id]
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
        users_db[u]['private_message'] = f"[اعلام همگانی]: {msg}"
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
