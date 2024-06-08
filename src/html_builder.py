from os.path import dirname, abspath

from letterboxd_scraper import get_movie_info


def build_overlap_html(movie_links: list, usernames: list, show_posters: bool):
    """
    Builds HTML of overlap page.

    Parameters:
        movie_links: List of Letterboxd movie links.
        usernames: List of Letterboxd usernames.
        show_posters: Whether to show posters in output.

    """
    # open outline and watchlist htmls

    outline_path = (
        dirname(dirname(abspath(__file__))) + "/templates/watchlistOutline.html"
    )
    with open(outline_path, "r") as outline:
        outline_string = outline.read()

    output_path = dirname(dirname(abspath(__file__))) + "/templates/watchlist.html"
    with open(output_path, "w") as output_html:

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
