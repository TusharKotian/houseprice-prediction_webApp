from flask import Flask, render_template, request, flash, redirect, url_for, session
import pickle
import numpy as np
from supabase_config import supabase
from hashlib import sha256
import os


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "1234")


def hash_password(password):
    return sha256(password.encode()).hexdigest()


# loading the model
with open("house_price_new.pkl", "rb") as f:
    model = pickle.load(f)


# Prediction function
def predict_house_price(
    bedrooms: int = 3,
    bathrooms: float = 2.0,
    sqft_living: int = 1500,
    sqft_lot: int = 6000,
    floors: float = 1.0,
    waterfront: int = 0,
    view: int = 0,
    condition: int = 3,
    sqft_above: int = 1500,
    sqft_basement: int = 0,
    yr_built: int = 1990,
    yr_renovated: int = 0,
):

    temp_array = [
        bedrooms,
        bathrooms,
        sqft_living,
        sqft_lot,
        floors,
        waterfront,
        view,
        condition,
        sqft_above,
        sqft_basement,
        yr_built,
        yr_renovated,
    ]

    temp_array = np.array([temp_array])

    prediction = model.predict(temp_array)

    return int(prediction[0])


@app.route("/")
def home():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("home.html")


@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/login",methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("u_email")
        password = request.form.get("u_password")

        response = supabase.table("users").select("*").eq("u_email", email).execute()
        user = response.data[0] if response.data else None

        if user and user["u_password"] == hash_password(password):
            session["user_id"] = user["user_id"]
            return redirect(url_for("home"))

        flash("Invalid email or password")

    return render_template("login.html")


@app.route("/signup",methods=["GET", "POST"])
def signup():
    if session.get("user_id"):
        return redirect(url_for("home"))

    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("u_email")
        password = request.form.get("u_password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match")
            return render_template("signup.html")

        full_name = f"{first_name} {last_name}".strip()
        existing = supabase.table("users").select("*").eq("u_email", email).execute()

        if existing.data:
            flash("Email already exists")
            return render_template("signup.html")

        supabase.table("users").insert({
            "u_name": full_name,
            "u_email": email,
            "u_password": hash_password(password)
        }).execute()

        flash("Signup successful, please login")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/predict", methods=["GET", "POST"])
def predict():
    if not session.get("user_id"):
        flash("Please log in to access predictions.")
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            bedrooms = int(request.form["bedrooms"])
            bathrooms = float(request.form["bathrooms"])
            sqft_living = int(
                request.form.get("sqft_living", request.form.get("living-area", 0))
            )
            sqft_lot = int(
                request.form.get("sqft_lot", request.form.get("lot-area", 0))
            )
            floors = float(request.form["floors"])
            waterfront = int(request.form["waterfront"])
            view = int(request.form["view"])
            condition = int(request.form["condition"])
            sqft_above = int(request.form["sqft_above"])
            sqft_basement = int(request.form["sqft_basement"])
            yr_built = int(request.form["yr_built"])
            yr_renovated = int(request.form.get("yr_renovated") or 0)

            price = predict_house_price(
                bedrooms,
                bathrooms,
                sqft_living,
                sqft_lot,
                floors,
                waterfront,
                view,
                condition,
                sqft_above,
                sqft_basement,
                yr_built,
                yr_renovated,
            )

            return render_template("predict.html", price=price)

        except ValueError:
            flash("Please enter valid input values.")
            return redirect(url_for("predict"))

    return render_template("predict.html")


if __name__ == "__main__":
    app.run(debug=True, port=4008)
