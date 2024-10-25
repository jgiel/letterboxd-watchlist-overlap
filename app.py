# TODO: throw error / display when entered user does not exist, no/1 user entered
# TODO: implement tests

from os.path import abspath, dirname

from flask import Flask, redirect, render_template, request, session

from letterboxd_api import get_watchlist_overlap
from constants import logger 

PORT = 5000

app = Flask(__name__, template_folder=dirname(abspath(__file__)) + "/templates")
app.secret_key = "dev"


@app.route("/", methods=["GET"])
def form():
    return render_template("form.html", user_amount=session.get("user_amount", 2))


@app.route("/showoverlap", methods=["GET"])
async def enter():
    if request.args["show_posters"] == "True":
        show_posters = True
    else:
        show_posters = False

    usernames = request.args.getlist("username")

    logger.info(f"Finding overlap between {usernames}")
    movies = await get_watchlist_overlap(usernames, show_posters)
    logger.info(f"DONE")

    return render_template(
        "watchlist.html",
        movies=movies,
        usernames=usernames,
        total=str(len(movies)),
    )


@app.route("/add", methods=["GET"])
def addUser():
    session["user_amount"] = session.get("user_amount", 2) + 1
    return redirect("/")


@app.route("/remove", methods=["GET"])
def removeUser():
    if session.get("user_amount", 2) > 2:
        session["user_amount"] = session.get("user_amount", 2) - 1

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=PORT)
