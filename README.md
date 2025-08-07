# Christina Kneis Personal Website

This Flask application will serve as the foundation for my personal website hosted on AWS.

## To run the app locally: 
```
# Create and Activate a Virtual Environment
python3 -m venv venv
source venv/bin/activate 

# Install Required Packages
pip install -r requirements.txt

# Run the Flask App
python run.py

# OR run with gunicorn 
gunicorn -w 1 -b 127.0.0.1:5050 run:app
```
