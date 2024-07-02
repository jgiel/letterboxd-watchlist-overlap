from os.path import dirname, abspath

from flask import Flask, redirect, render_template, request, session

from letterboxd_scraper import get_watchlist_overlap


PORT = 8080

app = Flask(__name__, template_folder=dirname(abspath(__file__)) + "/templates")
app.secret_key = "dev"


@app.route("/", methods=["GET"])
def form():
    return render_template("form.html", user_amount=session.get("user_amount", 2))


@app.route("/showoverlap", methods=["GET"])
def enter():
    if request.args["show_posters"] == "True":
        showPosters = True
    else:
        showPosters = False

    usernames = request.args.getlist("username")

    print("Getting movies from Letterboxd watchlists...")
    movies = get_watchlist_overlap(usernames, showPosters)
    print("DONE")

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
    app.run(debug=True)
