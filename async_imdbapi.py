from bs4 import BeautifulSoup
import asyncio
import aiohttp
import urllib

# HEADERS = {
#     "Connection": "keep-alive",
#     "sec-ch-ua": '"Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
#     "currency": "USD",
#     "sec-ch-ua-mobile": "?0",
#     "User-Agent": (
#         "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
#         " (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
#     ),
#     "Content-Type": "application/json;charset=UTF-8",
#     "Accept-Language": "en",
#     "Accept": "application/json, text/plain, */*",
#     "channel": "IBE",
#     "Sec-Fetch-Site": "same-site",
#     "Sec-Fetch-Mode": "cors",
#     "Sec-Fetch-Dest": "empty",
# }

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"
}
# get poster from link


def get_src_of_poster_div(div):
    try:
        return _get_best_src_of_img(div.img)
    except AttributeError:
        raise Exception("poster not found")


def _get_best_src_of_img(img):
    try:
        srcset = img["srcset"].split(", ")
    except KeyError:
        return img["src"]  # fallback

    best_quality = srcset[-1]
    return best_quality.split(" ")[0]


async def get_poster_from_link(session, link):
    # await asyncio.sleep(1)
    async with session.get(url=link, headers=HEADERS) as response:
        soup = BeautifulSoup(await response.text(), features="lxml")
        poster_div = soup.find("div", class_="ipc-media")
        if not poster_div:
            print(f"POSTER DIV NOT FOUND for {link}")
            # asyncio.sleep(1)
            # return await get_poster_from_link(session, await get_link_from_title(session, title), title)
            return "No Poster Found"
        else:
            print(f"FOUND POSTER FOR {link}")
            return get_src_of_poster_div(poster_div)


# get imdb link of movie


def _is_relative_link_to_title(link):
    return link.startswith("/title")


def get_imdb_link_from_relative(link):
    return "https://imdb.com" + link


async def get_link_from_search_results(response, title):

    soup = BeautifulSoup(await response.text(), features="lxml")
    # with open(f"response_{title}.html", "w") as f:
    #     f.write(await response.text())
    a_tag = soup.find("a", href=_is_relative_link_to_title)
    if not a_tag:
        raise Exception("movie not found")
    return get_imdb_link_from_relative(a_tag["href"])


async def get_link_from_title(session, title):

    search_url = "https://imdb.com/find/?s=tt&q=" + urllib.parse.quote_plus(title)

    print("SEARCH URL: ", search_url)
    # await asyncio.sleep(1)
    async with session.get(url=search_url, headers=HEADERS) as response:
        try:
            link = await get_link_from_search_results(response, title)
            # print("IMDB LINK: ", link)
            return link
        except Exception:
            raise Exception(f"movie not found, {title!r} not found on IMDb")


# main method


async def get_poster_from_title(session, title):  # semaphore, title):
    # async with semaphore:
    link = await get_link_from_title(session, title)
    return await get_poster_from_link(session, link)
