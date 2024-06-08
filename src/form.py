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
USER_AMOUNT = 2
PORT = 8080
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"
}

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
                "https://letterboxd.com" + container.find("div")["data-target-link"]
            )
            # print(container.find("div")["data-target-link"])

        if not containers:
            return watchlist
        else:
            current_page += 1
            # print("page " + str(current_page) + "\n")


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


def build_overlap_html(movie_links: list, usernames: list, show_posters: bool):
    """
    Builds HTML of overlap page.

    Parameters:
        movie_links: List of Letterboxd movie links.
        usernames: List of Letterboxd usernames.
        show_posters: Whether to show posters in output.

    """
    # open outline and watchlist htmls
    with open("templates/watchlistOutline.html", "r") as outline:
        outline_string = outline.read()

    with open("templates/watchlist.html", "w") as output_html:

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

        # split at specified spot at template and fill in usernames
        split_file = outline_string.split("<!--add names here-->")
        outline_string = (
            split_file[0]
            + "\n"
            + '<h3 style="text-align: center;"><span style="color: #800080; font-size: 18px">'
            + usernames_HTML
            + "</span></h3>"
            + "\n"
            + split_file[1]
        )

        # add total number of movie_links to bottom right
        split_file = outline_string.split("<!--add total here-->")
        outline_string = (
            split_file[0]
            + "\n"
            + '<p  class="total" style="color:  #4706ca; font-size: 14px" >'
            + str(len(movie_links))
            + " films in common</p>"
            + "</span><p>"
            + "\n"
            + split_file[1]
        )

        # get movie information and write to html
        split_file = outline_string.split("<!--add movies here-->")
        output_html.write(split_file[0])
        output_html.write("<tr>")

        counter = 1
        for movie in movie_links:
            # get movie information (director, year, poster if desired)
            movie_info = get_movie_info(movie, show_posters)
            movie_name = movie_info["name"]
            print(movie_name)
            movie_year = movie_info["year"]
            print(movie_year)
            movie_director = movie_info["director"]
            print(movie_director)
            if show_posters:
                movie_poster_link = movie_info["poster"]
                print(movie_poster_link)
            print("\n")

            # fills movies in html
            output_html.write(
                '<td style="width: 33.3333%; text-align: center;"><span style="color: #ff00ff; font-size:22px">'
            )
            if show_posters:
                output_html.write(
                    '<p style="margin:0"><img src="'
                    + movie_poster_link
                    + '" alt="" width="161" height="238" /></p>'
                )
            output_html.write(
                '<a style="color: #ff00ff;margin-top:3px" href="'
                + movie
                + '" target="_blank">'
                + movie_name
                + "</a>"
            )
            output_html.write(
                '<p style="color: #5a5c59; font-size:13px; margin-top:1px">'
                + movie_director
                + " "
                + movie_year
                + "</p>"
            )
            output_html.write("</span></td>")
            output_html.write("\n")
            if counter % 3 == 0:  # new row for every third movie
                output_html.write("</tr>\n<tr>\n")
            counter += 1

        output_html.write(split_file[1])  # write remaining half to html
        output_html.close()


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
    req = Request(url=movie_link, headers=HEADERS)
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
        for i in range(USER_AMOUNT):
            usernames.append(request.form.get("usr" + str(i + 1)))

        # gets overlap of movies as array of html chunks
        intersection = get_watchlist_overlap(usernames)

        # builds html from overlap
        build_overlap_html(intersection, usernames, showPosters)

        return render_template("watchlist.html")  # display watchlist
    return redirect("/")


# adds text box for another user
@app.route("/add", methods=["POST"])
def addUser():
    if request.method == "POST":
        global USER_AMOUNT
        USER_AMOUNT += 1  # update amount of users

        # find where to insert new box
        beforeInsertSubstring = (
            'placeholder = "Letterboxd User ' + str(USER_AMOUNT - 1) + '">'
        )
        formHtml = open("templates/form.html", "r")
        formHtmlString = formHtml.read()
        index = formHtmlString.find(beforeInsertSubstring) + len(beforeInsertSubstring)

        # copy html form and add in box
        newForm = (
            formHtmlString[0:index]
            + '\n<input type="text" id="username'
            + str(USER_AMOUNT)
            + '" name="usr'
            + str(USER_AMOUNT)
            + '" placeholder = "Letterboxd User '
            + str(USER_AMOUNT)
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
@app.route("/remove", methods=["POST"])
def removeUser():
    global USER_AMOUNT
    if request.method == "POST" and USER_AMOUNT > 2:
        # box to be deleted
        deletionSubstring = (
            '\n<input type="text" id="username'
            + str(USER_AMOUNT)
            + '" name="usr'
            + str(USER_AMOUNT)
            + '" placeholder = "Letterboxd User '
            + str(USER_AMOUNT)
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
        USER_AMOUNT -= 1  # update amount of users
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


if __name__ == "__main__":
    restartForm()
    print("\nRunning at localhost:" + str(PORT))
    serve(app, host="0.0.0.0", port=PORT)
