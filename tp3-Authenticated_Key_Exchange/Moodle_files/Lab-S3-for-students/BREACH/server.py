from flask import Flask, request, render_template_string, redirect, session, url_for
from flask_compress import Compress
import uuid
import secrets

app= Flask(__name__)
app.config['SECRET_KEY'] = "ab4e268215aa729d772c25ce264625ef"
Compress(app)


users = {"oracle":{"csrf_token": "d89b6bcfd6be", "password": "adf1c2b414d13921ba7d1e3511156a90"}}


@app.before_request
def ensure_session():
	if 'session_id' not in session:
		session['session_id'] = str(uuid.uuid4())


@app.route("/")
def index():
	username = session.get('username', 'Guest')
	return render_template_string("""
		<h1> Welcome {{ username|safe }}</h1>
		{% if username == 'Guest' %}
			<a href="/signin">Sign in</a> | <a href="signup">Sign up</a>
		{% else %}
			<a href="/secret?username={{ username|safe }}"> A secret for you </a>  |  <a href="/logout">Disconnect</a>
		{% endif %}
		""", username = username)


@app.route("/signin", methods=["GET", "POST"])
def singin():
	if request.method == "POST":
		username = request.form.get("username")
		password = request.form.get("password")
		if username not in users or users.get(username)["password"] != password:
			return "Username or password incorrect ", 401
		session["username"] = username
		return redirect(url_for("index"))
	
	return render_template_string("""
		<a href="/"> Home </a><br>
		<h2> Sign in </h2>
		<form method="POST">
			Username: <input type="text" name = "username">
			Password: <input type="password" name="password">
			<input type="submit" value="Sign in">
		</form><br>
		<a href="/signup">Sign up </a>
		""")

@app.route("/signup", methods=["GET", "POST"])
def signup():
	if request.method == "POST":
		username = request.form.get("username")
		password = request.form.get("password")
		if username in users:
			return "Username already used", 400
		users[username] = {}
		users[username]["password"] = password
		users[username]["csrf_token"] = str(secrets.token_hex(6))
		session['username'] = username
		return redirect(url_for("index"))
	
	return render_template_string("""
		<a href="/"> Home </a><br>
		<h2> Sign up </h2>
		<form method="POST">
			Username: <input type="text" name = "username">
			Password: <input type="password" name="password">
			<input type="submit" value="Sign up">
		</form><br>
		<a href="/signin">Sign in </a>
		""")

@app.route("/secret")
def secret():
	if "username" not in session:
		return "You must be connected", 401
	username = request.args.get("username")
	return render_template_string("""
		<a href="/"> Home </a><br>
		<h2> Hi {{ username|safe }} </h2>
		Here is your link to get the flag : <a href="/get_flag?csrf_token={{csrf_token}}"> secret </a>
		""", username=username, csrf_token=users[session["username"]]["csrf_token"])


@app.route("/get_flag")
def get_flag():
	csrf_token = request.args.get("csrf_token")
	return render_template_string("""
		{% if csrf_token == correct_csrf_token %}
			flag{BREACH_ATTACK_CAN_RETRIEVE_UNPROTECTED_CSRF_TOKEN}
		{% else %}
			Sorry you can't have the flag
		{% endif %}
		""", csrf_token=csrf_token, correct_csrf_token=users["oracle"]["csrf_token"])

@app.route("/logout")
def logout():
	session.clear()
	return redirect(url_for("index"))

if __name__ == "__main__":
	app.config["COMPRESS_MIN_SIZE"] = 20
	app.run(ssl_context=('cert.pem', 'key.pem'), host="0.0.0.0", port=5000)

