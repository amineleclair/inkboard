import os
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import cohere
import requests
import uuid
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_dev")

# Database configuration
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    # Fallback for development
    database_url = "sqlite:///inkboard.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize database
db = SQLAlchemy(app, model_class=Base)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access InkBoard'

# Initialize Cohere client for text generation
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
if not COHERE_API_KEY:
    logging.error("COHERE_API_KEY environment variable not set")
    cohere_client = None
else:
    cohere_client = cohere.Client(COHERE_API_KEY)

# Initialize Hugging Face for image generation
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")
HF_IMAGE_MODEL = "stabilityai/stable-diffusion-2-1"  # Popular image generation model

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """Main page - redirect to login if not authenticated"""
    if current_user.is_authenticated:
        return render_template('dashboard.html', user=current_user)
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '').strip()
            
            if not username or not email or not password:
                return jsonify({'error': 'All fields are required'}), 400
            
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                return jsonify({'error': 'Username already exists'}), 400
            
            if User.query.filter_by(email=email).first():
                return jsonify({'error': 'Email already exists'}), 400
            
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Log in the user
            login_user(user)
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('index')})
            else:
                flash('Registration successful! Welcome to InkBoard!', 'success')
                return redirect(url_for('index'))
                
        except Exception as e:
            logging.error(f"Registration error: {str(e)}")
            if request.is_json:
                return jsonify({'error': 'Registration failed'}), 500
            else:
                flash('Registration failed. Please try again.', 'error')
                return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            
            if not username or not password:
                return jsonify({'error': 'Username and password are required'}), 400
            
            # Find user by username or email
            user = User.query.filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if user and user.check_password(password):
                login_user(user)
                if request.is_json:
                    return jsonify({'success': True, 'redirect': url_for('index')})
                else:
                    flash('Welcome back to InkBoard!', 'success')
                    return redirect(url_for('index'))
            else:
                if request.is_json:
                    return jsonify({'error': 'Invalid username or password'}), 401
                else:
                    flash('Invalid username or password', 'error')
                    return render_template('login.html')
                    
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            if request.is_json:
                return jsonify({'error': 'Login failed'}), 500
            else:
                flash('Login failed. Please try again.', 'error')
                return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/generate', methods=['POST'])
@login_required
def generate_content():
    """Generate story and image from scene description using Cohere and Hugging Face"""
    try:
        data = request.get_json()
        scene_idea = data.get('scene_idea', '').strip()
        
        if not scene_idea:
            return jsonify({'error': 'Please provide a scene idea'}), 400
        
        if not cohere_client:
            return jsonify({'error': 'Cohere API key not configured'}), 500
        
        # Generate expanded story using Cohere
        story_prompt = f"""Transform this scene idea into a vivid, descriptive paragraph that paints a beautiful picture with words. Keep it between 80-150 words, rich in sensory details and atmosphere:

Scene idea: {scene_idea}

Write a single, flowing paragraph that brings this scene to life with beautiful imagery and emotions."""
        
        logging.debug(f"Generating story for scene: {scene_idea}")
        
        # Use Cohere's generate endpoint for text generation
        story_response = cohere_client.generate(
            model='command',  # Cohere's flagship model
            prompt=story_prompt,
            max_tokens=200,  # Limit to keep response concise (80-150 words)
            temperature=0.7,
            k=0,
            stop_sequences=[],
            return_likelihoods='NONE'
        )
        
        expanded_story = story_response.generations[0].text.strip()
        logging.debug(f"Generated story: {expanded_story[:100]}...")
        
        # Generate image using Hugging Face API
        image_url = None
        if HUGGINGFACE_API_KEY:
            try:
                image_url = generate_image_hf(scene_idea, expanded_story)
                logging.debug(f"Generated image URL: {image_url}")
            except Exception as img_error:
                logging.warning(f"Image generation failed: {str(img_error)}")
                # Continue without image - story generation is primary feature
        
        # Save to database instead of session
        creation_id = str(uuid.uuid4())
        creation = Creation(
            id=creation_id,
            user_id=current_user.id,
            scene_idea=scene_idea,
            story=expanded_story,
            image_url=image_url
        )
        
        db.session.add(creation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'story': expanded_story,
            'image_url': image_url,
            'creation_id': creation_id
        })
        
    except Exception as e:
        logging.error(f"Error generating content: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

def generate_image_hf(scene_idea, story):
    """Generate image using Hugging Face API or create a beautiful SVG placeholder"""
    try:
        # First try Hugging Face API
        if HUGGINGFACE_API_KEY:
            image_prompt = f"A beautiful artistic illustration of: {scene_idea}. Style: dreamy, soft colors, high quality digital art, atmospheric"
            
            # Try multiple models in case one fails
            models_to_try = [
                "runwayml/stable-diffusion-v1-5",
                "stabilityai/stable-diffusion-2-1",
                "CompVis/stable-diffusion-v1-4"
            ]
            
            for model in models_to_try:
                try:
                    api_url = f"https://api-inference.huggingface.co/models/{model}"
                    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
                    
                    # Send request to Hugging Face
                    response = requests.post(
                        api_url,
                        headers=headers,
                        json={"inputs": image_prompt},
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        # Save the image temporarily and return a placeholder URL
                        # In a real app, you'd upload to cloud storage
                        import base64
                        image_data = response.content
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                        logging.debug(f"Successfully generated image with model: {model}")
                        return f"data:image/png;base64,{image_base64}"
                    else:
                        logging.warning(f"Model {model} failed: {response.status_code} - {response.text}")
                        continue
                        
                except Exception as model_error:
                    logging.warning(f"Model {model} error: {str(model_error)}")
                    continue
            
            logging.warning("All Hugging Face models failed, falling back to SVG placeholder")
        
        # Create a beautiful SVG placeholder based on scene description
        return generate_svg_placeholder(scene_idea, story)
            
    except Exception as e:
        logging.error(f"Error generating image: {str(e)}")
        return generate_svg_placeholder(scene_idea, story)

def generate_svg_placeholder(scene_idea, story):
    """Generate a beautiful SVG placeholder image based on the scene"""
    try:
        # Create a color palette based on keywords in the scene
        colors = get_scene_colors(scene_idea.lower())
        
        # Create SVG with gradient background and artistic elements
        svg_content = f"""
        <svg width="400" height="400" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:{colors['primary']};stop-opacity:1" />
                    <stop offset="100%" style="stop-color:{colors['secondary']};stop-opacity:1" />
                </linearGradient>
                <radialGradient id="glow" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" style="stop-color:white;stop-opacity:0.3" />
                    <stop offset="100%" style="stop-color:white;stop-opacity:0" />
                </radialGradient>
            </defs>
            
            <!-- Background -->
            <rect width="400" height="400" fill="url(#bg)" />
            
            <!-- Artistic elements based on scene -->
            {get_scene_elements(scene_idea.lower(), colors)}
            
            <!-- Glow effect -->
            <rect width="400" height="400" fill="url(#glow)" />
            
            <!-- Scene text -->
            <text x="200" y="350" font-family="Arial, sans-serif" font-size="14" fill="white" text-anchor="middle" opacity="0.8">
                {scene_idea[:40]}{"..." if len(scene_idea) > 40 else ""}
            </text>
        </svg>
        """
        
        # Convert SVG to base64 data URL
        import base64
        svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{svg_base64}"
        
    except Exception as e:
        logging.error(f"Error generating SVG placeholder: {str(e)}")
        return None

def get_scene_colors(scene_text):
    """Get color palette based on scene description"""
    # Default colors
    colors = {
        'primary': '#4fd1c7',
        'secondary': '#88d8f7',
        'accent': '#a8e6cf'
    }
    
    # Adjust colors based on keywords
    if any(word in scene_text for word in ['sunset', 'dawn', 'orange', 'red']):
        colors = {'primary': '#ff6b6b', 'secondary': '#ffa726', 'accent': '#ffcc80'}
    elif any(word in scene_text for word in ['night', 'dark', 'moon', 'stars']):
        colors = {'primary': '#3f51b5', 'secondary': '#1a237e', 'accent': '#7986cb'}
    elif any(word in scene_text for word in ['forest', 'green', 'nature', 'tree']):
        colors = {'primary': '#4caf50', 'secondary': '#2e7d32', 'accent': '#a5d6a7'}
    elif any(word in scene_text for word in ['ocean', 'sea', 'water', 'blue']):
        colors = {'primary': '#2196f3', 'secondary': '#0d47a1', 'accent': '#90caf9'}
    elif any(word in scene_text for word in ['fire', 'flame', 'hot', 'warm']):
        colors = {'primary': '#f44336', 'secondary': '#d32f2f', 'accent': '#ffab91'}
    
    return colors

def get_scene_elements(scene_text, colors):
    """Generate SVG elements based on scene description"""
    elements = []
    
    # Add different shapes and elements based on keywords
    if any(word in scene_text for word in ['mountain', 'cliff', 'hill']):
        elements.append(f'<polygon points="0,400 150,200 300,250 400,400" fill="{colors["accent"]}" opacity="0.7" />')
        elements.append(f'<polygon points="100,400 250,150 400,200 400,400" fill="{colors["primary"]}" opacity="0.6" />')
    
    if any(word in scene_text for word in ['sun', 'sunset', 'sunrise']):
        elements.append(f'<circle cx="300" cy="100" r="40" fill="#ffeb3b" opacity="0.8" />')
        elements.append(f'<circle cx="300" cy="100" r="60" fill="#fff59d" opacity="0.3" />')
    
    if any(word in scene_text for word in ['moon', 'night']):
        elements.append(f'<circle cx="320" cy="80" r="30" fill="#f5f5f5" opacity="0.9" />')
        elements.append(f'<circle cx="100" cy="150" r="2" fill="white" opacity="0.8" />')
        elements.append(f'<circle cx="150" cy="120" r="1.5" fill="white" opacity="0.7" />')
        elements.append(f'<circle cx="200" cy="100" r="1" fill="white" opacity="0.6" />')
    
    if any(word in scene_text for word in ['tree', 'forest']):
        elements.append(f'<ellipse cx="80" cy="300" rx="15" ry="60" fill="{colors["accent"]}" opacity="0.8" />')
        elements.append(f'<ellipse cx="120" cy="280" rx="20" ry="70" fill="{colors["primary"]}" opacity="0.7" />')
    
    if any(word in scene_text for word in ['water', 'ocean', 'lake']):
        elements.append(f'<ellipse cx="200" cy="350" rx="150" ry="30" fill="{colors["secondary"]}" opacity="0.6" />')
        elements.append(f'<ellipse cx="200" cy="360" rx="180" ry="25" fill="{colors["primary"]}" opacity="0.4" />')
    
    # Add some abstract artistic elements
    elements.append(f'<circle cx="50" cy="80" r="8" fill="white" opacity="0.3" />')
    elements.append(f'<circle cx="350" cy="300" r="12" fill="white" opacity="0.2" />')
    elements.append(f'<circle cx="300" cy="250" r="6" fill="white" opacity="0.4" />')
    
    return '\n'.join(elements)

@app.route('/save_journal', methods=['POST'])
@login_required
def save_journal():
    """Save journal entry for a creation"""
    try:
        data = request.get_json()
        creation_id = data.get('creation_id')
        journal_entry = data.get('journal_entry', '').strip()
        
        if not creation_id:
            return jsonify({'error': 'Creation ID required'}), 400
        
        # Find the creation in database
        creation = Creation.query.filter_by(
            id=creation_id, 
            user_id=current_user.id
        ).first()
        
        if not creation:
            return jsonify({'error': 'Creation not found'}), 404
        
        creation.journal_entry = journal_entry
        creation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Error saving journal: {str(e)}")
        return jsonify({'error': 'Failed to save journal entry'}), 500

@app.route('/get_creations')
@login_required
def get_creations():
    """Get all user creations"""
    try:
        creations = Creation.query.filter_by(user_id=current_user.id).order_by(Creation.created_at.desc()).all()
        
        creations_data = []
        for creation in creations:
            creations_data.append({
                'id': creation.id,
                'scene_idea': creation.scene_idea,
                'story': creation.story,
                'image_url': creation.image_url,
                'journal_entry': creation.journal_entry,
                'created_at': creation.created_at.isoformat()
            })
        
        return jsonify({'creations': creations_data})
        
    except Exception as e:
        logging.error(f"Error getting creations: {str(e)}")
        return jsonify({'error': 'Failed to get creations'}), 500

# Import models after app and db are defined
from models import User, Creation

# Create database tables
with app.app_context():
    db.create_all()
    logging.info("Database tables created")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
