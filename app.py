import requests
from flask import Flask, make_response, redirect, render_template, request

app = Flask(__name__)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        token = request.cookies.get("token")
        if token:
            url = "http://localhost:8000/api/user/profile"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": "Bearer " + token,
            }
            response = requests.get(url, headers=headers)
            response_data = response.json()
            if response_data.get("success") == True:
                return redirect("/home")
        return render_template("signup.html")
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        data = {
            "name": name,
            "email": email,
            "password": password,
            "password_confirmation": confirm_password,
        }

        url = "http://localhost:8000/api/user/register"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()

        if response_data.get("success") == True:
            resp = make_response(redirect("/home"))
            resp.set_cookie("token", response_data.get("token", ""))
            return resp
        else:
            message = response_data.get("message")
            return render_template("signup.html", message=message)


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        token = request.cookies.get("token")
        if token:
            url = "http://localhost:8000/api/user/profile"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": "Bearer " + token,
            }
            response = requests.get(url, headers=headers)
            response_data = response.json()
            if response_data.get("success") == True:
                return redirect("/home")
        return render_template("signin.html")
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        data = {
            "email": email,
            "password": password,
        }

        url = "http://localhost:8000/api/user/login"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()

        if response_data.get("success") == True:
            resp = make_response(redirect("/home"))
            resp.set_cookie("token", response_data.get("token", ""))
            return resp
        else:
            message = response_data.get("message")
            return render_template("signin.html", message=message)


@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        token = request.cookies.get("token")
        if token:
            url = "http://localhost:8000/api/user/profile"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": "Bearer " + token,
            }
            response = requests.get(url, headers=headers)
            response_data = response.json()
            if response_data.get("success") == True:
                return render_template("home.html")
        return redirect("signin")


if __name__ == "__main__":
    app.run(debug=True)
