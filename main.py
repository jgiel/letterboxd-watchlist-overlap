#to do:
#sort by runtime, year, etc.
#fix text errors for special characters (salo)
#handle incorrect lb username
import urllib.request
from flask import Flask, request, render_template, redirect
from waitress import serve
from movieposters.movieposters import imdbapi


TEMPLATES_AUTO_RELOAD = True
userAmount = 2
port = 8080

app = Flask(__name__)

#returns array of each movie's HTML contents in the user's Letterboxd watchlist
#(return html content instead of name because need movie's letterboxd link located within HTML content as well)
def getWatchlist(username):
    currentPage = 1
    watchlist = []
    done = False
    beginKey = b'<li' #beginning of each movie entry on watchlist
    endKey = b'</li>' #end of each movie entry block on watchlist

    #loops through each page of watchlist
    while not done:
        #create request to letterboxd url HTML
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
        url = 'https://www.letterboxd.com/'+username+'/watchlist/page/'+str(currentPage)+'/'
        req = urllib.request.Request(url = url, headers=headers)

        #obtain HTML contents of watchlist
        html = urllib.request.urlopen(req)
        htmlString = html.read()
        htmlString = htmlString[htmlString.find(b'poster-list'): htmlString.find(b'pagination')]  #change html string to only include the poster list

        #find beginning first movie entry
        beginIndex = htmlString.find(beginKey)
        if beginIndex == -1: #if first movie not found, page must be empty
            done = True
        else: #otherwise, scrape each movie
            pageEmpty = False
            while not pageEmpty:
                #get ending index of movie entry
                endIndex = htmlString.find(endKey)

                movie = htmlString[beginIndex:endIndex+1].decode("utf-8")+ '</li> \n' #get html chunk containing movie info
                
                watchlist.append(movie) #add to watchlist               
                
                htmlString = htmlString[endIndex+3:] #get rid of movie from html string before moving on

                #get index of next movie (if doesnt exist, page empty)
                beginIndex = htmlString.find(beginKey)
                if beginIndex == -1: #if no next movie, then exit while loop and get new url for next page
                    pageEmpty = True
                    currentPage+=1
                
    return watchlist

#returns overlap of watchlists
def getOverlap(usernames):
    #get list of watchlists
    watchlists = []
    for i in range(len(usernames)):
        watchlists.append(getWatchlist(usernames[i]))

    #find overlap
    overlap = []
    for i in range(len(watchlists)):
        if i == 0:
            overlap = watchlists[0] #set overlap to first watchlist
        else:
            overlap = list(set(overlap) & set(watchlists[i])) #set overlap to intersection between prev overlap and current watchlsit
    return overlap



def buildOverlapHTML(list, usernames, showPosters):
    #open outline and watchlist htmls
    outlineFile = open('templates/watchlistOutline.html', "r")
    outputHTML = open('templates/watchlist.html', 'w')
    outlineString = outlineFile.read()

    #create usernames as HTML hyperlinks for second header (comma/& separated)
    usernames_HTML = '<a style="color: #800080;" href="https://letterboxd.com/'+usernames[0]+'/watchlist" target="_blank">'+usernames[0]+'</a>'
    for i in range(1, len(usernames)-1):
        usernames_HTML = usernames_HTML+", "+'<a style="color: #800080;" href="https://letterboxd.com/'+usernames[i]+'/watchlist" target="_blank">'+usernames[i]+'</a>'
    usernames_HTML = usernames_HTML + ' & ' + '<a style="color: #800080;" href="https://letterboxd.com/'+usernames[len(usernames)-1]+'/watchlist" target="_blank">'+usernames[len(usernames)-1]+'</a>'
    splitFile = outlineString.split('<!--add names here-->') #split at specified spot at template
    outlineString = splitFile[0] + '\n'+'<h3 style="text-align: center;"><span style="color: #800080; font-size: 18px">'+usernames_HTML+'</span></h3>'+'\n'+splitFile[1] #rebuild

    #add total number of movies to bottom right
    splitFile = outlineString.split('<!--add total here-->')#split at specified spot in template
    outlineString = splitFile[0] + '\n' + '<p  class="total" style="color:  #4706ca; font-size: 14px" >'+str(len(list))+ ' movies in common</p>'+'</span><p>'+'\n'+splitFile[1] #rebuild

    #get movie information and add each movie to html table
    splitFile = outlineString.split('<!--add movies here-->')#split at specified spot in template
    outputHTML.write(splitFile[0]) #write first half to html
    counter = 1
    outputHTML.write('<tr>')
    for movie in list: 
        #extract name and letterboxd link from html block
        movieLink = movie[movie.find('target-link="')+len('target-link="'):] #get where link begins to rest of file
        movieLink = "https://letterboxd.com" + movieLink[:movieLink.find('"')] #cuts link to where it ends

        #get movie information (director, year, poster if desired)
        movieInfo = getMovieInfo(movieLink, showPosters)

        movieName = movieInfo[0]
        print(movieName) 
        movieYear = movieInfo[1]
        print(movieYear)
        movieDirector = movieInfo[2]
        print(movieDirector)
        if showPosters:
            moviePosterLink = movieInfo[3]
            print(moviePosterLink)
        print('\n')

        #fills cell in table
        outputHTML.write('<td style="width: 33.3333%; text-align: center;"><span style="color: #ff00ff; font-size:22px">')
        if(showPosters):
            outputHTML.write('<p style="margin:0"><img src="'+moviePosterLink+'" alt="" width="161" height="238" /></p>')
        outputHTML.write('<a style="color: #ff00ff;margin-top:3px" href="'+movieLink+'" target="_blank">'+movieName+'</a>')
        outputHTML.write('<p style="color: #5a5c59; font-size:13px; margin-top:1px">'+movieDirector+' ('+movieYear+')'+'</p>')
        outputHTML.write('</span></td>')
        outputHTML.write('\n')
        if counter % 3 == 0: #new row for every third movie
            outputHTML.write('</tr>\n<tr>\n')
        counter += 1
    print('Finished')
    outputHTML.write(splitFile[1]) #write remaining half to html
    outputHTML.close()
    outlineFile.close()

#return name of movie, year, director, and poster link in 4 element array

def getMovieInfo(movieLink, showPosters):

    #create request
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
    req = urllib.request.Request(url = movieLink, headers=headers)

    #get html
    htmlString = urllib.request.urlopen(req).read().decode("utf-8")
    htmlString = htmlString[htmlString.find('<head>'):htmlString.find('<script>')] #chop off unneccessary portions of

    #get film's name
    name = ""
    try:
        nameIndex = htmlString.find('property="og:title" content="')+len('property="og:title" content="')
        if nameIndex == -1:
            raise Exception
        name = htmlString[nameIndex:]
        nameEndIndex = name.find(' (')
        if name[nameEndIndex + len(' (xxxx')] != ')': #checks that this is year paren, not paren in title
            nameEndIndex = name[nameEndIndex+1:].find(' (')
        name = name[:name.find(' (')] # (?) change to :nameEndIndex
    except Exception as e:
        print("name error: " +str(e)+" for "+name)
        name = "Name not found"

    #get film's year
    year = ""
    try:
        yearIndex = nameIndex + len(name) + len(' (')
        if yearIndex == -1:
            raise Exception
        year = htmlString[yearIndex:yearIndex+4]
    except Exception as e:
        print("year error: " +str(e)+" for "+name)
        year = "xxxx"
        
    #get director(s)
    directors = ""
    try:
        directorIndex = htmlString.find('content="Directed by" /><meta name="twitter:data') + len('content="Directed by" /><meta name="twitter:datax" content="')
        if directorIndex == -1:
            raise Exception
        directors = htmlString[directorIndex:] #set directors to rest of string
        directors = directors[:directors.find('"')] #chop off rest at quotation
    except Exception as e:
        print("director error: " +str(e)+" for "+name)
        directors = "Not found"

    #get poster (if desired) 
    if showPosters:
        
        posterLink = ""
        try:
            if name.__contains__('&#039;'):
                while name.__contains__('&#039;'):
                    name = name[:name.find('&#039;')] + "'"+ name[name.find('&#039;')+len('&#039;'):]
            posterLink = imdbapi.get_poster(name +" "+ year)
        except Exception as e:
            print("poster error: " +str(e)+" for "+name)
            posterLink = 'https://s.ltrbxd.com/static/img/empty-poster-500.825678f0.png' #return black poster later
        return [name, year, directors, posterLink]  
    else:
        return [name, year, directors]


#if empty path, rerender to form
@app.route('/', methods = ["GET", "POST"])
def refresh():
    form = open('templates/form.html', 'r')
    formString = form.read()
    form.close()
    return formString

#takes user input for usernames and finds displays watchlist overlap
@app.route('/showoverlap', methods = ["POST"])
def enter():
    usernames = []
    if request.method == "POST":
        #determine which button is pressed
        if(request.form['poster_type']=="yes_poster"):
            showPosters = True
        else:
            showPosters = False
        
        #get all usernames
        for i in range(userAmount):
            usernames.append(request.form.get("usr"+str(i+1)))

        #gets overlap of movies as array of html chunks
        intersection = getOverlap(usernames)
        
        #builds html from overlap
        buildOverlapHTML(intersection, usernames, showPosters)
        
        return render_template("watchlist.html") #display watchlist
    return redirect('/')

#adds text box for another user
@app.route('/add', methods = ["GET"])
def addUser():
    if request.method == "GET":
        global userAmount
        userAmount += 1 #update amount of users

        #find where to insert new box
        beforeInsertSubstring = 'placeholder = "Letterboxd User '+str(userAmount-1)+'">'
        formHtml = open("templates/form.html", "r")
        formHtmlString = formHtml.read()
        index = formHtmlString.find(beforeInsertSubstring)+len(beforeInsertSubstring)

        # copy html form and add in box
        newForm = formHtmlString[0:index] + '\n<input type="text" id="username'+str(userAmount)+'" name="usr'+str(userAmount)+'" placeholder = "Letterboxd User '+str(userAmount)+'">'+ formHtmlString[index:]
        formHtml.close()

        # update html form
        formHtml = open('templates/form.html', 'w')
        formHtml.write(newForm)

        formHtml.close()
        
        #refresh to form
        return redirect('/')
    return redirect('/')
        
#removes text box for another user
@app.route('/remove', methods = ["GET"])
def removeUser():
    global userAmount
    if request.method == "GET" and userAmount > 2:
        #box to be deleted
        deletionSubstring = '\n<input type="text" id="username'+str(userAmount)+'" name="usr'+str(userAmount)+'" placeholder = "Letterboxd User '+str(userAmount)+'">'
        
        #open html 
        formHtml = open("templates/form.html", "r")
        formHtmlString = formHtml.read()

        #copy html and remove at specified index
        index = formHtmlString.find(deletionSubstring)
        newForm = formHtmlString[0:index] + formHtmlString[index+len(deletionSubstring):]
        formHtml.close()

        #update html form
        formHtml = open('templates/form.html', 'w')
        formHtml.write(newForm)
        formHtml.close()
        userAmount -=1 #update amount of users 
        return redirect('/') #redirect to refresh
    return redirect('/')


#resets form.html and watchlist.html to their respective outlines
def restartForm():
    formHtmlOutline = open('templates/formOutline.html', 'r')
    formHtmlOutlineString = formHtmlOutline.read()
    formHtml = open('templates/form.html', 'w')
    formHtml.write(formHtmlOutlineString)
    formHtml.close()
    formHtmlOutline.close()

restartForm()
if __name__ == "__main__":
    print("\nRunning at localhost:"+str(port))
    serve(app, host="0.0.0.0", port=port)