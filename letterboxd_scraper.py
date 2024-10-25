import asyncio

import aiohttp
import requests
from bs4 import BeautifulSoup

from constants import HEADERS, logger
from imdb_scraper import get_poster_from_title


async def get_movie_info(
    session: aiohttp.ClientSession,
    letterboxd_semaphore: asyncio.Semaphore,
    imdb_semaphore: asyncio.Semaphore,
    movie_link: str,
    show_poster: bool = False,
):
    """
    Obtains movie info for given movie.

    Parameters:
        `session`: Current aiohttp session.
        `semaphore`: asyncio semaphore.
        `movie_link`: Letterboxd link of movie.
        `show_poster`: Show movie posters in result.

    Returns:
        Dictionary containing 'name', 'year', 'director', 'rating', 'link', and (optionally) 'poster'.

    """
    # create request
    async with letterboxd_semaphore and session.get(
        url=movie_link, headers=HEADERS
    ) as response:

        # get movie info
        movie_info = {}
        soup = BeautifulSoup(await response.text(), "html.parser")

        name_and_year = soup.find("meta", property="og:title")
        if name_and_year:
            name_and_year = name_and_year["content"]
            name = name_and_year[:-7]  # select name
            year = name_and_year[-6:]  # select year
        else:
            name = ""
            year = ""

        director = soup.find("meta", attrs={"name": "twitter:data1"})
        if director:
            director = director["content"]
        else:
            director = ""

        rating = soup.find("meta", attrs={"name": "twitter:data2"})
        if rating:
            rating = rating["content"]
        else:
            rating = ""

        movie_info["name"] = name
        movie_info["year"] = year
        movie_info["director"] = director
        movie_info["rating"] = rating
        movie_info["link"] = movie_link

    if show_poster:
        async with imdb_semaphore:
            poster_link = ""
            try:

                poster_link = await get_poster_from_title(session, name + " " + year)
            except Exception as e:
                logger.exception(f"Error obtaining poster for {name}: " + str(e))

            movie_info["poster"] = poster_link

    return movie_info


async def get_movies_from_page(
    session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, page_link: str
):
    """
    Gets link to each movie in current watchlist page.

    Parameters:
        `session`: Current aiohttp session.
        `semaphore`: asyncio semaphore.
        `page_link`: Link to watchlist page.
    Returns:
        List of links to each movie on watchlist page.
    """
    async with semaphore and session.get(url=page_link) as response:

        # parse with bs4
        soup = BeautifulSoup(await response.text(), "html.parser")
        containers = soup.find_all("li", class_="poster-container")

        return [
            "https://letterboxd.com" + container.find("div")["data-target-link"]
            for container in containers
        ]


async def get_watchlist(
    session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, username: str
):
    """
    Obtains list of all links to movies in user's watchlist.

    Parameters:
        `username`: Username of Letterboxd user.

    Returns:
        List of Letterboxd links to films in user's watchlist.

    """

    # find num of pages in watchlist
    req = requests.get(url=f"https://letterboxd.com/{username}/watchlist/")
    soup = BeautifulSoup(req.text, "html.parser")

    paginations = soup.find_all("li", class_="paginate-page")

    if paginations:
        num_pages = int(paginations[-1].string)
    else:
        num_pages = 1

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
    #  unpack movies from each page to single list
    movie_links = []
    for result in results:
        movie_links.extend(result)

    return movie_links


async def get_watchlist_overlap(usernames: list, show_posters: bool):
    """
    Gets overlap of watchlists of given users.

    Parameters:
        `usernames`: List of Letterboxed users.
        `show_posters`: Whether to retrieve posters.

    Returns:
        List of dicts containing 'name', 'year', 'director', 'rating', and (optionally) 'poster' in overlap between users' watchlists.

    """

    letterboxd_semaphore = asyncio.Semaphore(20)  # limit to 5 concurrent requests
    imdb_semaphore = asyncio.Semaphore(20)
    async with aiohttp.ClientSession(headers=HEADERS) as session:

        # get overlap between users' watchlists
        overlap_links = await get_watchlist(session, letterboxd_semaphore, usernames[0])
        for i in range(1, len(usernames)):

            overlap_links = list(
                set(overlap_links)
                & set(await get_watchlist(session, letterboxd_semaphore, usernames[i]))
            )

        # get information about each movie in overlap
        overlap = await asyncio.gather(
            *[
                get_movie_info(
                    session, letterboxd_semaphore, imdb_semaphore, link, show_posters
                )
                for link in overlap_links
            ]
        )

    return overlap
