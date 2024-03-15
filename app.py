import base64
from io import BytesIO

import requests
from flask import Flask, make_response, redirect, render_template, request
from PIL import Image
from werkzeug.utils import secure_filename

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


# @app.route("/home", methods=["GET", "POST"])
# def home():
#     if request.method == "GET":
#         token = request.cookies.get("token")
#         if token:
#             url = "http://localhost:8000/api/user/profile"
#             headers = {
#                 "Content-Type": "application/json",
#                 "Accept": "application/json",
#                 "Authorization": "Bearer " + token,
#             }
#             response = requests.get(url, headers=headers)
#             response_data = response.json()
#             if response_data.get("success") == True:
#                 return render_template("home.html")
#         return redirect("signin")


@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        url = " http://localhost:5001/retrieve-all-photos/?user_id=1"
        response = requests.get(url)
        images_base64 = response.json()
        images_data_urls = []
        for image_base64 in images_base64:
            image_data_url = "data:image/jpeg;base64," + image_base64
            images_data_urls.append(image_data_url)
        return render_template("home.html", images=images_data_urls)

    if request.method == "POST":
        file = request.files["image"]
        if file:
            filename = secure_filename(file.filename)
            url = "http://127.0.0.1:5001/photos"
            data = {
                "vector_id": 123,
                "filename": filename,
                "user_id": 1,
            }
            files = {"image": (filename, file)}
            response = requests.post(url, data=data, files=files)
        return redirect("/home")


if __name__ == "__main__":
    app.run(port=5000, debug=True)
