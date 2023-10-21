from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from bson.objectid import ObjectId
from flask_pymongo import pymongo
# from func_tools import wraps
# from app import app
# import pymongo

app = Flask(__name__)
app.secret_key = "aadeshkabra"
CONNECTION_STRING = "mongodb+srv://aadeshkabra:aadesh@ayurvedai-1.bqsgk4h.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(CONNECTION_STRING)
db = client.get_database("AyurvedAI")
users = pymongo.collection.Collection(db, 'users')
opportunities = pymongo.collection.Collection(db, 'opportunities')


def set_session(login_user):
    print("Set session: ", login_user)
    session["username"] = login_user["Name"]
    session["role"] = login_user["Role"]
    session["email"] = login_user["Email"]
    session["user_id"] = str(login_user["_id"])


def get_jobs(type):
    records = opportunities.find({"Type": type})
    jobs = [record for record in records]
    return jobs


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == "POST":
        session.clear()
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template("index.html")


@app.route("/user-login", methods=['POST', 'GET'])
def user_login():
    message = "Please enter credentials to Login"
    return render_template("login.html", message=message)


@app.route("/user-signup", methods=['POST'])
def user_signup():
    message = "Please fill in correct information to SignUp"
    return render_template("signup.html", message=message)


@app.route("/signup", methods=['POST', 'GET'])
def signup():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")
    # print(name, email, password)
    user_id = ObjectId()
    dic = {
        "_id": user_id,
        "Name": name,
        "Email": email,
        "Password": password,
        "Role": role
    }
    users.insert_one(dic)
    print("User inserted successfully")
    return render_template("login.html", message="User sign-up successful!")


@app.route("/store-url", methods=['POST'])
def store_url():
    data = request.get_json()
    url = data.get("url")
    session["redirect_url"] = url
    return jsonify(message="URL stored successfully")


@app.route("/login", methods=['POST', 'GET'])
def login():

    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        login_user = users.find_one({"Email": email})
        print("Login user: ", login_user)
        orig_password = login_user["Password"]
        if password == orig_password:
            set_session(login_user)
            redirect_url = session.get("redirect_url", "/")
            print(redirect_url)
            if redirect_url:
                return redirect(redirect_url)
            else:
                return redirect(url_for("index"))
        else:
            return render_template("login.html", message="Wrong credentials. Please enter correct email and password")

    return render_template("login.html")


@app.route("/start", methods=['POST'])
def start():
    button = request.form.get("submitButton")
    if button == "searchJobs":
        return render_template("privateE.html")
    elif button == "searchEmployees":
        return render_template("employees.html")
    else:
        return render_template("opportunity.html", message="Please enter correct information only")


@app.route("/privateE", methods=['POST', 'GET'])
def private():
    jobs = get_jobs("private")
    return render_template("privateE.html", jobs=jobs)

@app.route("/jobs", methods=['POST'])
def jobs():
    button = request.form.get("submitButton2")
    # print(button)
    if button == "private":
        jobs = get_jobs("private")
        return render_template("privateE.html", jobs=jobs)
    elif button == "public":
        return render_template("publicE.html")
    elif button == "self":
        return render_template("selfE.html")
    elif button == "pwds":
        return render_template("pwdE.html")
    elif button == "women":
        return render_template("womenE.html")
    else:
        return render_template("localE.html")


@app.route("/opportunity-form", methods=['POST'])
def opportunity_form():
    name = request.form.get("employer-name")
    email = request.form.get("employer-email")
    title = request.form.get("job-title")
    type = request.form.get("type")
    description = request.form.get("job-description")
    labels = request.form.get("labelValues")
    labels = labels.split(",")
    # print(name, email, title, type, description, labels)
    user = users.find_one({"Name": name})
    if user is not None:
        if user["Email"] == email:
            dic = {
                "Name": name,
                "Email": email,
                "Job_Title": title,
                "Type": type,
                "Job_Description": description,
                "Labels": labels
            }
            print(dic)
            opportunities.insert_one(dic)
            return render_template("index.html")
        else:
            return render_template("opportunity.html", message="You have not entered correct email. Please enter correct email!")
    else:
        return render_template("opportunity.html", message="You have not registered. Kindly register and then Post!")
    return render_template("index.html")


@app.route("/job/<string:job_id>")
def job_detail(job_id):
    job = opportunities.find_one({"_id": ObjectId(job_id)})
    print(job)
    return render_template("cardData.html", job=job)


@app.route('/check-login-status', methods=['GET'])
def check_login_status():
    if session.get("username"):
        return jsonify(loggedIn=True)
    else:
        return jsonify(loggedIn=False)


@app.route("/apply-job", methods=['POST', 'GET'])
def apply_job():
    try:
        data = request.json
        print(data)
        if "username" not in session:
            session["redirect_url"] = request.url
            return redirect(url_for('login'))

        job_details = opportunities.find_one({"_id": ObjectId(data['jobId'])})
        print("Job details: ", job_details)
        if job_details.get("users") is None:
            print(session["user_id"])
            opportunities.update_one(job_details, {'$set': {'users': [session["user_id"]]}})
        else:
            user = str(session["user_id"])
            job_id = str(job_details["_id"])
            print("User id:", user)
            print("Job id:", str(job_details["_id"]))
            print("Job details before update: ", job_details)
            opportunities.update_one({"_id": ObjectId(job_id)}, {'$push': {'users': user}})
            print("Job details after update: ", opportunities.find_one({"_id": ObjectId(job_id)}))
        return jsonify(message="Job application successful"), 200
    except Exception as e:
        print(str(e))
        return jsonify(error="Internal Server error"), 500


if __name__ == "__main__":
    app.run()

