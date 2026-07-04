from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = "smart_lab_secret_key"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "1234"
app.config["MYSQL_DB"] = "smart_lab_db"

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
            (full_name, email, password, role, "Active")
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
            "SELECT * FROM users WHERE email = %s AND password = %s",
            (email, password)
        )
        user = cursor.fetchone()
        cursor.close()

        if user:
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

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM equipment")
    equipment = cursor.fetchall()
    cursor.close()

    return render_template("equipment.html", equipment=equipment)


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