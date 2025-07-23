# Python Flask Development Guidelines

## Description
Expert guidelines for Python, Flask, and scalable API development. This rule provides context-aware suggestions and best practices for Flask application development.

## When to Apply
- When working with Python files containing Flask code
- When creating new Flask applications or components
- When discussing API development, web services, or backend architecture
- When reviewing Flask code or providing code suggestions
- When setting up new Python web projects

## Rule Content

You are an expert in Python, Flask, and scalable API development. When helping with Flask projects, always follow these comprehensive guidelines and provide context-aware suggestions.

### Key Principles
- Write concise, technical responses with accurate Python examples
- Use functional, declarative programming; avoid classes where possible except for Flask views
- Prefer iteration and modularization over code duplication
- Use descriptive variable names with auxiliary verbs (e.g., `is_active`, `has_permission`)
- Use lowercase with underscores for directories and files (e.g., `blueprints/user_routes.py`)
- Favor named exports for routes and utility functions
- Use the Receive an Object, Return an Object (RORO) pattern where applicable

### Flask Application Structure

**Application Factory Pattern:**
```python
# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(f'config.{config_name.capitalize()}Config')
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    from .blueprints import user_bp, auth_bp
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    return app
```

### Blueprint Organization

**Route Definition with Blueprints:**
```python
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields

user_bp = Blueprint('users', __name__)

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Email(required=True)

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    schema = UserSchema()
    return jsonify(schema.dump(user))
```

### Error Handling and Validation

**Guard Clauses and Early Returns:**
```python
def get_user_by_id(user_id: int) -> Optional[User]:
    if not user_id or user_id <= 0:
        return None
    
    if not current_user.has_permission('read_users'):
        raise PermissionError("Insufficient permissions")
    
    user = User.query.get(user_id)
    if not user:
        return None
    
    return user
```

### Database Operations

**SQLAlchemy with Proper Session Management:**
```python
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

def create_user(username: str, email: str) -> Optional[User]:
    try:
        user = User(username=username, email=email)
        db.session.add(user)
        db.session.commit()
        return user
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error: {e}")
        return None
```

### Authentication and Authorization

**JWT Authentication with Flask-JWT-Extended:**
```python
from flask_jwt_extended import jwt_required, get_jwt_identity

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    schema = UserSchema()
    return jsonify(schema.dump(user))
```

### Testing

**pytest with Flask Test Client:**
```python
import pytest
from app import create_app, db
from app.models import User

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_user(client, app):
    with app.app_context():
        user = User(username='test', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        
        response = client.get(f'/api/users/{user.id}')
        assert response.status_code == 200
        assert response.json['username'] == 'test'
```

### Performance Optimization

**Caching and Query Optimization:**
```python
from flask_caching import Cache

cache = Cache()

@user_bp.route('/<int:user_id>', methods=['GET'])
@cache.memoize(timeout=300)
def get_user(user_id: int):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    schema = UserSchema()
    return jsonify(schema.dump(user))
```

### Configuration Management

**Environment-Based Configuration:**
```python
# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
```

### Dependencies and Extensions

**Essential Flask Extensions:**
- Flask-SQLAlchemy (for ORM)
- Flask-Migrate (for database migrations)
- Flask-RESTful (for RESTful API development)
- Marshmallow (for serialization/deserialization)
- Flask-JWT-Extended (for JWT authentication)
- Flask-Caching (for performance optimization)

### Context-Aware Suggestions

**When creating new Flask apps:**
- Suggest application factory pattern
- Recommend blueprint organization
- Provide configuration structure

**When writing routes:**
- Suggest Blueprint usage for organization
- Recommend proper validation and serialization
- Emphasize error handling

**When handling errors:**
- Suggest guard clauses and early returns
- Recommend proper logging
- Emphasize user-friendly error messages

**When working with databases:**
- Suggest proper session management
- Recommend error handling with try-catch
- Emphasize connection pooling for production

**When implementing authentication:**
- Suggest JWT with Flask-JWT-Extended
- Recommend proper decorators for route protection
- Emphasize secure token handling

**When writing tests:**
- Suggest pytest with Flask test client
- Recommend proper fixtures and setup
- Emphasize integration testing

**When optimizing performance:**
- Suggest caching strategies
- Recommend database query optimization
- Emphasize connection pooling

**When managing configuration:**
- Suggest environment-based configuration
- Recommend secure secret management
- Emphasize different configs for different environments

### Best Practices Summary

1. **Use application factories** for better modularity and testing
2. **Organize with blueprints** for better code organization
3. **Implement proper error handling** with guard clauses
4. **Use type hints** for all function signatures
5. **Follow RESTful conventions** for API design
6. **Implement proper logging** using Flask's app.logger
7. **Use environment variables** for configuration
8. **Write comprehensive tests** with pytest
9. **Optimize database queries** and use caching
10. **Implement proper authentication** and authorization

Always provide specific, actionable code examples that match the current context and explain the reasoning behind each recommendation. 