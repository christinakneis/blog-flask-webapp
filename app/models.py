from app import db
from flask_login import UserMixin
from datetime import datetime
from slugify import slugify
from markdown import markdown
import bleach

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_html = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.String(20), default='markdown')  # 'markdown' or 'html'
    preview = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))
    published = db.Column(db.Boolean, default=False)
    featured = db.Column(db.Boolean, default=False)
    show_dates = db.Column(db.Boolean, default=True)  # Control whether dates are displayed
    display_order = db.Column(db.Integer, default=0)  # Custom ordering for posts
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        if self.title and not self.slug:
            self.slug = slugify(self.title)
        if self.content:
            self.content_html = self.convert_content()
    
    def convert_content(self):
        """Convert content to HTML based on content type"""
        if self.content_type == 'html':
            # For HTML posts, just sanitize the content
            allowed_tags = [
                'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'img', 'hr',
                'table', 'thead', 'tbody', 'tr', 'th', 'td', 'div', 'span', 'header',
                'i', 'b', 'small', 'mark', 'del', 'ins', 'sub', 'sup'
            ]
            allowed_attributes = {
                'a': ['href', 'title', 'target'],
                'img': ['src', 'alt', 'title', 'width', 'height', 'style'],
                'div': ['style', 'class'],
                'span': ['style', 'class'],
                'header': ['class'],
                'h1': ['class'],
                'p': ['class']
            }
            
            # Clean HTML content - don't escape HTML entities
            clean_html = bleach.clean(
                self.content, 
                tags=allowed_tags, 
                attributes=allowed_attributes,
                strip=False,
                strip_comments=False
            )
            return clean_html
        else:
            # For markdown posts, convert markdown to HTML
            allowed_tags = [
                'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'img', 'hr',
                'table', 'thead', 'tbody', 'tr', 'th', 'td', 'div', 'span'
            ]
            allowed_attributes = {
                'a': ['href', 'title', 'target'],
                'img': ['src', 'alt', 'title', 'width', 'height', 'style'],
                'div': ['style', 'class'],
                'span': ['style', 'class']
            }
            
            # Convert markdown to HTML
            # md_in_html allows markdown inside HTML blocks (like divs)
            html = markdown(self.content, extensions=['fenced_code', 'tables', 'codehilite', 'md_in_html'])
            
            # Clean the HTML
            clean_html = bleach.clean(
                html, 
                tags=allowed_tags, 
                attributes=allowed_attributes,
                strip=False
            )
            return clean_html
    
    def update_content(self, content):
        """Update content and regenerate HTML"""
        self.content = content
        self.content_html = self.convert_content()
        self.updated_at = datetime.utcnow()

class SiteConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(200))
    
    @classmethod
    def get_config(cls, key, default=None):
        """Get configuration value by key"""
        config = cls.query.filter_by(key=key).first()
        return config.value if config else default
    
    @classmethod
    def set_config(cls, key, value, description=None):
        """Set configuration value by key"""
        config = cls.query.filter_by(key=key).first()
        if config:
            config.value = value
            if description:
                config.description = description
        else:
            config = cls(key=key, value=value, description=description)
            db.session.add(config)
        db.session.commit()
        return config
