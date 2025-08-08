# Define the routes for the web app

from app import app
from flask import render_template

@app.route('/')
def home():
    #posts 
    posts = [
        {
            "title": "Why Do You Need a Systems Engineer?",
            "date": "",
            "slug": "why-systems-engineering-matters",
            "image": "assets/home/MS_sys.png",
            "preview": "In an age of AI that can build anything, systems engineers contextualize, connect the dots, trace intent, and ensure we’re building the right thing — and that it actually works...."
        },
        {
            "title": "Product Development Engineering in Action: A Demo (for this website!)",
            "date": "",
            "slug": "systems-engineering-in-action",
            "image": "assets/home/FRDP2.png",
            "preview": "From stakeholder needs to deployed infrastructure; a systems engineer’s approach to personal web design..."
        }
    ]   
    # Pass posts to the template
    return render_template('index.html', posts=posts)
    # Render the homepage
    #return render_template('index.html')

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")

@app.route("/posts/<slug>")
def post(slug):
    # Map slugs to templates
    templates = {
        "why-systems-engineering-matters": "posts/whysysengmatters.html",
        "systems-engineering-in-action": "posts/sysengwebsite.html"
    }

    template_name = templates.get(slug)
    if template_name:
        return render_template(template_name)
    else:
        return render_template("404.html"), 404
