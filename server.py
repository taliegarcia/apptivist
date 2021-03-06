"""Apptivist Server"""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session, json, jsonify, url_for
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Article, Tag, Meetup, GlobalGiving, Action, article_tags, connect_to_db, db
from serializer import UserSerializer, ArticleSerializer, ActionSerializer

from modules.suncongress import gen_rep_list
from modules.meetup import list_events
from modules.global_giving import list_giving_projs
from modules.og import PyOpenGraph as pyog

import datetime

app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"


app.jinja_env.undefined = StrictUndefined

###############################################################################
    ### Homepage - News Feed ###
    
@app.route('/')
def show_newsfeed():
    """Display newsfeed on Homepage, order by most recent date."""

    articles = Article.query.order_by(Article.date.desc()).all()
   
    return render_template("newsfeed.html", articles=articles)

###############################################################################
    ### Filter News Feed ###
    
@app.route('/news/<tag_name>', methods=["GET"])
def filter_newsfeed_by_tag(tag_name):
    """Filter newsfeed to only show articles associated with a particular tag"""

    tag = Tag.query.filter_by(tag_name=tag_name).first()

    # query object
    articles_by_tag = tag.article_list

    return render_template("newsfeed.html", articles=articles_by_tag)


###############################################################################
    ### User Registration ###

@app.route('/registration', methods=['GET'])
def register_form():
    """Show form for user signup."""

    return render_template("reg_form.html")


@app.route('/registration', methods=['POST'])
def register_process():
    """Process reg, add user to db, add user to current server session."""

    # Get form variables
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    zipcode = request.form["zipcode"]

    new_user = User(name=name, email=email, password=password, zipcode=zipcode)

    db.session.add(new_user)
    db.session.commit()

    # automatically log in the new user:
    session["user_name"] = new_user.name

    flash("Welcome to the movement, %s. You are now logged in and ready to get active!" % name)

    print User.query.filter_by(name=name).first()

    return redirect("/")

###############################################################################
    ### User Login/Logout ###

@app.route('/login', methods=['GET'])
def login_form():
    """Show login form."""

    return render_template("login.html")


@app.route('/login', methods=['POST'])
def login_process():
    """Process login information"""

    name = request.form["name"]
    password = request.form["password"]

    user = User.query.filter_by(name=name).first()

    if not user:
        print "No such user"
        return redirect("/login")

    if user.password != password:
        print "Incorrect password"
        return redirect("/login")

    session["user_name"] = name

    print "Logged in"

    return redirect("/apptivist/%s" % user.name)


@app.route('/logout')
def logout():
    """Log out the user from the session."""

    del session["user_name"]
    flash("Logged Out.")
    return redirect("/")

###############################################################################
    ### User Profile Page ###

@app.route("/apptivist/<name>")
def get_user_by_name(name):
    """Display user info page by user's name'"""

    user = User.query.filter_by(name=name).first()
    print user.name
    return render_template("profile.html", 
                            user=user, 
                            articles=user.articles, 
                            actions=user.actions)

@app.route("/apptivist/<int:id>")
def get_user_by_id(id):
    """Display user info page by user_id. This handles the d3 tree links."""


    user = User.query.get(id)

    user_url = "/apptivist/" + user.name

    return redirect(user_url)


###############################################################################
    ### Post New Article Page ###

@app.route("/new_post")
def new_post_form():
    """Display postArticle form on page"""
    return render_template("new_post.html")

@app.route("/post_article", methods=["POST"])
def post_to_db():
    """Handles form post of new article.

    When the form is submitted, this will add the new article to the
    db. It will also return the new article's url to the js AJAX call.
    The ajax call will handle redirecting to the resulting url."""

    url = request.form.get('url')
    title = request.form.get('title')
    img_src = request.form.get('img_src')
    date_str = request.form.get('date')
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    tags = json.loads(request.form.get('tagList'))
    print "()()()() These are the TAGS:", tags

    user = User.query.filter_by(name=session['user_name']).first()
    ### Add New Article to the articles table ###
    article = Article(title=title,
                        url=url,
                        img_src=img_src,
                        date=date,
                        user_id=user.user_id)

    db.session.add(article)
    db.session.commit() # needs to be committed here before it can be added to article_tags table below
    print "SUCCESSFULLY added new article!!!"

    ### Append New ArticleTag Association(s) to the articletags tables ###
    article = Article.query.filter_by(title=title).first()
    for tag_name in tags:
        print tag_name
        tag = Tag.query.filter_by(tag_name=tag_name).first()
        article.tag_list.append(tag)

    db.session.commit()

    article_address = "/article/" + article.title

    return article_address

###############################################################################
    ### OpenGraph for Previewing News Article ###

@app.route("/preview", methods=['POST'])
def preview_article():
    """Get OpenGraph Metadata to preview article post"""

    url = request.form.get("url")

    og_data = pyog(url).metadata

    print og_data

    return jsonify(title=og_data['title'], 
                    img=og_data['image'],
                    desc=og_data['description'])

###############################################################################
    ### Display Article Page ###

@app.route("/article/<title>", methods=['GET'])
def display_article(title):
    """Show individual article page.


    If a user is logged in, let them view possible actions.
    Logged in users can also add more category tags to the 
    articles they read.
    """
    print title

    article = Article.query.filter_by(title=title).first()

    user_name = session.get("user_name")

    if user_name:
        user = User.query.filter_by(name=user_name).first()
    else:
        user = None

    return render_template("article.html",
                           user=user,
                           article=article)

@app.route("/article/update_article", methods=['POST'])
def add_tags():
    """User can add more article tags to articles."""

    article_id = request.form.get("article_id")
    print "article_id: ", article_id

    article = Article.query.get(article_id)

    tags = request.form.getlist('tag')
    print "Tags: ", tags

    for tag_name in tags:
        tag = Tag.query.filter_by(tag_name=tag_name).first()
        article.tag_list.append(tag)

    db.session.commit()

    article_address = "/article/" + article.title

    return redirect(article_address)

###############################################################################
    ### API Results Pages ###

@app.route("/meet/<title>", methods=['GET'])
def display_meetups(title):
    """This will display meetup info based on tags associated with this article.
    

    meetup_dict_by_tag keeps the tag object with the generated meetup info,
    this keeps things organized and separate on the results page."""

    article = Article.query.filter_by(title=title).first()

    user = User.query.filter_by(name=session['user_name']).first()

    if user:
        meetup_dict_by_tag = {}
        for tag in article.tag_list:
            meetup_dict_by_tag[tag] = list_events(user.zipcode, tag.meetup_topic)

    for tag, tagged_meetups in meetup_dict_by_tag.items():
        for event in tagged_meetups:
            print type(event['event_url'])
    

    return render_template("meet.html", article=article, meetup_dict=meetup_dict_by_tag)
    

@app.route("/give/<title>", methods=['GET'])
def display_giving_projs(title):
    """This will display list of Global Giving Projects"""

    article = Article.query.filter_by(title=title).first()

    user = User.query.filter_by(name=session['user_name']).first()

    if user:
        giving_dict_by_tag = {}
        for tag in article.tag_list:
            giving_dict_by_tag[tag] = list_giving_projs(tag.gg_code)

    if giving_dict_by_tag:
        for tag, tagged_projs in giving_dict_by_tag.items():  
            for project in tagged_projs:
                print project['projectLink']
                print pyog(project['projectLink']).metadata
    else:
        giving_dict_by_tag["Error"] = "Sorry no results found."

    return render_template("give.html", article=article, giving_projs=giving_dict_by_tag)


    

@app.route("/congress/<zipcode>", methods=["GET"])
def lookup_congress(zipcode):
    """This returns a congress page with a list of 
    contact info for each of the congress members associated 
    with the user's zipcode."""

    congress_list = gen_rep_list(zipcode)
    
    return render_template('congress.html', congress_list=congress_list)

###############################################################################
    ### Tracking Usage Behaviour on the site ###

@app.route('/action', methods=['POST'])
def add_action_to_db():
    """Add tracking info on a user's action to the db"""

    tag_id = request.form.get('tag_id')
    article_id = request.form.get('article_id')
    action_type = request.form.get('action_type')
    print tag_id, article_id, action_type

    user = User.query.filter_by(name=session['user_name']).first()

    new_action = Action(tag_id=int(tag_id),
                        article_id=int(article_id),
                        action_user=user.user_id,
                        action_type=action_type)

    db.session.add(new_action)
    db.session.commit()

    return "Successfully added a new action to db."   


###############################################################################
    ### d3 Jsonifier ###

@app.route("/influences/<name>", methods=["GET"])
def get_influences_json(name):
    """Create JSON tree object for d3 graph.

    Based on user's articles and the actions associated with those articles."""

    user = User.query.filter_by(name=name).first()

    return jsonify(user.influences)

###############################################################################
    ### Heatmap of Actions ###

@app.route("/actionmap")
def show_heatmap():
    """Show heatmap of user actions by zipcode.

    Uses Google Javascript Maps API."""

    return render_template("heatmap.html")

@app.route("/jsonactions", methods=["GET"])
def get_actions_json():
    """Create JSON tree object based all actions on site by zipcode.
    
    """

    return jsonify("/static/js/map.json")


###############################################################################
    ### Antique Map SVG ###

@app.route("/antique")
def show_antique_map():
    """Having fun with an SVG Antique Map of USA"""

    return render_template("antique_map.html")


###############################################################################
    ### Run Server ###

if __name__ == "__main__":
    # Run in debug mode
    app.debug = True
    app.config['TESTING'] = True
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()


