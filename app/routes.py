# Define the routes for the web app

from app import app
from flask import render_template

@app.route('/')
def home():
    # Render the homepage
    return render_template('index.html')
