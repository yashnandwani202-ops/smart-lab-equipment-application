from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file
import os


app = Flask(__name__)

# Secret key for sessions and flash messages
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "local-development-secret-key"
)

# Database configuration
app.config["MYSQL_HOST"] = os.environ.get(
    "MYSQL_HOST",
    "localhost"
)

app.config["MYSQL_USER"] = os.environ.get(
    "MYSQL_USER",
    "root"
)

app.config["MYSQL_PASSWORD"] = os.environ.get(
    "MYSQL_PASSWORD",
    "1234"
)

app.config["MYSQL_DB"] = os.environ.get(
    "MYSQL_DB",
    "smart_lab_db"
)

app.config["MYSQL_PORT"] = int(
    os.environ.get("MYSQL_PORT", "3306")
)

mysql_ssl_mode = os.environ.get("MYSQL_SSL_MODE")

if mysql_ssl_mode:
    app.config["MYSQL_CUSTOM_OPTIONS"] = {
        "ssl_mode": mysql_ssl_mode
    }

mysql = MySQL(app)




def require_role(role):
    if "user_id" not in session or session["role"] != role:
        return False
    return True


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)
        role = request.form["role"]

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            flash("Email already registered!")
            return redirect(url_for("register"))

        cursor.execute(
            """
            INSERT INTO users (full_name, email, password, role, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (full_name, email, hashed_password, role, "Active")
        )

        mysql.connection.commit()
        cursor.close()

        flash("Registration successful! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
             (email,)
)
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["full_name"] = user[1]
            session["email"] = user[2]
            session["role"] = user[4]

            role = user[4]

            if role == "student":
                return redirect(url_for("student_dashboard"))
            elif role == "faculty":
                return redirect(url_for("faculty_dashboard"))
            elif role == "admin":
                return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid email or password")

    return render_template("login.html")


@app.route("/student")
def student_dashboard():
    if not require_role("student"):
        return redirect(url_for("login"))

    return render_template("student_dashboard.html")


@app.route("/equipment")
def equipment():

    if not require_role("student"):
        return redirect(url_for("login"))

    search = request.args.get("search", "")
    category = request.args.get("category", "")
    availability = request.args.get("availability", "")

    query = "SELECT * FROM equipment WHERE 1=1"
    values = []

    if search:
        query += " AND (equipment_name LIKE %s OR category LIKE %s)"
        values.extend([f"%{search}%", f"%{search}%"])

    if category:
        query += " AND category = %s"
        values.append(category)

    if availability == "available":
        query += " AND available_quantity > 0"

    elif availability == "unavailable":
        query += " AND available_quantity = 0"

    cursor = mysql.connection.cursor()
    cursor.execute(query, tuple(values))
    equipment = cursor.fetchall()

    cursor.execute("SELECT DISTINCT category FROM equipment")
    categories = cursor.fetchall()

    cursor.close()

    return render_template(
        "equipment.html",
        equipment=equipment,
        search=search,
        category=category,
        availability=availability,
        categories=categories
    )


@app.route("/book/<int:equipment_id>")
def book_equipment(equipment_id):
    if not require_role("student"):
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO bookings (user_id, equipment_id, status) VALUES (%s, %s, %s)",
        (user_id, equipment_id, "Pending")
    )
    mysql.connection.commit()
    cursor.close()

    flash("Equipment booked successfully. Waiting for faculty approval.")
    return redirect(url_for("equipment"))


@app.route("/my-bookings")
def my_bookings():
    if not require_role("student"):
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT
            bookings.id,
            equipment.equipment_name,
            equipment.category,
            bookings.booking_date,
            bookings.status
        FROM bookings
        JOIN equipment
            ON bookings.equipment_id = equipment.id
        WHERE bookings.user_id = %s
    """, (user_id,))

    bookings = cursor.fetchall()
    cursor.close()

    return render_template("my_bookings.html", bookings=bookings)


@app.route("/faculty")
def faculty_dashboard():
    if not require_role("faculty"):
        return redirect(url_for("login"))

    return render_template("faculty_dashboard.html")


@app.route("/faculty-requests")
def faculty_requests():
    if not require_role("faculty"):
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT
            bookings.id,
            users.full_name,
            equipment.equipment_name,
            bookings.booking_date,
            bookings.status
        FROM bookings
        JOIN users ON bookings.user_id = users.id
        JOIN equipment ON bookings.equipment_id = equipment.id
    """)

    requests = cursor.fetchall()
    cursor.close()

    return render_template("faculty_requests.html", requests=requests)


@app.route("/approve/<int:booking_id>")
def approve_booking(booking_id):
    if not require_role("faculty"):
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT equipment_id, status FROM bookings WHERE id = %s",
        (booking_id,)
    )
    booking = cursor.fetchone()

    if booking:
        equipment_id = booking[0]
        current_status = booking[1]

        if current_status == "Pending":
            cursor.execute(
                "UPDATE equipment SET available_quantity = available_quantity - 1 WHERE id = %s AND available_quantity > 0",
                (equipment_id,)
            )

            cursor.execute(
                "UPDATE bookings SET status = %s WHERE id = %s",
                ("Approved", booking_id)
            )

            mysql.connection.commit()

    cursor.close()

    return redirect(url_for("faculty_requests"))


@app.route("/reject/<int:booking_id>")
def reject_booking(booking_id):
    if not require_role("faculty"):
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE bookings SET status = %s WHERE id = %s",
        ("Rejected", booking_id)
    )
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for("faculty_requests"))

@app.route("/admin-reports")
def admin_reports():
    if not require_role("admin"):
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM equipment")
    total_equipment = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'Approved'")
    approved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'Rejected'")
    rejected = cursor.fetchone()[0]

    cursor.close()

    return render_template(
        "admin_reports.html",
        total_users=total_users,
        total_equipment=total_equipment,
        total_bookings=total_bookings,
        pending=pending,
        approved=approved,
        rejected=rejected
    )

@app.route("/download-report")
def download_report():

    if not require_role("admin"):
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM equipment")
    total_equipment = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM bookings WHERE status = 'Pending'"
    )
    pending = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM bookings WHERE status = 'Approved'"
    )
    approved = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM bookings WHERE status = 'Rejected'"
    )
    rejected = cursor.fetchone()[0]

    cursor.close()

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph(
        "<b>LabNexa System Report</b>",
        styles["Title"]
    )

    generated_date = Paragraph(
        f"Generated on: {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
        styles["Normal"]
    )

    elements.append(title)
    elements.append(Spacer(1, 12))
    elements.append(generated_date)
    elements.append(Spacer(1, 25))

    report_data = [
        ["Report Category", "Value"],
        ["Total Users", total_users],
        ["Total Equipment", total_equipment],
        ["Total Bookings", total_bookings],
        ["Pending Requests", pending],
        ["Approved Bookings", approved],
        ["Rejected Bookings", rejected]
    ]

    report_table = Table(
        report_data,
        colWidths=[300, 120]
    )

    report_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),

            ("ALIGN", (1, 1), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                colors.HexColor("#F1F5F9")
            ]),

            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12)
        ])
    )

    elements.append(report_table)
    elements.append(Spacer(1, 25))

    footer = Paragraph(
        "Generated by LabNexa Laboratory Equipment Management System",
        styles["Normal"]
    )

    elements.append(footer)

    document.build(elements)

    buffer.seek(0)

    filename = (
        f"labnexa_system_report_"
        f"{datetime.now().strftime('%Y-%m-%d')}.pdf"
    )

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )


@app.route("/admin")
def admin_dashboard():
    if not require_role("admin"):
        return redirect(url_for("login"))

    return render_template("admin_dashboard.html")


@app.route("/admin-equipment")
def admin_equipment():
    if not require_role("admin"):
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM equipment")
    equipment = cursor.fetchall()
    cursor.close()

    return render_template("admin_equipment.html", equipment=equipment)


@app.route("/add-equipment", methods=["GET", "POST"])
def add_equipment():
    if not require_role("admin"):
        return redirect(url_for("login"))

    if request.method == "POST":
        equipment_name = request.form["equipment_name"]
        category = request.form["category"]
        quantity = request.form["quantity"]
        available_quantity = request.form["available_quantity"]
        status = request.form["status"]

        cursor = mysql.connection.cursor()
        cursor.execute(
            """
            INSERT INTO equipment
            (equipment_name, category, quantity, available_quantity, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (equipment_name, category, quantity, available_quantity, status)
        )
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for("admin_equipment"))

    return render_template("add_equipment.html")


@app.route("/edit-equipment/<int:equipment_id>", methods=["GET", "POST"])
def edit_equipment(equipment_id):
    if not require_role("admin"):
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    if request.method == "POST":
        equipment_name = request.form["equipment_name"]
        category = request.form["category"]
        quantity = request.form["quantity"]
        available_quantity = request.form["available_quantity"]
        status = request.form["status"]

        cursor.execute(
            """
            UPDATE equipment
            SET equipment_name=%s,
                category=%s,
                quantity=%s,
                available_quantity=%s,
                status=%s
            WHERE id=%s
            """,
            (equipment_name, category, quantity, available_quantity, status, equipment_id)
        )
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for("admin_equipment"))

    cursor.execute("SELECT * FROM equipment WHERE id = %s", (equipment_id,))
    equipment = cursor.fetchone()
    cursor.close()

    return render_template("edit_equipment.html", equipment=equipment)


@app.route("/delete-equipment/<int:equipment_id>")
def delete_equipment(equipment_id):
    if not require_role("admin"):
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM equipment WHERE id = %s", (equipment_id,))
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for("admin_equipment"))

@app.route("/add-user", methods=["GET", "POST"])
def add_user():

    if not require_role("admin"):
        return redirect(url_for("login"))

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)
        role = request.form["role"]
        status = request.form["status"]

        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            INSERT INTO users
            (full_name, email, password, role, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
           (full_name, email, hashed_password, role, status) 
        )

        mysql.connection.commit()
        cursor.close()

        return redirect(url_for("admin_users"))

    return render_template("add_user.html")

@app.route("/edit-user/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):

    if not require_role("admin"):
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        status = request.form["status"]

        if password:
            hashed_password = generate_password_hash(password)

            cursor.execute(
                """
                UPDATE users
                SET full_name=%s,
                    email=%s,
                    password=%s,
                    role=%s,
                    status=%s
                WHERE id=%s
                """,
                (full_name, email, hashed_password, role, status, user_id)
            )
        else:
            cursor.execute(
                """
                UPDATE users
                SET full_name=%s,
                    email=%s,
                    role=%s,
                    status=%s
                WHERE id=%s
                """,
                (full_name, email, role, status, user_id)
            )

        mysql.connection.commit()
        cursor.close()

        return redirect(url_for("admin_users"))

    cursor.execute(
        "SELECT * FROM users WHERE id = %s",
        (user_id,)
    )

    user = cursor.fetchone()
    cursor.close()

    return render_template("edit_user.html", user=user)

@app.route("/delete-user/<int:user_id>")
def delete_user(user_id):

    if not require_role("admin"):
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    cursor.execute(
        "DELETE FROM users WHERE id = %s",
        (user_id,)
    )

    mysql.connection.commit()
    cursor.close()

    return redirect(url_for("admin_users"))


@app.route("/admin-users")
def admin_users():
    if not require_role("admin"):
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()

    return render_template("admin_users.html", users=users)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)