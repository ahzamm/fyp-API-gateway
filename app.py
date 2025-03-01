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
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

app = Flask(__name__)


google_client_id = os.getenv("CLIENT_ID")
app.secret_key   = os.getenv("CLIENT_SECRET")
project_id       = os.getenv("PROJECT_ID")


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def get_avatar_link(name):
    first_letter = name[0].upper()
    hash_value   = hashlib.md5(first_letter.encode("utf-8")).hexdigest()
    return f"https://www.gravatar.com/avatar/{hash_value}?d=identicon"


@app.route("/login-with-google", methods=["GET"])
def login_with_google():
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id"                  : google_client_id,
                "project_id"                 : project_id,
                "auth_uri"                   : "https://accounts.google.com/o/oauth2/auth",
                "token_uri"                  : "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret"              : app.secret_key,
                "redirect_uris"              : ["http://localhost:5000/callback"],
                "javascript_origins"         : ["http://localhost:5000"],
            }
        },
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/photoslibrary",
            "https://www.googleapis.com/auth/photoslibrary.readonly",
        ],
        redirect_uri = "http://localhost:5000/callback",
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true"
    )
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback", methods=["GET"])
def callback():
    state = request.args.get("state")

    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id"                  : google_client_id,
                "project_id"                 : project_id,
                "auth_uri"                   : "https://accounts.google.com/o/oauth2/auth",
                "token_uri"                  : "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret"              : app.secret_key,
                "redirect_uris"              : ["http://localhost:5000/callback"],
                "javascript_origins"         : ["http://localhost:5000"],
            }
        },
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/photoslibrary",
            "https://www.googleapis.com/auth/photoslibrary.readonly",
        ],
        state=state,
        redirect_uri="http://localhost:5000/callback",
    )

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session["credentials"] = credentials_to_dict(credentials)

    id_info = id_token.verify_oauth2_token(
        id_token = credentials.id_token,
        request  = google.auth.transport.requests.Request(),
        audience = google_client_id,
    )
    email = id_info.get("email")
    name = id_info.get("name")
    picture = id_info.get("picture")

    url           = f"http://localhost:8001/api/user/check-email/?email={email}"
    response      = requests.get(url)
    response_data = response.json()
    if response_data.get("success") == False:
        # Create user
        random_string = generate_random_string(10)
        data = {
            "name"                 : name,
            "email"                : email,
            "password"             : random_string,
            "password_confirmation": random_string,
            "avatar"               : picture,
        }

        url           = "http://localhost:8001/api/user/register"
        headers       = {"Content-Type": "application/json", "Accept": "application/json"}
        response      = requests.post(url, json=data, headers=headers)
        response_data = response.json()

        if response_data.get("success") == True:
            resp = make_response(redirect("/"))
            resp.set_cookie(
                "token", response_data.get("token", ""), max_age=timedelta(days=1)
            )
            return resp
        else:
            message = response_data.get("message")
            return render_template("signup.html", message=message)

    elif response_data.get("success") == True:
        data = {
            "name"  : name,
            "email" : email,
            "avatar": picture,
        }

        url           = "http://localhost:8001/api/user/edit-user"
        headers       = {"Content-Type": "application/json", "Accept": "application/json"}
        response      = requests.post(url, json=data, headers=headers)
        response_data = response.json()
        if response_data.get("success") == True:
            resp = make_response(redirect("/"))
            resp.set_cookie(
                "token", response_data.get("token", ""), max_age=timedelta(days=1)
            )
            return resp
        else:
            message = response_data.get("message")
            return render_template("signup.html", message=message)


@app.route("/signup", methods=["GET"])
def show_signup_form():
    token = request.cookies.get("token")
    if token:
        url     = "http://localhost:8001/api/user/profile"
        headers = {
            "Content-Type" : "application/json",
            "Accept"       : "application/json",
            "Authorization": "Bearer " + token,
        }
        response      = requests.get(url, headers=headers)
        response_data = response.json()
        if response_data.get("success") == True:
            return redirect("/")
    return render_template("signup.html")


@app.route("/signup", methods=["POST"])
def signup():
        name             = request.form["name"]
        email            = request.form["email"]
        password         = request.form["password"]
        confirm_password = request.form["confirm_password"]

        data = {
            "name"                 : name,
            "email"                : email,
            "password"             : password,
            "password_confirmation": confirm_password,
            "avatar"               : get_avatar_link(name),
        }

        url           = "http://localhost:8001/api/user/register"
        headers       = {"Content-Type": "application/json", "Accept": "application/json"}
        response      = requests.post(url, json=data, headers=headers)
        response_data = response.json()

        if response_data.get("success") == True:
            resp = make_response(redirect("/"))
            resp.set_cookie(
                "token", response_data.get("token", ""), max_age=timedelta(days=1)
            )
            return resp
        else:
            message = response_data.get("message")
            return render_template("signup.html", message=message)



@app.route("/signin", methods=["GET"])
def show_signin_form():
    session.pop('message', None)
    
    token = request.cookies.get("token")
    if token:
        url     = "http://localhost:8001/api/user/profile"
        headers = {
            "Content-Type" : "application/json",
            "Accept"       : "application/json",
            "Authorization": "Bearer " + token,
        }
        response      = requests.get(url, headers=headers)
        response_data = response.json()
        if response_data.get("success") == True:
            return redirect("/")
    
    return render_template("signin.html")



@app.route("/signin", methods=["POST"])
def signin():
    email    = request.form["email"]
    password = request.form["password"]

    data = {
        "email"   : email,
        "password": password,
    }

    url           = "http://localhost:8001/api/user/login"
    headers       = {"Content-Type": "application/json", "Accept": "application/json"}
    response      = requests.post(url, json=data, headers=headers)
    response_data = response.json()

    if response_data.get("success") == True:
        resp = make_response(redirect("/"))
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


def refresh_google_token(refresh_token):
    url  = "https://oauth2.googleapis.com/token"
    data = {
        "client_id"    : google_client_id,
        "client_secret": app.secret_key,
        "refresh_token": refresh_token,
        "grant_type"   : "refresh_token",
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        new_credentials = response.json()
        return new_credentials
    else:
        return None


def sync_local_photos(user_id, google_photos_ids):
    # Fetch locally stored photos
    url          = f"http://localhost:5001/retrieve-all-photos/?user_id={user_id}"
    response     = requests.get(url)
    local_photos = response.json()
    print('🚀🚀🚀', local_photos)

    # Extract local photo ids
    local_photo_ids = [photo["vector_id"] for photo in local_photos["photos"]]

    # Find photos that are no longer in Google Photos
    photos_to_delete = set(local_photo_ids) - set(google_photos_ids)

    # Delete these photos from local storage
    for photo_id in photos_to_delete:
        if photo_id.startswith("ANU"):
        
            delete_url = f"http://127.0.0.1:5001/photos?image_id={photo_id}"
            requests.delete(delete_url)

            delete_url = f"http://127.0.0.1:5002/delete-photo/?vector_id={photo_id}"
            requests.delete(delete_url)


@app.route("/", methods=["GET", "POST"])
def home():
    token = request.cookies.get("token")
    if token is None:
        return redirect("/signin")

    url     = "http://localhost:8001/api/user/profile"
    headers = {
        "Content-Type" : "application/json",
        "Accept"       : "application/json",
        "Authorization": "Bearer " + token,
    }
    response      = requests.get(url, headers=headers)
    response_data = response.json()
    if response_data.get("success") == True:
        user_id     = response_data.get("user").get("id")
        user_name   = response_data.get("user").get("name")
        user_email  = response_data.get("user").get("email")
        user_avatar = response_data.get("user").get("avatar")
        user_data   = {"name": user_name, "email": user_email, "avatar": user_avatar}
    else:
        return redirect("/signin")

    if request.method == "GET":
        query = request.args.get("search")
        if query:
            images_data_urls = []
            url              = "http://127.0.0.1:5001/query"
            headers          = {
                "Content-Type": "application/json",
                "Accept"      : "application/json",
            }
            data      = {"query": query, "user_id": user_id}
            response  = requests.post(url, data=json.dumps(data), headers=headers)
            image_ids = response.json().get("image_ids")

            if image_ids:
                url           = f"http://127.0.0.1:5002/retrieve-photos/?vector_ids={image_ids}"
                response      = requests.get(url)
                images_base64 = response.json()
                for image_dict in images_base64:
                    image_data_url = "data:image/jpeg;base64," + image_dict["image"]
                    images_data_urls.append(
                        {"image": image_data_url, "vector_id": image_dict["vector_id"]}
                    )

            response = make_response(
                render_template(
                    "home.html", images=images_data_urls, user_data=user_data
                )
            )

            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"]        = "no-cache"
            response.headers["Expires"]       = "0"

            return response

        # Retrieve other images
        url              = f"http://localhost:5002/retrieve-all-photos/?user_id={user_id}"
        response         = requests.get(url)
        images_base64    = response.json()
        images_data_urls = []
        for image_dict in images_base64:
            image_data_url = "data:image/jpeg;base64," + image_dict["image"]
            images_data_urls.append(
                {"image": image_data_url, "vector_id": image_dict["vector_id"]}
            )

        # Retrieve Google Photos with pagination
        credentials = Credentials(**session["credentials"])
        if not credentials.valid:
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                session["credentials"] = credentials_to_dict(credentials)
            else:
                return redirect("/login-with-google")

        access_token      = credentials.token
        google_photos_ids = []
        if access_token:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept"       : "application/json",
            }
            url             = "https://photoslibrary.googleapis.com/v1/mediaItems"
            next_page_token = None
            while True:
                if next_page_token:
                    response = requests.get(
                        url, headers=headers, params={"pageToken": next_page_token}
                    )
                else:
                    response = requests.get(url, headers=headers)

                if response.status_code != 200:
                    break

                google_photos_data = response.json()
                for item in google_photos_data.get("mediaItems", []):
                    image_url = item.get("baseUrl") + "=w500-h500"
                    vector_id = item.get("id")
                    google_photos_ids.append(vector_id)

                    # Check if vector_id exists in both microservices
                    vector_exists = False
                    for port in [5001, 5002]:
                        check_url      = f"http://127.0.0.1:{port}/check-vector"
                        data           = {"vector_id": vector_id}
                        check_response = requests.get(check_url, data)
                        if check_response.json().get(
                            "success"
                        ) and check_response.json().get("exists"):
                            vector_exists = True

                    # If vector_id does not exist in both microservices, create an entry
                    if not vector_exists:
                        for port in [5001, 5002]:
                            create_url = f"http://127.0.0.1:{port}/photos"
                            data       = {
                                "vector_id": vector_id,
                                "filename" : item.get("filename", "unknown.jpg"),
                                "user_id"  : user_id,
                            }
                            image_data = requests.post(image_url).content
                            files      = {
                                "image": (data["filename"], image_data, "image/jpeg")
                            }
                            requests.post(create_url, data=data, files=files)

                next_page_token = google_photos_data.get("nextPageToken")
                if not next_page_token:
                    break

        # Sync local photos with Google Photos
        sync_local_photos(user_id, google_photos_ids)

        response = make_response(
            render_template(
                "home.html", images=reversed(images_data_urls), user_data=user_data
            )
        )
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"]        = "no-cache"
        response.headers["Expires"]       = "0"

        return response

    if request.method == "POST":
        if "image" in request.files:
            file = request.files["image"]
            if file:
                filename = secure_filename(file.filename)
                files    = {"image": (filename, file)}
                url      = "http://127.0.0.1:5001/photos"
                data     = {
                    "user_id": user_id,
                }
                response  = requests.post(url, data=data, files=files)
                vector_id = response.json().get("vector_id")

                file.seek(0)
                files = {"image": (filename, file)}
                url   = "http://127.0.0.1:5002/photos"
                data  = {
                    "vector_id": vector_id,
                    "filename" : filename,
                    "user_id"  : user_id,
                }
                response = requests.post(url, data=data, files=files)
                return redirect("/")


def credentials_to_dict(credentials):
    return {
        "token"        : credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri"    : credentials.token_uri,
        "client_id"    : credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes"       : credentials.scopes,
    }


@app.route("/delete-image", methods=["POST"])
def delete_image():
    vector_id = request.json["vector_id"]

    url = f"http://127.0.0.1:5001/photos?image_id={vector_id}"
    requests.delete(url)

    url = f"http://127.0.0.1:5002/delete-photo/?vector_id={vector_id}"
    requests.delete(url)

    return redirect("/")


@app.route("/photos", methods=["GET"])
def get_photos():
    access_token = session.get("access_token")
    if not access_token:
        return redirect("/signin")

    headers  = {"Authorization": f"Bearer " + access_token, "Accept": "application/json"}
    url      = "https://photoslibrary.googleapis.com/v1/mediaItems"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        photos_data = response.json()
        return render_template("photos.html", photos=photos_data.get("mediaItems", []))
    else:
        return f"An error occurred: {response.status_code} {response.text}"


@app.route("/delete-account", methods=["POST"])
def delete_account():
    token = request.cookies.get("token")
    if token is None:
        return redirect("/signin")
    
    # Get the user profile to fetch the user ID
    url     = "http://localhost:8001/api/user/profile"
    headers = {
        "Content-Type" : "application/json",
        "Accept"       : "application/json",
        "Authorization": "Bearer " + token,
    }
    response = requests.get(url, headers=headers)
    response_data = response.json()

    if response_data.get("success") == True:
        user_id = response_data.get("user").get("id")
        
        # Delete the user's vectors from the vector embedding service
        delete_vectors_url = f"http://localhost:5001/delete-user-data?user_id={user_id}"
        vector_delete_response = requests.delete(delete_vectors_url)
        print(f"Vector delete response: {vector_delete_response.json()}")

        # Delete the user's images from the image storage service
        delete_images_url = f"http://localhost:5002/delete-user-data?user_id={user_id}"
        image_delete_response = requests.delete(delete_images_url)
        print(f"Image delete response: {image_delete_response.json()}")

        # Now proceed to delete the user account
        url     = "http://localhost:8001/api/user/delete-account"
        response = requests.delete(url, headers=headers)
        response_data = response.json()

        if response_data.get("success") == True:
             return redirect("/signin")
    
    return render_template("error.html", message="Failed to delete the account")


if __name__ == "__main__":
    app.run(port=5000, debug=True)
