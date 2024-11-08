# modified from https://github.com/thomasbreydo/movieposters to run async
from __future__ import annotations

import urllib

from bs4 import BeautifulSoup

from constants import HEADERS
from errors import MovieNotFound, PosterNotFound


def get_src_of_poster_div(div):
    """
    Gets best src of given poster div.

    Parameters:
        `div` (bs4.element.Tag): current div
    Returns:
        Link to poster
    """
    try:
        # get best src of div
        try:
            srcset = div.img["srcset"].split(", ")
        except KeyError:
            return div.img["src"]  # fallback
    except AttributeError:
        raise PosterNotFound

    best_quality = srcset[-1]
    return best_quality.split(" ")[0]


async def get_poster_from_link(session, link: str):
    """
    Gets poster from IMDB link of movie.

    Parameters:
        `session`: Current aiohttp session.
        `link`: IMDb link to movie.
    Returns:
        Link to poster.
    """
    async with session.get(url=link, headers=HEADERS) as response:
        soup = BeautifulSoup(await response.text(), features="lxml")
        poster_div = soup.find("div", class_="ipc-media")
        if not poster_div:
            raise PosterNotFound("Poster not found.")
        else:
            return get_src_of_poster_div(poster_div)


def _is_relative_link_to_title(link):
    """
    Used by bs4 to find desired relative link.
    """
    return link.startswith("/title")


def get_imdb_link_from_relative(link):
    """
    Gets IMDb link from relative link found by bs4.
    """
    return "https://imdb.com" + link


async def get_link_from_search_results(response):
    """
    Retrieves movie link from search page.

    Parameters:
        `response`: Response containing search results.
    Returns:
        IMDb link of movie.
    """
    soup = BeautifulSoup(await response.text(), features="lxml")
    a_tag = soup.find("a", href=_is_relative_link_to_title)
    if not a_tag:
        raise MovieNotFound
    return get_imdb_link_from_relative(a_tag["href"])


async def get_link_from_title(session, title: str):
    """
    Gets IMDb link of movie from title.

    Parameters:
        `session`: Current aiohttp session.
        `title`: Title of movie.
    Returns:
        IMDb link of movie.

    """

    search_url = "https://imdb.com/find/?s=tt&q=" + urllib.parse.quote_plus(title)

    async with session.get(url=search_url, headers=HEADERS) as response:

        link = await get_link_from_search_results(response)
        return link


async def get_poster_from_title(session, title: str):  
    """
    Gets link to poster from movie title.

    Parameters:
        `session`: Current aiohttp session.
        `title`: Title of movie.
    Returns:
        Link to movie poster.
    """
    link = await get_link_from_title(session, title)
    return await get_poster_from_link(session, link)
