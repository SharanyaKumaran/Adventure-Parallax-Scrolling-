import os
import logging
from app import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create Flask app
app = create_app()

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join('app', 'static', 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )