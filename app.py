#!/usr/bin/env python3
"""
My Beauty AI - Main Application Entry Point

This is an example Flask application demonstrating how to use
the My Beauty AI core components together.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Import our core components
from config import get_config, validate_config
from models import Base
from rag_system import create_rag_system
from conflict_analyzer import create_conflict_analyzer
from routine_optimizer import create_routine_optimizer

# Initialize Flask app
app = Flask(__name__)

# Load and validate configuration
try:
    config = get_config()
    validate_config()
    print("✅ Configuration loaded and validated")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    exit(1)

# Configure Flask
app.config['SECRET_KEY'] = config.security.secret_key
app.config['DEBUG'] = config.app.debug

# Enable CORS
CORS(app, origins=config.security.cors_origins)

# Initialize database
engine = create_engine(config.database.connection_string)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables (in production, use migrations)
if config.app.environment == 'development':
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

# Initialize core systems
rag_system = None
conflict_analyzer = None
routine_optimizer = None

try:
    # Initialize RAG system
    rag_system = create_rag_system()
    print("✅ RAG system initialized")

    # Initialize conflict analyzer
    db_session = SessionLocal()
    conflict_analyzer = create_conflict_analyzer(db_session, rag_system)
    print("✅ Conflict analyzer initialized")

    # Initialize routine optimizer  
    routine_optimizer = create_routine_optimizer(db_session, conflict_analyzer, rag_system)
    print("✅ Routine optimizer initialized")

except Exception as e:
    print(f"⚠️ Warning: Some systems could not be initialized: {e}")
    print("The app will still run but with limited functionality")


@app.route('/')
def home():
    """Home endpoint with system status."""
    return jsonify({
        'message': 'Welcome to My Beauty AI API',
        'version': config.app.version,
        'status': 'running',
        'systems': {
            'rag_system': rag_system is not None,
            'conflict_analyzer': conflict_analyzer is not None,
            'routine_optimizer': routine_optimizer is not None
        }
    })


@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'environment': config.app.environment,
        'database': 'connected' if engine else 'disconnected'
    })


@app.route('/api/v1/analyze/conflicts', methods=['POST'])
def analyze_conflicts():
    """Analyze potential conflicts between products."""
    if not conflict_analyzer:
        return jsonify({'error': 'Conflict analyzer not available'}), 503

    try:
        data = request.get_json()
        products = data.get('products', [])
        user_profile = data.get('user_profile', {})

        if not products:
            return jsonify({'error': 'Products list is required'}), 400

        # Analyze conflicts
        db_session = SessionLocal()
        analyzer = create_conflict_analyzer(db_session, rag_system)
        report = analyzer.analyze_products(products, skin_type=user_profile.get('skin_type'))

        return jsonify({
            'success': True,
            'report': report.to_dict()
        })

    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/api/v1/routines/optimize', methods=['POST'])
def optimize_routine():
    """Generate optimized skincare routine."""
    if not routine_optimizer:
        return jsonify({'error': 'Routine optimizer not available'}), 503

    try:
        data = request.get_json()
        products = data.get('products', [])
        user_profile = data.get('user_profile', {})
        preferences = data.get('preferences', {})

        if not products:
            return jsonify({'error': 'Products list is required'}), 400

        # Optimize routine
        db_session = SessionLocal()
        optimizer = create_routine_optimizer(db_session, conflict_analyzer, rag_system)
        routine = optimizer.optimize_routine(products, user_profile, preferences)

        return jsonify({
            'success': True,
            'routine': routine.to_dict()
        })

    except Exception as e:
        return jsonify({'error': f'Optimization failed: {str(e)}'}), 500


@app.route('/api/v1/rag/query', methods=['POST'])
def rag_query():
    """Query the RAG system for ingredient information."""
    if not rag_system:
        return jsonify({'error': 'RAG system not available'}), 503

    try:
        data = request.get_json()
        ingredients = data.get('ingredients', [])
        user_context = data.get('user_context', {})

        if not ingredients:
            return jsonify({'error': 'Ingredients list is required'}), 400

        # Query RAG system
        result = rag_system.query_ingredients_interaction(ingredients, user_context)

        return jsonify({
            'success': True,
            'result': result
        })

    except Exception as e:
        return jsonify({'error': f'RAG query failed: {str(e)}'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print(f"🚀 Starting My Beauty AI server...")
    print(f"   Environment: {config.app.environment}")
    print(f"   Debug mode: {config.app.debug}")
    print(f"   Host: {config.app.host}")
    print(f"   Port: {config.app.port}")

    app.run(
        host=config.app.host,
        port=config.app.port,
        debug=config.app.debug
    )
