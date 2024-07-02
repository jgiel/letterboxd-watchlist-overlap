from os.path import dirname, abspath

from flask import Flask, request, render_template, redirect, session

from letterboxd_scraper import get_watchlist_overlap


PORT = 8080

app = Flask(
    __name__, template_folder=dirname(dirname(abspath(__file__))) + "/templates"
)
app.secret_key = "dev"


# if empty path, rerender to form
@app.route("/", methods=["GET"])
def form():
    return render_template("form.html", user_amount=session.get("user_amount", 2))


# takes user input for usernames and finds displays watchlist overlap
@app.route("/showoverlap", methods=["POST", "GET"])
def enter():
    if request.method == "POST":
        if request.form["show_poster"] == "True":
            showPosters = True
        else:
            showPosters = False

        session["usernames"] = []
        for i in range(session.get("user_amount", 2)):
            session["usernames"].append(request.form.get("usr" + str(i + 1)))

    if request.method == "GET":
        session["usernames"] = request.args.getlist("user")
        if request.args.get("show_posters") == "True":
            showPosters = True
        else:
            showPosters = False

    print("Getting movies from Letterboxd watchlists...")
    movies = get_watchlist_overlap(session["usernames"], showPosters)
    print("DONE")

    return render_template(
        "watchlist.html",
        movies=movies,
        usernames=session["usernames"],
        total=str(len(movies)),
    )


@app.route("/add", methods=["POST"])
def addUser():
    session["user_amount"] = session.get("user_amount", 2) + 1
    return redirect("/")


@app.route("/remove", methods=["POST"])
def removeUser():
    if session.get("user_amount", 2) > 2:
        session["user_amount"] = session.get("user_amount", 2) - 1

    return redirect("/")


if __name__ == "__main__":
    app.run()
