from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import Post, User, SiteConfig
from app.forms import PostForm, LoginForm, UserForm
from app import db, csrf
from datetime import datetime
import os

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html', form=form)

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    total_posts = Post.query.count()
    published_posts = Post.query.filter_by(published=True).count()
    draft_posts = Post.query.filter_by(published=False).count()
    
    # Get recent posts
    recent_posts = Post.query.order_by(Post.updated_at.desc()).limit(5).all()
    
    # Get site configuration
    posts_per_page = SiteConfig.get_config('posts_per_page', '6')
    blog_posts_per_page = SiteConfig.get_config('blog_posts_per_page', '10')
    
    return render_template('admin/dashboard.html', 
                         total_posts=total_posts,
                         published_posts=published_posts,
                         draft_posts=draft_posts,
                         recent_posts=recent_posts,
                         posts_per_page=posts_per_page,
                         blog_posts_per_page=blog_posts_per_page)

@admin_bp.route('/posts')
@login_required
def posts():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.display_order, Post.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/posts.html', posts=posts)

@admin_bp.route('/posts/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            content_type=form.content_type.data,
            preview=form.preview.data,
            image=form.image.data,
            published=form.published.data,
            featured=form.featured.data,
            show_dates=form.show_dates.data,
            display_order=form.display_order.data or 0
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!', 'success')
        return redirect(url_for('admin.posts'))
    
    return render_template('admin/post_form.html', form=form, title='New Post')

@admin_bp.route('/posts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    form = PostForm(obj=post)
    
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.content_type = form.content_type.data
        post.preview = form.preview.data
        post.image = form.image.data
        post.published = form.published.data
        post.featured = form.featured.data
        post.show_dates = form.show_dates.data
        post.display_order = form.display_order.data or 0
        post.update_content(form.content.data)
        
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin.posts'))
    
    return render_template('admin/post_form.html', form=form, post=post, title='Edit Post')

@admin_bp.route('/posts/<int:id>/delete', methods=['POST'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin.posts'))

@admin_bp.route('/posts/<int:id>/toggle-publish', methods=['POST'])
@login_required
def toggle_publish(id):
    post = Post.query.get_or_404(id)
    post.published = not post.published
    db.session.commit()
    
    status = 'published' if post.published else 'unpublished'
    flash(f'Post {status} successfully!', 'success')
    return redirect(url_for('admin.posts'))

@admin_bp.route('/posts/reorder', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def reorder_posts():
    """Reorder posts with drag and drop interface"""
    if request.method == 'POST':
        # Handle AJAX reorder request
        try:
            print(f"Request method: {request.method}")
            print(f"Request headers: {dict(request.headers)}")
            print(f"Request content type: {request.content_type}")
            print(f"Request data: {request.get_data()}")
            
            if not request.is_json:
                print("Request is not JSON")
                return jsonify({'success': False, 'message': 'Request must be JSON'}), 400
            
            data = request.get_json()
            print(f"Parsed JSON data: {data}")
            
            if not data:
                print("No data received")
                return jsonify({'success': False, 'message': 'No data received'}), 400
            
            if 'posts' not in data:
                print("No 'posts' key in data")
                return jsonify({'success': False, 'message': 'Missing "posts" key in data'}), 400
            
            if not isinstance(data['posts'], list):
                print(f"'posts' is not a list: {type(data['posts'])}")
                return jsonify({'success': False, 'message': '"posts" must be a list'}), 400
            
            print(f"Processing {len(data['posts'])} posts...")
            
            for i, item in enumerate(data['posts']):
                print(f"Processing item {i}: {item}")
                
                if not isinstance(item, dict):
                    print(f"Item {i} is not a dictionary: {type(item)}")
                    continue
                
                post_id = item.get('id')
                new_order = item.get('order')
                
                print(f"Item {i} - post_id: {post_id} (type: {type(post_id)}), new_order: {new_order} (type: {type(new_order)})")
                
                if post_id is None or new_order is None:
                    print(f"Invalid item data: {item}")
                    continue
                
                # Convert post_id to int if it's a string
                try:
                    post_id = int(post_id)
                except (ValueError, TypeError):
                    print(f"Invalid post_id: {post_id}")
                    continue
                
                # Convert new_order to int if it's a string
                try:
                    new_order = int(new_order)
                except (ValueError, TypeError):
                    print(f"Invalid new_order: {new_order}")
                    continue
                
                post = Post.query.get(post_id)
                if post:
                    print(f"Updating post {post.title} (ID: {post_id}) to order {new_order}")
                    post.display_order = new_order
                else:
                    print(f"Post with ID {post_id} not found")
                    return jsonify({'success': False, 'message': f'Post with ID {post_id} not found'}), 400
            
            db.session.commit()
            print("Database commit successful")
            return jsonify({'success': True, 'message': 'Posts reordered successfully'})
            
        except Exception as e:
            print(f"Error during reorder: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500
    
    # GET request - show reorder interface
    posts = Post.query.filter_by(published=True).order_by(Post.display_order, Post.created_at.desc()).all()
    return render_template('admin/reorder_posts.html', posts=posts)

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        posts_per_page = request.form.get('posts_per_page', '6')
        blog_posts_per_page = request.form.get('blog_posts_per_page', '10')
        
        SiteConfig.set_config('posts_per_page', posts_per_page, 'Number of posts to show on homepage')
        SiteConfig.set_config('blog_posts_per_page', blog_posts_per_page, 'Number of posts to show per page on blog')
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin.settings'))
    
    posts_per_page = SiteConfig.get_config('posts_per_page', '6')
    blog_posts_per_page = SiteConfig.get_config('blog_posts_per_page', '10')
    
    return render_template('admin/settings.html', 
                         posts_per_page=posts_per_page,
                         blog_posts_per_page=blog_posts_per_page)

@admin_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    # Check if admin user already exists
    if User.query.filter_by(is_admin=True).first():
        flash('Admin user already exists!', 'error')
        return redirect(url_for('admin.login'))
    
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            is_admin=True
        )
        db.session.add(user)
        db.session.commit()
        
        # Set default site configuration
        SiteConfig.set_config('posts_per_page', '6', 'Number of posts to show on homepage')
        SiteConfig.set_config('blog_posts_per_page', '10', 'Number of posts to show per page on blog')
        
        flash('Admin user created successfully! You can now log in.', 'success')
        return redirect(url_for('admin.login'))
    
    return render_template('admin/setup.html', form=form)
