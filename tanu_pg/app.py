from flask import Flask, render_template, request, redirect, session, send_file
import os
import csv
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "mysecret"

UPLOAD_FOLDER = "static/uploads"
DATA_FOLDER = "data"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure folders exist
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Admin credentials
USERNAME = "admin"
PASSWORD = "1234"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# home page
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]
        if user == USERNAME and pwd == PASSWORD:
            session["logged_in"] = True
            return redirect("/admin")
        else:
            return "<h3>Invalid login!</h3><a href='/login'>Try Again</a>"
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect("/")


# view_pg
@app.route("/view", methods=["GET", "POST"])
def view_pgs():
    city = request.args.get("city")
    min_rent = request.args.get("min_rent")
    max_rent = request.args.get("max_rent")
    min_rooms = request.args.get("min_rooms")
    max_rooms = request.args.get("max_rooms")

    pgs = []
    file_path = os.path.join(DATA_FOLDER, "pg_list.txt")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            data = file.read().strip().split("\n\n")
            for block in data:
                pg_info = {}
                for line in block.strip().split("\n"):
                    if ": " in line:
                        key, val = line.split(": ", 1)
                        pg_info[key.strip()] = val.strip()
                if city and city.lower() not in pg_info.get("City", "").lower():
                    continue
                if min_rent and int(pg_info.get("Rent", 0)) < int(min_rent):
                    continue
                if max_rent and int(pg_info.get("Rent", 0)) > int(max_rent):
                    continue
                if min_rooms and int(pg_info.get("Rooms", 0)) < int(min_rooms):
                    continue
                if max_rooms and int(pg_info.get("Rooms", 0)) > int(max_rooms):
                    continue
                pgs.append(pg_info)
    return render_template("view_pgs.html", pgs=pgs)


# register_pg
@app.route("/register-pg", methods=["GET", "POST"])
def register_pg():
    file_path = os.path.join(DATA_FOLDER, "pg_list.txt")

    if request.method == "POST":
        name = request.form["name"]
        city = request.form["city"]
        rooms = request.form["rooms"]
        rent = request.form["rent"]
        image_file = request.files["image"]
        image_path = ""

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)
            image_path = f"/static/uploads/{filename}"  # This path will be used in HTML

        pg_id = "PG1"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                existing = file.read().strip().split("\n\n")
                pg_id = "PG" + str(len(existing) + 1)

        with open(file_path, "a", encoding="utf-8", newline="\n") as file:
            file.write(f"PG_ID: {pg_id}\n")
            file.write(f"Name: {name}\n")
            file.write(f"City: {city}\n")
            file.write(f"Rooms: {rooms}\n")
            file.write(f"Rent: {rent}\n")
            file.write(f"Image: {image_path}\n\n")

        return redirect("/view")

    return render_template("register_pg.html")


@app.route("/book", methods=["GET", "POST"])
def book_pg():
    pg_options = []
    file_path = os.path.join(DATA_FOLDER, "pg_list.txt")

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            data = file.read().strip().split("\n\n")
            for block in data:
                pg_id = pg_name = ""
                for line in block.strip().split("\n"):
                    if line.startswith("PG_ID"):
                        pg_id = line.split(": ")[1].strip()
                    if line.startswith("Name"):
                        pg_name = line.split(": ")[1].strip()
                if pg_id and pg_name:
                    pg_options.append((pg_id, pg_name))

    if request.method == "POST":
        name = request.form["name"]
        contact = request.form["contact"]
        selected_pg = request.form["pg_id"]

        with open(
            os.path.join(DATA_FOLDER, "bookings.txt"),
            "a",
            encoding="utf-8",
            newline="\n",
        ) as file:
            file.write(f"User: {name}\n")
            file.write(f"Contact: {contact}\n")
            file.write(f"Booked PG: {selected_pg}\n\n")

        return f"<h3>Booking Successful for {name}!</h3><a href='/'>Go Home</a>"

    return render_template("book_pg.html", pg_options=pg_options)


@app.route("/history")
def booking_history():
    bookings = []
    bookings_path = os.path.join(DATA_FOLDER, "bookings.txt")
    if os.path.exists(bookings_path):
        with open(bookings_path, "r", encoding="utf-8") as file:
            data = file.read().strip().split("\n\n")
            for block in data:
                booking = {}
                for line in block.strip().split("\n"):
                    if ": " in line:
                        key, val = line.split(": ", 1)
                        booking[key.strip()] = val.strip()
                bookings.append(booking)
    return render_template("booking_history.html", bookings=bookings)


@app.route("/admin")
def admin_panel():
    if not session.get("logged_in"):
        return redirect("/login")
    return render_template("admin.html")


@app.route("/export")
def export_csv():
    csv_path = os.path.join(DATA_FOLDER, "pg_data.csv")
    input_path = os.path.join(DATA_FOLDER, "pg_list.txt")

    data = []
    if os.path.exists(input_path):
        with open(input_path, "r", encoding="utf-8") as f:
            blocks = f.read().strip().split("\n\n")
            for block in blocks:
                pg = {}
                for line in block.split("\n"):
                    if ": " in line:
                        key, value = line.split(": ", 1)
                        pg[key.strip()] = value.strip()
                data.append(pg)

    if data:
        keys = data[0].keys()
        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)

    return send_file(csv_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
