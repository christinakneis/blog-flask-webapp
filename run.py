#!/usr/bin/env python3
"""
Main entry point for the Flask blog application.
Run this file to start the development server.
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
