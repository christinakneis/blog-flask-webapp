#!/usr/bin/env python3
"""
Migration script to transfer existing hardcoded posts to the new CMS database.
Run this after setting up the admin user and before creating new posts.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Post, User

def migrate_posts():
    """Migrate existing hardcoded posts to the database"""
    app = create_app()
    
    with app.app_context():
        # Check if admin user exists
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            print("❌ No admin user found. Please run the setup first at /admin/setup")
            return False
        
        # Check if posts already exist
        existing_posts = Post.query.count()
        if existing_posts > 0:
            print(f"⚠️  {existing_posts} posts already exist in database. Skipping migration.")
            return True
        
        # Define the existing posts
        existing_posts_data = [
            {
                "title": "Why Do You Need a Systems Engineer?",
                "content": """# Why Do You Need a Systems Engineer?

In an age of AI that can build anything, systems engineers contextualize, connect the dots, trace intent, and ensure we're building the right thing — and that it actually works.

## The Role of Systems Engineering

Systems engineering is more than just technical expertise; it's about understanding the bigger picture. When AI can generate code, design components, and even create entire systems, the human element becomes even more critical.

### Key Responsibilities

- **Contextualization**: Understanding the broader environment and constraints
- **Connection**: Linking different components and subsystems
- **Intent Tracing**: Ensuring the solution aligns with stakeholder needs
- **Validation**: Verifying that the system actually works as intended

## Why It Matters

In complex projects, especially in aerospace and infrastructure, the cost of failure is enormous. Systems engineers provide the oversight and coordination needed to prevent catastrophic failures and ensure project success.

## Conclusion

While AI can build components, systems engineers ensure we're building the right system, in the right way, for the right reasons.""",
                "preview": "In an age of AI that can build anything, systems engineers contextualize, connect the dots, trace intent, and ensure we're building the right thing — and that it actually works.",
                "image": "assets/home/MS_sys.png",
                "published": True,
                "featured": True
            },
            {
                "title": "Product Development Engineering in Action: A Demo (for this website!)",
                "content": """# Product Development Engineering in Action: A Demo

From stakeholder needs to deployed infrastructure; a systems engineer's approach to personal web design.

## The Engineering Process

### 1. Requirements Analysis
- **Stakeholder Needs**: Personal branding and professional presence
- **Functional Requirements**: Blog, portfolio, contact information
- **Non-Functional Requirements**: Performance, security, maintainability

### 2. System Architecture
- **Frontend**: Responsive design with modern UI/UX
- **Backend**: Flask-based CMS for easy content management
- **Infrastructure**: Terraform-managed cloud deployment

### 3. Implementation
- **Development**: Iterative development with continuous feedback
- **Testing**: User acceptance testing and performance validation
- **Deployment**: Automated deployment pipeline

## Key Engineering Principles Applied

- **Modularity**: Separate concerns between frontend, backend, and infrastructure
- **Scalability**: Design for future growth and content expansion
- **Maintainability**: Clean code and documentation
- **User Experience**: Intuitive interface and responsive design

## Results

A professional website that demonstrates engineering principles while serving practical needs. The system is maintainable, scalable, and provides an excellent user experience.""",
                "preview": "From stakeholder needs to deployed infrastructure; a systems engineer's approach to personal web design.",
                "image": "assets/home/FRDP2.png",
                "published": True,
                "featured": False
            }
        ]
        
        # Create posts
        created_count = 0
        for post_data in existing_posts_data:
            try:
                post = Post(**post_data)
                db.session.add(post)
                created_count += 1
                print(f"✅ Created post: {post.title}")
            except Exception as e:
                print(f"❌ Error creating post '{post_data['title']}': {e}")
                db.session.rollback()
                return False
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n🎉 Successfully migrated {created_count} posts to the CMS!")
            print("You can now manage these posts through the admin panel at /admin")
            return True
        except Exception as e:
            print(f"❌ Error committing changes: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🚀 Starting post migration...")
    success = migrate_posts()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
