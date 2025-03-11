from flask import Flask
from utils.frontend.file_helpers import ensure_directories
from utils.frontend.html_helper import create_templates
from utils.frontend.css_helper import create_css
from utils.frontend.js_helper import create_js

# Configuration class
class Config:
    """Configuration settings for the Flask application"""
    # Flask settings
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    
    # API settings
    DEFAULT_API_LIMIT = 50
    DEFAULT_API_OFFSET = 0
    
    # Default model settings
    DEFAULT_LLM_MODEL = "deepseek-chat"

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Import routes after the app is created to avoid circular imports
from utils.routes import register_routes

def init_app():
    """Initialize the application"""
    # Ensure necessary directories and files exist
    ensure_directories()
    create_templates()
    create_css()
    create_js()
    
    # Register routes
    register_routes(app)
    
    return app

if __name__ == "__main__":
    app = init_app()
    print("Schedule visualization app initialized!")
    print("Running at http://127.0.0.1:5000")
    app.run(debug=app.config['DEBUG']) 