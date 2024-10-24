from urllib.request import Request, urlopen

import aiohttp
from bs4 import BeautifulSoup
# from movieposters import imdbapi
import async_imdbapi
import asyncio

from time import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"
}


async def get_movie_info(session, semaphore, movie_link: str, show_poster: bool = False):
    """
    Obtains movie info for given movie.

    Parameters:
        movie_link: Letterboxd link of movie.
        show_poster: Show movie posters in result.

    Returns:
        movie_info (dict): Dictionary containing 'name', 'year', 'director', 'rating', 'link', and (optionally) 'poster'.

    """
    tic = time()
    # create request
    async with semaphore and session.get(url=movie_link, headers=HEADERS) as response:
    # html = urlopen(req).read()

        # get movie info
        movie_info = {}
        soup = BeautifulSoup(await response.text(), "html.parser")

        name_and_year = soup.find("meta", property="og:title")["content"]
        name = name_and_year[:-7]  # select name
        year = name_and_year[-6:]  # select year

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
                # replace apostrophes (not necessary w bs4?)
                # if name.__contains__("&#039;"):
                #     while name.__contains__("&#039;"):
                #         name = (
                #             name[: name.find("&#039;")]
                #             + "'"
                #             + name[name.find("&#039;") + len("&#039;") :]
                #         )
                poster_link = await async_imdbapi.get_poster_from_title(session, name + " " + year)
            except Exception as e:
                print("poster error: " + str(e) + " for " + name)
                poster_link = "https://s.ltrbxd.com/static/img/empty-poster-500.825678f0.png"  # return black poster later

            movie_info["poster"] =  poster_link
            print(f"got poster link for {movie_info["name"]}: {poster_link}")

        print(f"retrieved info for {movie_info["name"]} in {time()-tic}")
        with open("movie_info.txt", "a") as f:
            f.write(str(movie_info) + "\n")

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
        print(f"getting watchlist of {username}, page {current_page}")
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


async def get_watchlist_overlap(usernames: list, show_posters: bool):
    """
    Gets overlap of watchlists of given users.

    Parameters:
        usernames: List of Letterboxed users.
        show_posters: Whether to retrieve posters.

    Returns:
        watchlist_overlap (list): List of dicts containing 'name', 'year', 'director', 'rating', and (optionally) 'poster'..

    """
    print("getting overlap")
    print(f"getting watchlist for {usernames[0]}")
    overlap_links = get_watchlist(usernames[0])
    for i in range(1, len(usernames)):
        print(f"getting overlap with {usernames[i]}")

        overlap_links = list(set(overlap_links) & set(get_watchlist(usernames[i])))
        print(f"DONE getting overlap with {usernames[i]}")

    semaphore = asyncio.Semaphore(20) # limit to 5 concurrent requests
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        overlap = await asyncio.gather(*[get_movie_info(session, semaphore, link, show_posters) for link in overlap_links])
    print("done getting overlap")

    return overlap
