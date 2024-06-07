# to do:
# sort by runtime, year, etc.
# fix text errors for special characters (salo)
# handle incorrect lb username

from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from flask import Flask, request, render_template, redirect
from movieposters import imdbapi
from waitress import serve


TEMPLATES_AUTO_RELOAD = True
userAmount = 2
port = 8080

app = Flask(__name__)


def get_watchlist(username: str):
    """
    Obtains list of all suffix links to movies in user's watchlist.

    Parameters:
        username: Username of Letterboxd user

    Returns:
        watchlist: List of Letterboxd links to films in user's watchlist

    """

    current_page = 1

    watchlist = []

    while True:
        # create request to letterboxd url HTML
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"
        }
        url = (
            "https://www.letterboxd.com/"
            + username
            + "/watchlist/page/"
            + str(current_page)
            + "/"
        )
        req = Request(url=url, headers=headers)
        html = urlopen(req).read()

        # parse with bs4
        soup = BeautifulSoup(html, "html.parser")
        containers = soup.find_all("li", class_="poster-container")
        for container in containers:
            watchlist.append(
                "letterboxd.com" + container.find("div")["data-target-link"]
            )
            print(container.find("div")["data-target-link"])

        if not containers:
            return watchlist
        else:
            current_page += 1
            print("page " + str(current_page) + "\n")


def get_watchlist_overlap(usernames):
    """
    Gets overlap of watchlists of given users.

    Parameters:
        usernames: List of Letterboxed users.

    Returns:
        watchlist_overlap (list): List of dictionaries containing movies in all users watchlists.

    """
    # get list of watchlists
    watchlists = []
    for i in range(len(usernames)):
        watchlists.append(get_watchlist(usernames[i]))

    # find overlap
    watchlist_overlap = watchlists[0]
    for i in range(1, len(watchlists)):
        watchlist_overlap = list(
            set(watchlist_overlap) & set(watchlists[i])
        )  # set overlap to intersection between prev overlap and current watchlsit

    return watchlist_overlap


def build_overlap_html(list, usernames, showPosters):
    # open outline and watchlist htmls
    outlineFile = open("templates/watchlistOutline.html", "r")
    outputHTML = open("templates/watchlist.html", "w")
    outlineString = outlineFile.read()

    # create usernames as HTML hyperlinks for second header (comma/& separated)
    usernames_HTML = (
        '<a style="color: #800080;" href="https://letterboxd.com/'
        + usernames[0]
        + '/watchlist" target="_blank">'
        + usernames[0]
        + "</a>"
    )
    for i in range(1, len(usernames) - 1):
        usernames_HTML = (
            usernames_HTML
            + ", "
            + '<a style="color: #800080;" href="https://letterboxd.com/'
            + usernames[i]
            + '/watchlist" target="_blank">'
            + usernames[i]
            + "</a>"
        )
    usernames_HTML = (
        usernames_HTML
        + " & "
        + '<a style="color: #800080;" href="https://letterboxd.com/'
        + usernames[len(usernames) - 1]
        + '/watchlist" target="_blank">'
        + usernames[len(usernames) - 1]
        + "</a>"
    )
    splitFile = outlineString.split(
        "<!--add names here-->"
    )  # split at specified spot at template
    outlineString = (
        splitFile[0]
        + "\n"
        + '<h3 style="text-align: center;"><span style="color: #800080; font-size: 18px">'
        + usernames_HTML
        + "</span></h3>"
        + "\n"
        + splitFile[1]
    )  # rebuild

    # add total number of movies to bottom right
    splitFile = outlineString.split(
        "<!--add total here-->"
    )  # split at specified spot in template
    outlineString = (
        splitFile[0]
        + "\n"
        + '<p  class="total" style="color:  #4706ca; font-size: 14px" >'
        + str(len(list))
        + " movies in common</p>"
        + "</span><p>"
        + "\n"
        + splitFile[1]
    )  # rebuild

    # get movie information and add each movie to html table
    splitFile = outlineString.split(
        "<!--add movies here-->"
    )  # split at specified spot in template
    outputHTML.write(splitFile[0])  # write first half to html
    counter = 1
    outputHTML.write("<tr>")
    for movie in list:
        # extract name and letterboxd link from html block
        movieLink = movie[
            movie.find('target-link="') + len('target-link="') :
        ]  # get where link begins to rest of file
        movieLink = (
            "https://letterboxd.com" + movieLink[: movieLink.find('"')]
        )  # cuts link to where it ends

        # get movie information (director, year, poster if desired)
        movieInfo = get_movie_info(movieLink, showPosters)

        movieName = movieInfo[0]
        print(movieName)
        movieYear = movieInfo[1]
        print(movieYear)
        movieDirector = movieInfo[2]
        print(movieDirector)
        if showPosters:
            moviePosterLink = movieInfo[3]
            print(moviePosterLink)
        print("\n")

        # fills cell in table
        outputHTML.write(
            '<td style="width: 33.3333%; text-align: center;"><span style="color: #ff00ff; font-size:22px">'
        )
        if showPosters:
            outputHTML.write(
                '<p style="margin:0"><img src="'
                + moviePosterLink
                + '" alt="" width="161" height="238" /></p>'
            )
        outputHTML.write(
            '<a style="color: #ff00ff;margin-top:3px" href="'
            + movieLink
            + '" target="_blank">'
            + movieName
            + "</a>"
        )
        outputHTML.write(
            '<p style="color: #5a5c59; font-size:13px; margin-top:1px">'
            + movieDirector
            + " ("
            + movieYear
            + ")"
            + "</p>"
        )
        outputHTML.write("</span></td>")
        outputHTML.write("\n")
        if counter % 3 == 0:  # new row for every third movie
            outputHTML.write("</tr>\n<tr>\n")
        counter += 1
    print("Finished")
    outputHTML.write(splitFile[1])  # write remaining half to html
    outputHTML.close()
    outlineFile.close()


def get_movie_info(movie_link: str, show_poster: bool = False):
    """
    Obtains movie info for given movie.

    Parameters:
        movie_link: Letterboxd link of movie.
        show_poster: Show movie posters in result.

    Returns:
        movie_info (dict): Dictionary containing 'name', 'year', 'director', 'rating', and (optionally) 'poster'.

    """

    # create request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"
    }
    req = Request(url=movie_link, headers=headers)
    html = urlopen(req).read()

    # get movie info
    movie_info = {}
    soup = BeautifulSoup(html, "html.parser")

    name_year = soup.find("meta", property="og:title")["content"]
    name = name_year[:-7]  # select name
    year = name_year[-6:]  # select year

    director = soup.find("meta", attrs={"name": "twitter:data1"})["content"]

    rating = soup.find("meta", attrs={"name": "twitter:data2"})["content"]

    movie_info["name"] = name
    movie_info["year"] = year
    movie_info["director"] = director
    movie_info["rating"] = rating

    if show_poster:
        poster_link = ""
        try:
            if name.__contains__("&#039;"):
                while name.__contains__("&#039;"):
                    name = (
                        name[: name.find("&#039;")]
                        + "'"
                        + name[name.find("&#039;") + len("&#039;") :]
                    )
            poster_link = imdbapi.get_poster(name + " " + year)
        except Exception as e:
            print("poster error: " + str(e) + " for " + name)
            poster_link = "https://s.ltrbxd.com/static/img/empty-poster-500.825678f0.png"  # return black poster later

        movie_info["poster"] = poster_link

    return movie_info


# if empty path, rerender to form
@app.route("/", methods=["GET", "POST"])
def refresh():
    form = open("templates/form.html", "r")
    formString = form.read()
    form.close()
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
        for i in range(userAmount):
            usernames.append(request.form.get("usr" + str(i + 1)))

        # gets overlap of movies as array of html chunks
        intersection = get_watchlist_overlap(usernames)

        # builds html from overlap
        build_overlap_html(intersection, usernames, showPosters)

        return render_template("watchlist.html")  # display watchlist
    return redirect("/")


# adds text box for another user
@app.route("/add", methods=["GET"])
def addUser():
    if request.method == "GET":
        global userAmount
        userAmount += 1  # update amount of users

        # find where to insert new box
        beforeInsertSubstring = (
            'placeholder = "Letterboxd User ' + str(userAmount - 1) + '">'
        )
        formHtml = open("templates/form.html", "r")
        formHtmlString = formHtml.read()
        index = formHtmlString.find(beforeInsertSubstring) + len(beforeInsertSubstring)

        # copy html form and add in box
        newForm = (
            formHtmlString[0:index]
            + '\n<input type="text" id="username'
            + str(userAmount)
            + '" name="usr'
            + str(userAmount)
            + '" placeholder = "Letterboxd User '
            + str(userAmount)
            + '">'
            + formHtmlString[index:]
        )
        formHtml.close()

        # update html form
        formHtml = open("templates/form.html", "w")
        formHtml.write(newForm)

        formHtml.close()

        # refresh to form
        return redirect("/")
    return redirect("/")


# removes text box for another user
@app.route("/remove", methods=["GET"])
def removeUser():
    global userAmount
    if request.method == "GET" and userAmount > 2:
        # box to be deleted
        deletionSubstring = (
            '\n<input type="text" id="username'
            + str(userAmount)
            + '" name="usr'
            + str(userAmount)
            + '" placeholder = "Letterboxd User '
            + str(userAmount)
            + '">'
        )

        # open html
        formHtml = open("templates/form.html", "r")
        formHtmlString = formHtml.read()

        # copy html and remove at specified index
        index = formHtmlString.find(deletionSubstring)
        newForm = (
            formHtmlString[0:index] + formHtmlString[index + len(deletionSubstring) :]
        )
        formHtml.close()

        # update html form
        formHtml = open("templates/form.html", "w")
        formHtml.write(newForm)
        formHtml.close()
        userAmount -= 1  # update amount of users
        return redirect("/")  # redirect to refresh
    return redirect("/")


# resets form.html and watchlist.html to their respective outlines
def restartForm():
    formHtmlOutline = open("templates/formOutline.html", "r")
    formHtmlOutlineString = formHtmlOutline.read()
    formHtml = open("templates/form.html", "w")
    formHtml.write(formHtmlOutlineString)
    formHtml.close()
    formHtmlOutline.close()


restartForm()
if __name__ == "__main__":
    print("\nRunning at localhost:" + str(port))
    serve(app, host="0.0.0.0", port=port)
