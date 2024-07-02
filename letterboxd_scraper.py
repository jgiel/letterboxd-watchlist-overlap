from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from movieposters import imdbapi


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"
}


def get_movie_info(movie_link: str, show_poster: bool = False):
    """
    Obtains movie info for given movie.

    Parameters:
        movie_link: Letterboxd link of movie.
        show_poster: Show movie posters in result.

    Returns:
        movie_info (dict): Dictionary containing 'name', 'year', 'director', 'rating', 'link', and (optionally) 'poster'.

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
    movie_info["link"] = movie_link

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


def get_watchlist(username: str):
    """
    Obtains list of all links to movies in user's watchlist.

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
        req = Request(url=url, headers=HEADERS)
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


def get_watchlist_overlap(usernames: list, show_posters: bool):
    """
    Gets overlap of watchlists of given users.

    Parameters:
        usernames: List of Letterboxed users.
        show_posters: Whether to retrieve posters.

    Returns:
        watchlist_overlap (list): List of dicts containing 'name', 'year', 'director', 'rating', and (optionally) 'poster'..

    """

    overlap_links = get_watchlist(usernames[0])
    for i in range(1, len(usernames)):
        overlap_links = list(set(overlap_links) & set(get_watchlist(usernames[i])))

    overlap = [get_movie_info(link, show_posters) for link in overlap_links]
    return overlap
