from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app.models import Post, User, SiteConfig
from app.forms import PostForm, LoginForm, UserForm
from app import db, csrf
from datetime import datetime
import os
import uuid

# Try to import PIL for image optimization (optional)
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

admin_bp = Blueprint('admin', __name__)

# Image upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_folder():
    """Get the upload folder path, creating it if needed"""
    upload_folder = os.path.join(current_app.root_path, 'static', 'assets', 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder

def generate_unique_filename(filename):
    """Generate a unique filename while preserving the extension"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'png'
    unique_name = f"{uuid.uuid4().hex[:12]}_{secure_filename(filename)}"
    return unique_name

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

@admin_bp.route('/posts/<int:id>/preview')
@login_required
def preview_post(id):
    """Preview any post (published or draft) as admin"""
    post = Post.query.get_or_404(id)
    return render_template('post.html', post=post, is_preview=True)

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
        # Determine publish status from button clicked
        action = request.form.get('action', 'draft')
        is_published = (action == 'publish')

        post = Post(
            title=form.title.data,
            content=form.content.data,
            content_type=form.content_type.data,
            preview=form.preview.data,
            image=form.image.data,
            published=is_published,
            featured=form.featured.data,
            show_dates=form.show_dates.data,
            display_order=form.display_order.data or 0
        )
        db.session.add(post)
        db.session.commit()

        if is_published:
            flash('Post published!', 'success')
        else:
            flash('Draft saved!', 'success')
        return redirect(url_for('admin.posts'))

    return render_template('admin/post_form.html', form=form, title='New Post')

@admin_bp.route('/posts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    form = PostForm(obj=post)

    if form.validate_on_submit():
        # Determine publish status from button clicked
        action = request.form.get('action', 'draft')
        is_published = (action == 'publish')

        post.title = form.title.data
        post.content = form.content.data
        post.content_type = form.content_type.data
        post.preview = form.preview.data
        post.image = form.image.data
        post.published = is_published
        post.featured = form.featured.data
        post.show_dates = form.show_dates.data
        post.display_order = form.display_order.data or 0
        post.update_content(form.content.data)

        db.session.commit()

        if is_published:
            flash('Post published!', 'success')
        else:
            flash('Draft saved!', 'success')
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

    # Return JSON for AJAX requests
    if request.headers.get('Content-Type') == 'application/json' or request.is_json:
        return jsonify({
            'success': True,
            'published': post.published,
            'status': status
        })

    # Regular form submission - redirect
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

@admin_bp.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    """Handle image uploads for blog posts"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image file provided'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning

    if size > MAX_IMAGE_SIZE:
        return jsonify({'success': False, 'error': 'File too large. Maximum size is 10MB'}), 400

    try:
        upload_folder = get_upload_folder()
        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)

        # Save the file
        file.save(filepath)

        # Optimize image if PIL is available and it's not SVG
        if HAS_PIL and not filename.lower().endswith('.svg'):
            try:
                with Image.open(filepath) as img:
                    # Convert to RGB if necessary (for PNG with transparency, keep RGBA)
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        pass  # Keep transparency
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')

                    # Resize if too large (max 1920px width)
                    max_width = 1920
                    if img.width > max_width:
                        ratio = max_width / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                    # Save optimized
                    if filename.lower().endswith(('.jpg', '.jpeg')):
                        img.save(filepath, 'JPEG', quality=85, optimize=True)
                    elif filename.lower().endswith('.png'):
                        img.save(filepath, 'PNG', optimize=True)
                    elif filename.lower().endswith('.webp'):
                        img.save(filepath, 'WEBP', quality=85)
            except Exception as e:
                print(f"Image optimization failed: {e}")
                # Continue with original file if optimization fails

        # Return both the URL path (for preview) and the storage path (for database)
        # url is the full path for displaying in browser
        # storage_path is relative to static folder (for use with url_for('static', filename=...))
        url = f'/static/assets/uploads/{filename}'
        storage_path = f'assets/uploads/{filename}'

        return jsonify({
            'success': True,
            'url': url,
            'storage_path': storage_path,
            'filename': filename,
            'message': 'Image uploaded successfully'
        })

    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/images')
@login_required
def image_gallery():
    """Get list of all uploaded images for the gallery"""
    images = []

    # Scan upload folder
    upload_folder = get_upload_folder()
    if os.path.exists(upload_folder):
        for filename in os.listdir(upload_folder):
            if allowed_file(filename):
                filepath = os.path.join(upload_folder, filename)
                stat = os.stat(filepath)
                images.append({
                    'filename': filename,
                    'url': f'/static/assets/uploads/{filename}',
                    'storage_path': f'assets/uploads/{filename}',
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })

    # Also scan other asset folders
    asset_folders = ['home', 'sysengwebsite', 'lfl', 'devops']
    for folder in asset_folders:
        folder_path = os.path.join(current_app.root_path, 'static', 'assets', folder)
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if allowed_file(filename):
                    filepath = os.path.join(folder_path, filename)
                    stat = os.stat(filepath)
                    images.append({
                        'filename': filename,
                        'url': f'/static/assets/{folder}/{filename}',
                        'storage_path': f'assets/{folder}/{filename}',
                        'folder': folder,
                        'size': stat.st_size,
                        'modified': stat.st_mtime
                    })

    # Sort by modification time (newest first)
    images.sort(key=lambda x: x['modified'], reverse=True)

    return jsonify({'success': True, 'images': images})


@admin_bp.route('/delete-image', methods=['POST'])
@login_required
def delete_image():
    """Delete an uploaded image"""
    data = request.get_json()
    if not data or 'filename' not in data:
        return jsonify({'success': False, 'error': 'No filename provided'}), 400

    filename = secure_filename(data['filename'])
    upload_folder = get_upload_folder()
    filepath = os.path.join(upload_folder, filename)

    # Only allow deleting from uploads folder for safety
    if os.path.exists(filepath) and os.path.dirname(filepath) == upload_folder:
        try:
            os.remove(filepath)
            return jsonify({'success': True, 'message': 'Image deleted'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({'success': False, 'error': 'Image not found or cannot be deleted'}), 404


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
