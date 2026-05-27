from flask import Flask, request, render_template_string
import requests
import urllib3
import time

time.sleep(5)

app= Flask(__name__)

url = "https://localhost:5000/"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.headers.update({ "Accept-Encoding": "gzip" })
session.post(url + "signin", data={"username": "oracle", "password": "adf1c2b414d13921ba7d1e3511156a90"}, verify=False)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uri = request.form.get("research")
        response = session.get(url + uri, verify=False)
        return str(response.headers.get("Content-Length"))
    else:
        return render_template_string("""
            <h1> Oracle </h1>
            <form method="POST">
                Make a research :  <input type="text" name = "research">
                <input type="submit" value="Search">
            </form>
            """
            )


if __name__ == "__main__":
	app.run( host="0.0.0.0", port=5001)