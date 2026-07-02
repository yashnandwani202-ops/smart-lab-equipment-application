from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = "smart_lab_secret_key"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "1234"
app.config["MYSQL_DB"] = "smart_lab_db"

mysql = MySQL(app)


@app.route("/")
def home():
    return render_template("index.html")


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


@app.route("/equipment")
def equipment():

    cursor = mysql.connection.cursor()

    cursor.execute("SELECT * FROM equipment")

    equipment = cursor.fetchall()

    cursor.close()

    return render_template("equipment.html", equipment=equipment)


@app.route("/student")
def student_dashboard():
    return render_template("student_dashboard.html")


@app.route("/faculty")
def faculty_dashboard():
    return render_template("faculty_dashboard.html")


@app.route("/admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)