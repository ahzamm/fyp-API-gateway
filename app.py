from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        return f"Signed up successfully! Name: {name}, Email: {email}"


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        return render_template("signin.html")
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        return f"Signed in successfully! Email: {email}"


if __name__ == "__main__":
    app.run(debug=True)
