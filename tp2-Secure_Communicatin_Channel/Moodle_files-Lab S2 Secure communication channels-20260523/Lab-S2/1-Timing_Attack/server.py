from flask import Flask, request, make_response
import time

app = Flask(__name__)

PINCODE = "33102144"


def verify_pincode(pincode):
    if len(pincode) != len(PINCODE):
        return False
    time.sleep(0.01)
    for check, ref in zip(pincode, PINCODE):
        if check != ref:
            return False
        else:
            time.sleep(0.01)
    return True


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            request_pincode = request.form["pincode"]
        except Exception:
            request_pincode = None
        if request_pincode is None:
            response = make_response(
                """Empty pincode !<br>\n<form method="post">\n<input type="pincode" name="pincode" id="pincode">\n<input type="submit">\n</form>"""
            )
        elif verify_pincode(request_pincode):
            response = make_response("You found the correct pincode !")
        else:
            response = make_response(
                """Incorrect pincode !<br>\n<form method="post">\n<input type="pincode" name="pincode" id="pincode">\n<input type="submit">\n</form>"""
            )
    else:
        response = make_response(
            """Enter a pincode<br>\n<form method="post">\n<input type="pincode" name="pincode" id="pincode">\n<input type="submit">\n</form>"""
        )

    return response


if __name__ == "__main__":
    app.run()

