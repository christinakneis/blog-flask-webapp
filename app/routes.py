# Define the routes for the web app

from flask import Blueprint, render_template, request, redirect, url_for, abort
from app.models import Post, SiteConfig
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    # Get posts per page from configuration (default: 6)
    posts_per_page = int(SiteConfig.get_config('posts_per_page', '6'))
    
    # Get published posts, ordered by display_order first, then by creation date
    posts = Post.query.filter_by(published=True).order_by(Post.display_order, Post.created_at.desc()).limit(posts_per_page).all()
    
    # Pass posts to the template
    return render_template('index.html', posts=posts)

@main_bp.route("/about")
def about():
    return render_template("about.html")

@main_bp.route("/consulting")
def consulting():
    return render_template("consulting.html")

@main_bp.route("/contact")
def contact():
    return render_template("contact.html")

@main_bp.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")

@main_bp.route("/resume")
def resume():
    return render_template("resume.html")

@main_bp.route("/posts/<slug>")
def post(slug):
    # Find post by slug
    post = Post.query.filter_by(slug=slug, published=True).first()
    
    if post:
        return render_template('post.html', post=post)
    else:
        abort(404)

@main_bp.route("/blog")
def blog():
    # Get all published posts for the blog page
    page = request.args.get('page', 1, type=int)
    per_page = int(SiteConfig.get_config('blog_posts_per_page', '10'))
    
    posts = Post.query.filter_by(published=True).order_by(Post.display_order, Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('blog.html', posts=posts)
