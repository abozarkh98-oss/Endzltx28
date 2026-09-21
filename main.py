import os
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, jsonify, request, session, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key"
)

database_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://", "postgresql+psycopg://", 1
    )
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================
# DATABASE MODELS
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    is_admin = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    total_gb = db.Column(
        db.Float,
        default=0
    )

    used_gb = db.Column(
        db.Float,
        default=0
    )

    remaining_gb = db.Column(
        db.Float,
        default=0
    )

    days_left = db.Column(
        db.Integer,
        default=0
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


class Package(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    category = db.Column(
        db.String(20),
        nullable=False
    )

    name = db.Column(
        db.String(120),
        nullable=False
    )

    data = db.Column(
        db.String(80),
        nullable=False
    )

    price = db.Column(
        db.Integer,
        nullable=False
    )

    description = db.Column(
        db.Text,
        default=""
    )

    tag = db.Column(
        db.String(80),
        default=""
    )

    active = db.Column(
        db.Boolean,
        default=True
    )


class Order(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    package_id = db.Column(
        db.Integer,
        db.ForeignKey("package.id"),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship(
        "User",
        backref="orders"
    )

    package = db.relationship(
        "Package"
    )


class Message(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    sender = db.Column(
        db.String(20),
        nullable=False
    )

    text = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship(
        "User",
        backref="messages"
    )


# =========================
# AUTH
# =========================

def current_user():
    uid = session.get("user_id")

    if not uid:
        return None

    return db.session.get(User, uid)


def login_required(fn):

    @wraps(fn)
    def wrapper(*args, **kwargs):

        if not current_user():
            return jsonify({
                "success": False,
                "message": "ابتدا وارد حساب شوید."
            }), 401

        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):

    @wraps(fn)
    def wrapper(*args, **kwargs):

        user = current_user()

        if not user or not user.is_admin:
            return jsonify({
                "success": False,
                "message": "دسترسی مدیر لازم است."
            }), 403

        return fn(*args, **kwargs)

    return wrapper


# =========================
# JSON HELPERS
# =========================

def user_json(user):

    return {
        "id": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
        "total": user.total_gb,
        "used": user.used_gb,
        "remaining": user.remaining_gb,
        "days_left": user.days_left,
        "active": user.active
    }


def package_json(package):

    return {
        "id": package.id,
        "category": package.category,
        "name": package.name,
        "data": package.data,
        "price": package.price,
        "desc": package.description,
        "tag": package.tag
    }


# =========================
# PAGES
# =========================

@app.get("/")
def index():

    return render_template(
        "index.html"
    )


@app.get("/admin")
def admin_page():

    user = current_user()

    if not user or not user.is_admin:
        return redirect(
            url_for("index")
        )

    return render_template(
        "admin.html"
    )


# =========================
# PACKAGES
# =========================

@app.get("/api/packages")
def api_packages():

    packages = (
        Package.query
        .filter_by(active=True)
        .order_by(Package.id)
        .all()
    )

    return jsonify([
        package_json(p)
        for p in packages
    ])


# =========================
# LOGIN
# =========================

@app.post("/api/login")
def api_login():

    data = request.get_json(
        silent=True
    ) or {}

    username = (
        data.get("username") or ""
    ).strip()

    password = (
        data.get("password") or ""
    )

    user = User.query.filter_by(
        username=username
    ).first()

    if (
        not user
        or not user.active
        or not check_password_hash(
            user.password_hash,
            password
        )
    ):

        return jsonify({
            "success": False,
            "message": "نام کاربری یا رمز عبور اشتباه است."
        }), 401

    session["user_id"] = user.id

    return jsonify({
        "success": True,
        **user_json(user)
    })


@app.post("/api/logout")
def api_logout():

    session.clear()

    return jsonify({
        "success": True
    })


@app.get("/api/me")
@login_required
def api_me():

    return jsonify({
        "success": True,
        **user_json(
            current_user()
        )
    })


# =========================
# ORDERS
# =========================

@app.post("/api/orders")
@login_required
def api_order():

    user = current_user()

    data = request.get_json(
        silent=True
    ) or {}

    package = db.session.get(
        Package,
        data.get("package_id")
    )

    if not package or not package.active:

        return jsonify({
            "success": False,
            "message": "بسته پیدا نشد."
        }), 404

    order = Order(
        user_id=user.id,
        package_id=package.id,
        status="pending"
    )

    db.session.add(order)

    db.session.commit()

    return jsonify({
        "success": True,
        "order_id": order.id,
        "status": order.status
    })


# =========================
# USER MESSAGES
# =========================

@app.get("/api/messages")
@login_required
def api_messages():

    messages = (
        Message.query
        .filter_by(
            user_id=current_user().id
        )
        .order_by(
            Message.created_at.asc()
        )
        .all()
    )

    return jsonify([
        {
            "id": message.id,
            "sender": message.sender,
            "text": message.text,
            "created_at": message.created_at.isoformat()
        }
        for message in messages
    ])


@app.post("/api/messages")
@login_required
def api_send_message():

    data = request.get_json(
        silent=True
    ) or {}

    text = (
        data.get("text") or ""
    ).strip()

    if not text:

        return jsonify({
            "success": False,
            "message": "متن پیام خالی است."
        }), 400

    message = Message(
        user_id=current_user().id,
        sender="user",
        text=text
    )

    db.session.add(message)

    db.session.commit()

    return jsonify({
        "success": True,
        "id": message.id
    })


# =========================
# ADMIN USERS
# =========================

@app.get("/api/admin/users")
@admin_required
def admin_users():

    users = (
        User.query
        .order_by(User.id)
        .all()
    )

    return jsonify([
        user_json(user)
        for user in users
    ])


@app.patch("/api/admin/users/<int:user_id>")
@admin_required
def admin_update_user(user_id):

    user = db.session.get(
        User,
        user_id
    )

    if not user:

        return jsonify({
            "success": False,
            "message": "کاربر پیدا نشد."
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    fields = (
        "total_gb",
        "used_gb",
        "remaining_gb",
        "days_left",
        "active"
    )

    for field in fields:

        if field in data:
            setattr(
                user,
                field,
                data[field]
            )

    if (
        "remaining_gb" not in data
        and (
            "total_gb" in data
            or "used_gb" in data
        )
    ):

        user.remaining_gb = max(
            0,
            float(user.total_gb or 0)
            - float(user.used_gb or 0)
        )

    db.session.commit()

    return jsonify({
        "success": True,
        **user_json(user)
    })


# =========================
# ADMIN MESSAGE
# =========================

@app.post("/api/admin/users/<int:user_id>/message")
@admin_required
def admin_message(user_id):

    user = db.session.get(
        User,
        user_id
    )

    if not user:

        return jsonify({
            "success": False,
            "message": "کاربر پیدا نشد."
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    text = (
        data.get("text") or ""
    ).strip()

    if not text:

        return jsonify({
            "success": False,
            "message": "متن پیام خالی است."
        }), 400

    message = Message(
        user_id=user_id,
        sender="admin",
        text=text
    )

    db.session.add(message)

    db.session.commit()

    return jsonify({
        "success": True
    })


# =========================
# BROADCAST
# =========================

@app.post("/api/admin/broadcast")
@admin_required
def admin_broadcast():

    data = request.get_json(
        silent=True
    ) or {}

    text = (
        data.get("text") or ""
    ).strip()

    if not text:

        return jsonify({
            "success": False,
            "message": "متن پیام خالی است."
        }), 400

    users = (
        User.query
        .filter_by(
            is_admin=False,
            active=True
        )
        .all()
    )

    for user in users:

        db.session.add(
            Message(
                user_id=user.id,
                sender="admin",
                text=text
            )
        )

    db.session.commit()

    return jsonify({
        "success": True,
        "count": len(users)
    })


# =========================
# ADMIN ORDERS
# =========================

@app.get("/api/admin/orders")
@admin_required
def admin_orders():

    orders = (
        Order.query
        .order_by(
            Order.id.desc()
        )
        .all()
    )

    return jsonify([
        {
            "id": order.id,
            "username": order.user.username,
            "package": order.package.name,
            "price": order.package.price,
            "status": order.status,
            "created_at": order.created_at.isoformat()
        }
        for order in orders
    ])


@app.patch("/api/admin/orders/<int:order_id>")
@admin_required
def admin_order_status(order_id):

    order = db.session.get(
        Order,
        order_id
    )

    if not order:

        return jsonify({
            "success": False,
            "message": "سفارش پیدا نشد."
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    status = (
        data.get("status") or ""
    ).strip()

    allowed = {
        "pending",
        "paid",
        "completed",
        "cancelled"
    }

    if status not in allowed:

        return jsonify({
            "success": False,
            "message": "وضعیت نامعتبر است."
        }), 400

    order.status = status

    db.session.commit()

    return jsonify({
        "success": True
    })


# =========================
# INITIAL DATABASE
# =========================

def seed():

    db.create_all()

    admin_username = os.environ.get(
        "ADMIN_USERNAME",
        "admin"
    )

    admin_password = os.environ.get(
        "ADMIN_PASSWORD",
        "ChangeMe123!"
    )

    admin = User.query.filter_by(
        username=admin_username
    ).first()

    if not admin:

        admin = User(
            username=admin_username,
            password_hash=generate_password_hash(
                admin_password
            ),
            is_admin=True,
            total_gb=0,
            used_gb=0,
            remaining_gb=0,
            days_left=0
        )

        db.session.add(admin)

    if Package.query.count() == 0:

        packages = [

            (
                "daily",
                "بسته ۱ روزه",
                "۱ گیگابایت",
                15000,
                "بسته اقتصادی روزانه مناسب کارهای سبک و پیام‌رسان‌ها",
                "اقتصادی"
            ),

            (
                "daily",
                "بسته ۱ روزه",
                "۲ گیگابایت",
                20000,
                "سرعت مناسب وب‌گردی و شبکه‌های اجتماعی",
                "پرفروش"
            ),

            (
                "daily",
                "بسته ۱ روزه",
                "۳ گیگابایت",
                30000,
                "حجم مطلوب برای استفاده یک روزه",
                "استاندارد"
            ),

            (
                "daily",
                "بسته ۱ روزه ویژه",
                "۵ گیگابایت",
                45000,
                "همراه با تخفیف ویژه مصرف روزانه بالا",
                "تخفیف‌دار"
            ),

            (
                "weekly",
                "بسته ۷ روزه استاندارد",
                "۵ گیگابایت",
                50000,
                "مقرون‌به‌صرفه برای یک هفته",
                "اقتصادی"
            ),

            (
                "weekly",
                "بسته ۷ روزه پرطرفدار",
                "۷ گیگابایت",
                70000,
                "مناسب استفاده روزمره هفتگی",
                "پرفروش"
            ),

            (
                "weekly",
                "بسته ۷ روزه حرفه‌ای",
                "۹ گیگابایت",
                90000,
                "برای مصرف هفتگی سنگین",
                "پیشنهاد"
            ),

            (
                "monthly",
                "بسته ۳۰ روزه استاندارد",
                "۵ گیگابایت",
                65000,
                "بسته پایه ماهانه",
                "اقتصادی"
            ),

            (
                "monthly",
                "بسته ۳۰ روزه متوسط",
                "۱۰ گیگابایت",
                130000,
                "مناسب کاربران کم‌مصرف",
                "متوسط"
            ),

            (
                "monthly",
                "بسته ۳۰ روزه سنگین",
                "۵۰ گیگابایت",
                600000,
                "برای دانلود و مصرف سنگین",
                "پرفروش"
            ),

            (
                "monthly",
                "بسته شبانه ماهانه VIP",
                "نامحدود (۲ تا ۹ صبح)",
                120000,
                "دانلود سنگین در ساعات شبانه",
                "شبانه VIP"
            )
        ]

        for item in packages:

            db.session.add(
                Package(
                    category=item[0],
                    name=item[1],
                    data=item[2],
                    price=item[3],
                    description=item[4],
                    tag=item[5]
                )
            )

    db.session.commit()


# =========================
# START
# =========================

with app.app_context():
    seed()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                "5000"
            )
        ),
        debug=False
  )
