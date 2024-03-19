import json
import os
import random
import string
from datetime import timedelta

import google.auth.transport.requests
import requests
from flask import Flask, make_response, redirect, render_template, request, session
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
from werkzeug.utils import secure_filename
import hashlib

app = Flask(__name__)


google_client_id = os.getenv("CLIENT_ID")
app.secret_key = os.getenv("CLIENT_SECRET")
project_id = os.getenv("PROJECT_ID")


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def get_avatar_link(name):
    first_letter = name[0].upper()
    hash_value = hashlib.md5(first_letter.encode("utf-8")).hexdigest()
    return f"https://www.gravatar.com/avatar/{hash_value}?d=identicon"


@app.route("/login-with-google", methods=["GET"])
def login_with_google():
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": google_client_id,
                "project_id": project_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": app.secret_key,
                "redirect_uris": ["http://localhost:5000/callback"],
                "javascript_origins": ["http://localhost:5000"],
            }
        },
        scopes=[
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        redirect_uri="http://localhost:5000/callback",
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true"
    )
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback", methods=["GET"])
def callback():
    state = session["state"]

    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": google_client_id,
                "project_id": project_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": app.secret_key,
                "redirect_uris": ["http://localhost:5000/callback"],
                "javascript_origins": ["http://localhost:5000"],
            }
        },
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        state=state,
        redirect_uri="http://localhost:5000/callback",
    )

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials.id_token, request=token_request, audience=google_client_id
    )
    email = id_info.get("email")
    name = id_info.get("name")
    picture = id_info.get("picture")

    url = f"http://localhost:8001/api/user/check-email/?email={email}"
    response = requests.get(url)
    response_data = response.json()
    if response_data.get("success") == False:
        # Create user
        random_string = generate_random_string(10)
        data = {
            "name": name,
            "email": email,
            "password": random_string,
            "password_confirmation": random_string,
            "avatar": picture,
        }

        url = "http://localhost:8001/api/user/register"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()

        if response_data.get("success") == True:
            resp = make_response(redirect("/home"))
            resp.set_cookie(
                "token", response_data.get("token", ""), max_age=timedelta(days=1)
            )
            return resp
        else:
            message = response_data.get("message")
            return render_template("signup.html", message=message)

    elif response_data.get("success") == True:
        data = {
            "name": name,
            "email": email,
            "avatar": picture,
        }

        url = "http://localhost:8001/api/user/edit-user"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()
        if response_data.get("success") == True:
            resp = make_response(redirect("/home"))
            resp.set_cookie(
                "token", response_data.get("token", ""), max_age=timedelta(days=1)
            )
            return resp
        else:
            message = response_data.get("message")
            return render_template("signup.html", message=message)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        token = request.cookies.get("token")
        if token:
            url = "http://localhost:8001/api/user/profile"
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
            "avatar": get_avatar_link(name),
        }

        url = "http://localhost:8001/api/user/register"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()

        if response_data.get("success") == True:
            resp = make_response(redirect("/home"))
            resp.set_cookie(
                "token", response_data.get("token", ""), max_age=timedelta(days=1)
            )
            return resp
        else:
            message = response_data.get("message")
            return render_template("signup.html", message=message)


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        token = request.cookies.get("token")
        if token:
            url = "http://localhost:8001/api/user/profile"
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

        url = "http://localhost:8001/api/user/login"
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


@app.route("/logout", methods=["GET"])
def logout():
    resp = make_response(redirect("/signin"))
    resp.set_cookie("token", "", expires=0)
    return resp


@app.route("/home", methods=["GET", "POST"])
def home():
    token = request.cookies.get("token")
    if token is None:
        return redirect("/signin")

    url = "http://localhost:8001/api/user/profile"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Bearer " + token,
    }
    response = requests.get(url, headers=headers)
    response_data = response.json()
    if response_data.get("success") == True:
        user_id = response_data.get("user").get("id")
        user_name = response_data.get("user").get("name")
        user_email = response_data.get("user").get("email")
        user_avatar = response_data.get("user").get("avatar")
        user_data = {"name": user_name, "email": user_email, "avatar": user_avatar}
    else:
        return redirect("/signin")

    # retrieve user info here

    if request.method == "GET":
        url = f"http://localhost:5002/retrieve-all-photos/?user_id={user_id}"
        response = requests.get(url)
        images_base64 = response.json()
        images_data_urls = []
        for image_dict in images_base64:
            image_data_url = "data:image/jpeg;base64," + image_dict["image"]
            images_data_urls.append(
                {"image": image_data_url, "vector_id": image_dict["vector_id"]}
            )
        response = make_response(
            render_template(
                "home.html", images=reversed(images_data_urls), user_data=user_data
            )
        )
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response

    if request.method == "POST":
        if "image" in request.files:
            file = request.files["image"]
            if file:
                filename = secure_filename(file.filename)
                files = {"image": (filename, file)}
                url = "http://127.0.0.1:5001/photos"
                data = {
                    "user_id": user_id,
                }
                response = requests.post(url, data=data, files=files)
                vector_id = response.json().get("vector_id")

                file.seek(0)
                files = {"image": (filename, file)}
                url = "http://127.0.0.1:5002/photos"
                data = {
                    "vector_id": vector_id,
                    "filename": filename,
                    "user_id": user_id,
                }
                response = requests.post(url, data=data, files=files)
                return redirect("/home")

        query = request.form["search"]
        if query:
            url = "http://127.0.0.1:5001/query"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            data = {"query": query, "user_id": user_id}
            response = requests.post(url, data=json.dumps(data), headers=headers)
            image_ids = response.json().get("image_ids")

            url = f"http://127.0.0.1:5002/retrieve-photos/?vector_ids={image_ids}"
            response = requests.get(url)
            images_base64 = response.json()
            images_data_urls = []
            for image_dict in images_base64:
                image_data_url = "data:image/jpeg;base64," + image_dict["image"]
                images_data_urls.append(
                    {"image": image_data_url, "vector_id": image_dict["vector_id"]}
                )
            return render_template(
                "home.html", images=images_data_urls, user_data=user_data
            )


@app.route("/delete-image", methods=["POST"])
def delete_image():
    vector_id = request.json["vector_id"]

    url = f"http://127.0.0.1:5001/photos?image_id={vector_id}"
    requests.delete(url)

    url = f"http://127.0.0.1:5002/delete-photo/?vector_id={vector_id}"
    requests.delete(url)

    return redirect("/home")


if __name__ == "__main__":
    app.run(port=5000, debug=True)
