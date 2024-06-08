from os.path import dirname, abspath, join

from flask import Flask, request, render_template, redirect
from waitress import serve

from html_builder import build_overlap_html
from letterboxd_scraper import get_watchlist_overlap


TEMPLATES_AUTO_RELOAD = True
USER_AMOUNT = 2
PORT = 8080


app = Flask(
    __name__, template_folder=dirname(dirname(abspath(__file__))) + "/templates"
)


# if empty path, rerender to form
@app.route("/", methods=["GET", "POST"])
def refresh():
    render_template
    with open("templates/form.html", "r") as form:
        formString = form.read()
    return formString


# takes user input for usernames and finds displays watchlist overlap
@app.route("/showoverlap", methods=["POST"])
def enter():
    usernames = []
    if request.method == "POST":
        # determine which button is pressed
        if request.form["poster_type"] == "yes_poster":
            showPosters = True
        else:
            showPosters = False

        # get all usernames
        for i in range(USER_AMOUNT):
            usernames.append(request.form.get("usr" + str(i + 1)))

        # gets overlap of movies as array of html chunks
        intersection = get_watchlist_overlap(usernames)

        # builds html from overlap
        build_overlap_html(intersection, usernames, showPosters)

        print("DONE")

        return render_template("watchlist.html")  # display watchlist
    return redirect("/")


# adds text box for another user
@app.route("/add", methods=["POST"])
def addUser():
    if request.method == "POST":
        global USER_AMOUNT
        USER_AMOUNT += 1  # update amount of users

        # find where to insert new box
        before_insert_substring = (
            'placeholder = "Letterboxd User ' + str(USER_AMOUNT - 1) + '">'
        )
        with open("templates/form.html", "r") as form_html:
            form_html_string = form_html.read()

        index = form_html_string.find(before_insert_substring) + len(
            before_insert_substring
        )

        # copy html form and add in box
        newForm = (
            form_html_string[0:index]
            + '\n<input type="text" id="username'
            + str(USER_AMOUNT)
            + '" name="usr'
            + str(USER_AMOUNT)
            + '" placeholder = "Letterboxd User '
            + str(USER_AMOUNT)
            + '">'
            + form_html_string[index:]
        )

        # update html form
        with open("templates/form.html", "w") as form_html:
            form_html.write(newForm)

        # refresh to form
        return redirect("/")
    return redirect("/")


# removes text box for another user
@app.route("/remove", methods=["POST"])
def removeUser():
    global USER_AMOUNT
    if request.method == "POST" and USER_AMOUNT > 2:
        # box to be deleted
        delection_substring = (
            '\n<input type="text" id="username'
            + str(USER_AMOUNT)
            + '" name="usr'
            + str(USER_AMOUNT)
            + '" placeholder = "Letterboxd User '
            + str(USER_AMOUNT)
            + '">'
        )

        # open html
        with open("templates/form.html", "r") as form_html:
            form_html_string = form_html.read()

        # copy html and remove at specified index
        index = form_html_string.find(delection_substring)
        newForm = (
            form_html_string[0:index]
            + form_html_string[index + len(delection_substring) :]
        )
        form_html.close()

        # update html form
        with open("templates/form.html", "w") as form_html:
            form_html.write(newForm)

        USER_AMOUNT -= 1  # update amount of users
        return redirect("/")  # redirect to refresh
    return redirect("/")


# resets form.html and watchlist.html to their respective outlines
def restartForm():
    form_outline_path = (
        dirname(dirname(abspath(__file__))) + "/templates/formOutline.html"
    )
    with open(form_outline_path, "r") as form_outline_html:
        form_outline = form_outline_html.read()

    form_path = dirname(dirname(abspath(__file__))) + "/templates/form.html"
    with open(form_path, "w") as form_html:
        form_html.write(form_outline)


if __name__ == "__main__":
    restartForm()
    print("\nRunning at localhost:" + str(PORT))
    serve(app, host="0.0.0.0", port=PORT)
