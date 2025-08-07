# Entry point for running the app locally

from app import app

if __name__ == '__main__':
    # Enable debug mode for development
    app.run(debug=True)
