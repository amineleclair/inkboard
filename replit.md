# InkBoard - Neural Story Generator

## Overview

InkBoard is a web application that transforms scene ideas into vivid stories and beautiful images using Cohere's language models and Hugging Face's image generation capabilities. Features user authentication, purple/neon pixelated theme, and a complete dashboard with story creation, gallery, and journal functionality.

## User Preferences

- Preferred communication style: Simple, everyday language
- Theme: Purple/neon pixelated aesthetic with cyberpunk elements
- Authentication: User accounts with login/registration system
- Database: PostgreSQL for persistent user data storage

## System Architecture

### Frontend Architecture
- **Technology**: Pure HTML, CSS, and JavaScript with Bootstrap 5 for styling
- **Structure**: Single-page application with modal-based interactions
- **UI Framework**: Bootstrap 5 for responsive design and components
- **Icons**: Font Awesome for iconography
- **Fonts**: Google Fonts (Poppins and Inter) for typography

### Backend Architecture
- **Framework**: Flask (Python web framework) with Flask-SQLAlchemy
- **Database**: PostgreSQL for persistent data storage
- **Authentication**: Flask-Login for user session management
- **API**: RESTful endpoints for content generation and user management
- **Password Security**: Werkzeug password hashing
- **Logging**: Python logging module for debugging

### Key Design Decisions
- **Authentication**: Full user account system with secure password hashing
- **Theme**: Purple/neon pixelated cyberpunk aesthetic with animated elements
- **Cohere Integration**: Direct API calls to Cohere for text generation
- **Hugging Face Integration**: Image generation with SVG fallback system
- **Database-driven**: PostgreSQL for persistent user data and creations
- **Responsive Design**: Mobile-friendly interface with Bootstrap 5

## Key Components

### Backend Components
1. **app.py**: Main Flask application with authentication, database, and API integration
2. **models.py**: SQLAlchemy models for User and Creation entities
3. **main.py**: Application entry point for Gunicorn deployment
4. **Routes**:
   - `/`: Landing page (unauthenticated) or dashboard (authenticated)
   - `/login`: User authentication endpoint
   - `/register`: User registration endpoint
   - `/logout`: User logout endpoint
   - `/generate`: POST endpoint for story and image generation (protected)
   - `/save_journal`: POST endpoint for saving journal entries (protected)
   - `/get_creations`: GET endpoint for retrieving user creations (protected)

### Frontend Components
1. **templates/index.html**: Landing page with cyberpunk theme and feature showcase
2. **templates/login.html**: User login page with neon animations
3. **templates/register.html**: User registration page with pixelated styling
4. **templates/dashboard.html**: Main application dashboard with navigation
5. **static/css/style.css**: Purple/neon pixelated theme with CSS animations
6. **static/js/script.js**: JavaScript class handling user interactions and API calls

### Core Features
- **User Authentication**: Secure login/registration system
- **Scene-to-Story Generation**: Transform scene ideas into vivid stories using Cohere
- **AI Image Generation**: Create images using Hugging Face API with SVG fallback
- **Personal Gallery**: View all created stories and images in Pinterest-style layout
- **Digital Journal**: Add personal notes and thoughts to creations
- **Responsive Dashboard**: Clean navigation between Create, Gallery, and Journal sections

## Data Flow

1. User registers/logs in through authentication system
2. Authenticated user accesses dashboard with three main sections
3. In Create section: User enters scene description
4. JavaScript sends POST request to `/generate` endpoint (login required)
5. Flask backend processes request and calls Cohere API for text generation
6. Cohere generates expanded story (80-150 words) from scene description
7. Flask backend calls Hugging Face API for image generation (with SVG fallback)
8. Generated content is saved to PostgreSQL database linked to user account
9. Frontend displays generated story and image with journal options
10. User can view all creations in Gallery section and add journal entries

## External Dependencies

### Backend Dependencies
- **Flask**: Web framework for Python
- **Flask-SQLAlchemy**: ORM for database operations
- **Flask-Login**: User session management
- **Werkzeug**: Password hashing and security utilities
- **Cohere**: Text generation using Cohere's language models
- **Hugging Face**: Image generation using Stable Diffusion models
- **PostgreSQL**: Database for persistent data storage
- **psycopg2-binary**: PostgreSQL adapter for Python
- **Requests**: HTTP library for API calls
- **Python Standard Library**: logging, os, uuid, datetime modules

### Frontend Dependencies
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome**: Icon library
- **Google Fonts**: Typography (Poppins and Inter fonts)

### Environment Variables
- `COHERE_API_KEY`: Required for Cohere API access (text generation)
- `HUGGINGFACE_API_KEY`: Required for Hugging Face API access (image generation)
- `SESSION_SECRET`: Flask session encryption key (required for security)
- `DATABASE_URL`: PostgreSQL database connection string
- Additional PostgreSQL variables: `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`

### How to Add API Keys
API keys are stored as environment variables in Replit Secrets:
1. Go to the Secrets tab in your Replit project (lock icon in sidebar)
2. Click "New Secret"
3. Add key name (e.g., `COHERE_API_KEY`) and paste your API key value
4. The keys will be automatically available to your Flask app

## Deployment Strategy

### Development Environment
- **Server**: Flask development server on port 5000
- **Host**: 0.0.0.0 for accessibility
- **Debug Mode**: Enabled for development

### Production Considerations
- Environment variables must be properly configured
- Session secret should be set for security
- OpenAI API key is required for functionality
- Static file serving handled by Flask (suitable for small-scale deployment)

### File Structure
```
/
├── app.py              # Main Flask application with authentication
├── models.py           # SQLAlchemy database models
├── main.py             # Gunicorn deployment entry point
├── templates/
│   ├── index.html      # Landing page
│   ├── login.html      # User login page
│   ├── register.html   # User registration page
│   └── dashboard.html  # Main application dashboard
└── static/
    ├── css/
    │   └── style.css   # Purple/neon pixelated theme
    └── js/
        └── script.js   # Frontend JavaScript
```

## Notes

- **Authentication System**: Full user account system with secure password hashing
- **Theme**: Purple/neon pixelated cyberpunk aesthetic with CSS animations
- **Database**: PostgreSQL for persistent storage of user accounts and creations
- **API Integration**: Cohere for text generation, Hugging Face for image generation
- **Fallback System**: SVG placeholder images when Hugging Face API is unavailable
- **Responsive Design**: Mobile-friendly interface with Bootstrap 5
- **Generated stories**: Constrained to 80-150 words for optimal readability
- **Security**: Login required for all story generation and data access