from flask import Flask
from app.api.routes import api_bp

def create_app():
    app = Flask(__name__, static_folder='../static', template_folder='../static')
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload
    
    app.register_blueprint(api_bp)
    
    @app.route('/')
    def index():
        return app.send_static_file('index.html')
        
    return app