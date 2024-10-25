from urllib.request import Request, urlopen

import aiohttp
from bs4 import BeautifulSoup

# from movieposters import imdbapi
import async_imdbapi
import asyncio
import requests

from time import time


# TODO: put in external file
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"
}


async def get_movie_info(
    session, letterboxd_semaphore, imdb_semaphore, movie_link: str, show_poster: bool = False
):
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
    async with letterboxd_semaphore and session.get(url=movie_link, headers=HEADERS) as response:
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
        async with imdb_semaphore:
            poster_link = ""
            try:
                # replace apostrophes (TODO: not necessary w bs4?)
                # if name.__contains__("&#039;"):
                #     while name.__contains__("&#039;"):
                #         name = (
                #             name[: name.find("&#039;")]
                #             + "'"
                #             + name[name.find("&#039;") + len("&#039;") :]
                #         )
                poster_link = await async_imdbapi.get_poster_from_title(
                    session, name + " " + year
                )
            except Exception as e:
                print("poster error: " + str(e) + " for " + name)
                poster_link = "https://s.ltrbxd.com/static/img/empty-poster-500.825678f0.png"  # return black poster later

            movie_info["poster"] = poster_link
            print(f"got poster link for {movie_info["name"]}: {poster_link}")

        print(f"retrieved info for {movie_info["name"]} in {time()-tic}")
        with open("movie_info.txt", "a") as f:
            f.write(str(movie_info) + "\n")

    return movie_info


async def get_movies_from_page(session, semaphore, page_link):

    async with semaphore and session.get(url=page_link) as response:

        # parse with bs4
        soup = BeautifulSoup(await response.text(), "html.parser")
        containers = soup.find_all("li", class_="poster-container")

        return [
            "https://letterboxd.com" + container.find("div")["data-target-link"]
            for container in containers
        ]


async def get_watchlist(session, semaphore, username: str):
    """
    Obtains list of all links to movies in user's watchlist.

    Parameters:
        username: Username of Letterboxd user

    Returns:
        watchlist: List of Letterboxd links to films in user's watchlist

    """

    # find num of pages in watchlist
    req = requests.get(url=f"https://letterboxd.com/{username}/watchlist/")
    soup = BeautifulSoup(req.text, "html.parser")

    paginations = soup.find_all("li", class_="paginate-page")

    num_pages = int(paginations[-1].string)

    results = await asyncio.gather(
        *(
            get_movies_from_page(
                session,
                semaphore,
                f"https://letterboxd.com/{username}/watchlist/page/{page}/",
            )
            for page in range(1, num_pages + 1)
    )
    )
    #  unpack to 1d list (TODO: find better way to do this)
    movie_links = []
    for result in results:
        movie_links.extend(result)
    
    return movie_links


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

    letterboxd_semaphore = asyncio.Semaphore(20)  # limit to 5 concurrent requests
    imdb_semaphore = asyncio.Semaphore(3)
    async with aiohttp.ClientSession(headers=HEADERS) as session:

        overlap_links = await get_watchlist(session, letterboxd_semaphore, usernames[0]) # use different semaphore here?
        print("OVERLAP LINKS: ", overlap_links)
        for i in range(1, len(usernames)):
            print(f"getting overlap with {usernames[i]}")

            overlap_links = list(set(overlap_links) & set(await get_watchlist(session, letterboxd_semaphore, usernames[i])))
            print(f"DONE getting overlap with {usernames[i]}")

        
        overlap = await asyncio.gather(
            *[
                get_movie_info(session, letterboxd_semaphore, imdb_semaphore, link, show_posters)
                for link in overlap_links
            ]
        )
    print("done getting overlap")

    return overlap
