# Python Web Development Cursor Rules Summary

A comprehensive collection of Cursor rules for Python web application development, covering best practices, security, performance, and framework-specific guidelines.

## 📋 **Rules Overview**

### **1. Python Web Best Practices** (`.cursor/rules/python-web-best-practices.mdc`)
**Purpose**: Comprehensive guidelines for Python web development across all frameworks

**Key Features**:
- Framework selection guidance (Django, Flask, FastAPI)
- Project structure recommendations
- Security best practices
- Database optimization techniques
- API development guidelines
- Testing strategies
- Deployment best practices
- Logging and monitoring

**Intelligent Triggers**:
- `creating_web_app`: Framework selection and project structure
- `security_concerns`: Input validation, SQL injection prevention, CSRF/XSS protection
- `database_operations`: ORM usage, connection management
- `performance_optimization`: Caching strategies, database optimization
- `api_development`: RESTful design, error handling
- `testing`: Unit testing, API testing
- `deployment`: Environment configuration, WSGI setup, Docker
- `logging_monitoring`: Structured logging, health checks

### **2. Django-Specific Guidelines** (`.cursor/rules/django-specific-guidelines.mdc`)
**Purpose**: Expert Django development guidelines based on industry best practices

**Key Features**:
- MVT (Model-View-Template) pattern adherence
- Django ORM best practices
- Class-based vs function-based views
- Forms and validation
- URL configuration
- Admin interface customization
- Database optimization
- Testing strategies

**Intelligent Triggers**:
- `creating_django_app`: Project layout, app creation, settings configuration
- `writing_models`: Model definition, Meta classes, indexes, methods
- `writing_views`: Class-based views, function-based views, context data
- `forms_validation`: Model forms, custom validators
- `urls_routing`: URL patterns, namespacing, API URLs
- `admin_interface`: Admin models, customizations
- `database_optimization`: Query optimization, N+1 prevention, indexes
- `testing_django`: Test cases, API testing

### **3. Python Security Guidelines** (`.cursor/rules/python-security-guidelines.mdc`)
**Purpose**: Comprehensive security best practices for Python applications

**Key Features**:
- Input validation and sanitization
- SQL injection prevention
- Authentication and authorization
- Session management
- CSRF protection
- XSS prevention
- File upload security
- API security
- Environment security
- Secure logging

**Intelligent Triggers**:
- `input_validation`: Email/phone validation, input sanitization
- `sql_injection_prevention`: Parameterized queries, ORM usage
- `authentication_security`: Password hashing, JWT tokens, API keys
- `session_management`: Secure session configuration
- `csrf_protection`: Django and Flask CSRF implementation
- `xss_prevention`: Template escaping, Content Security Policy
- `file_upload_security`: File validation, secure storage
- `api_security`: Rate limiting, authentication
- `environment_security`: Environment variables, configuration
- `logging_security`: Sensitive data protection

### **4. Python Performance Optimization** (`.cursor/rules/python-performance-optimization.mdc`)
**Purpose**: Performance optimization best practices for Python applications

**Key Features**:
- Database query optimization
- Caching strategies
- Code optimization techniques
- Asynchronous programming
- Memory optimization
- Profiling and monitoring
- Connection pooling
- Background tasks

**Intelligent Triggers**:
- `database_optimization`: N+1 prevention, select_related, prefetch_related
- `caching_strategies`: Django caching, Redis caching, function caching
- `code_optimization`: List comprehensions, generators, data structures
- `async_optimization`: Async/await, I/O operations, FastAPI
- `memory_optimization`: Iterators, garbage collection, weak references
- `profiling_optimization`: Performance profiling, query monitoring
- `connection_pooling`: Database connection pooling
- `background_tasks`: Celery integration, task optimization

## 🧠 **Intelligence Features**

### **Context-Aware Filtering**
Each rule uses multiple filter types:
- **File Extension**: `*.py` files
- **Content Patterns**: Framework-specific keywords
- **Context Patterns**: Development context indicators

### **Conditional Actions**
Rules provide different guidance based on development scenarios:
- **Framework-specific**: Django vs Flask vs FastAPI
- **Development phase**: Creating, testing, deploying
- **Security concerns**: Input validation, authentication
- **Performance issues**: Database queries, caching

### **Smart Pattern Recognition**
Rules detect common anti-patterns and provide specific solutions:
- N+1 query problems
- SQL injection vulnerabilities
- Inefficient code patterns
- Security vulnerabilities

## 📚 **Best Practices Covered**

### **Security**
- Input validation and sanitization
- SQL injection prevention
- CSRF and XSS protection
- Secure authentication
- File upload security
- API rate limiting
- Environment variable management

### **Performance**
- Database query optimization
- Caching strategies
- Memory management
- Asynchronous programming
- Connection pooling
- Background task processing

### **Code Quality**
- Framework-specific patterns
- Error handling
- Testing strategies
- Logging and monitoring
- Code organization

### **Deployment**
- Environment configuration
- WSGI setup
- Docker configuration
- Health checks
- Monitoring

## 🎯 **Usage Examples**

### **Django Development**
```python
# Creating a model
class User(models.Model):
    email = models.EmailField(unique=True)
    # Rule suggests: Add proper field types, Meta class, and indexes

# Writing a view
def product_list(request):
    products = Product.objects.all()
    # Rule suggests: Use select_related/prefetch_related and add pagination
```

### **Security Implementation**
```python
# Unsafe SQL query
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
# Rule suggests: Use parameterized queries to prevent SQL injection

# No input validation
user_input = request.form['message']
# Rule suggests: Always validate and sanitize user input
```

### **Performance Optimization**
```python
# N+1 query problem
for order in orders:
    print(order.user.email)
# Rule suggests: Use select_related to avoid N+1 query problems

# No caching
def get_user_data(user_id):
    return expensive_database_query(user_id)
# Rule suggests: Implement caching to improve performance
```

## 🔧 **Integration with Existing Rules**

These new rules complement the existing rules:
- **Conventional Commits**: Automated commit message formatting
- **Python Flask Guidelines**: Flask-specific development patterns
- **Cursor Rules Location**: File organization and validation

## 📈 **Benefits**

### **For Developers**
- **Immediate Guidance**: Context-aware suggestions during development
- **Best Practices**: Industry-standard patterns and techniques
- **Security**: Built-in security awareness and prevention
- **Performance**: Optimization techniques and anti-pattern detection

### **For Teams**
- **Consistency**: Standardized development practices
- **Quality**: Automated code quality improvements
- **Security**: Reduced security vulnerabilities
- **Maintainability**: Better code organization and patterns

### **For Projects**
- **Scalability**: Performance optimization from the start
- **Reliability**: Comprehensive testing and error handling
- **Security**: Multi-layered security approach
- **Deployment**: Production-ready configuration

## 🚀 **Getting Started**

1. **Install Rules**: All rules are automatically placed in `.cursor/rules/`
2. **Validate Setup**: Run `python3 cursor_validator_cli.py validate`
3. **Start Coding**: Rules will provide intelligent suggestions as you develop
4. **Monitor Usage**: Use `python3 cursor_validator_cli.py summary` to check status

## 📖 **References**

- [Django Documentation](https://docs.djangoproject.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Python Security Best Practices](https://owasp.org/www-project-python-security-top-10/)
- [PostgreSQL with Python](https://www.psycopg.org/docs/usage.html)

---

*These rules provide a comprehensive foundation for Python web development, ensuring security, performance, and maintainability across all development phases.* 