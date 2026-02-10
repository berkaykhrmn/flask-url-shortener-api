# Flask URL Shortener API

A modern, production-ready URL shortener built with Flask, featuring user authentication, custom short codes, click analytics, asynchronous URL preview fetching, and rate limiting. This project demonstrates a full-stack implementation with Redis for caching, Celery for background tasks, and JWT-based authentication.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white&style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-3.1+-000000?logo=flask&logoColor=white&style=for-the-badge)
![Redis](https://img.shields.io/badge/Redis-7+-DC382D?logo=redis&logoColor=white&style=for-the-badge)
![Celery](https://img.shields.io/badge/Celery-5.6+-37814A?logo=celery&logoColor=white&style=for-the-badge)
![JWT](https://img.shields.io/badge/JWT-black?logo=jsonwebtokens&logoColor=white&style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white&style=for-the-badge)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?logo=pytest&logoColor=white&style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

> **Note:**
> The UI design of this project is based on a pre-made HTML/CSS/JS template.
I fully implemented and integrated the Flask backend myself and adapted the template to the project structure.
All backend functionality — including URL shortening logic, authentication, rate limiting, Redis integration, Celery background tasks, analytics, expiration handling, and API design — was developed by me.


## 🚀 Features

- **URL Shortening**: Generate short, memorable links with automatic or custom codes
- **User Authentication**: Secure JWT-based authentication system with Argon2 password hashing
- **Custom Short Codes**: Create personalized short URLs (4-16 alphanumeric characters)
- **Click Analytics**: Track total clicks and unique visitors for each shortened URL
- **URL Preview Fetching**: Asynchronous background task to fetch page titles and descriptions
- **Rate Limiting**: Redis-backed rate limiting to prevent abuse
- **Link Management**: View and manage all your shortened URLs in one place
- **Expiration System**: Automatic URL expiration (24 hours for guests, 7 days for registered users)
- **RESTful API**: Comprehensive API documentation with OpenAPI/Swagger
- **Modern UI**: Responsive web interface with gradient design and smooth animations
- **Docker Support**: Easy deployment with Docker and Docker Compose

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Testing](#testing)

## 🛠️ Installation

### Prerequisites

- Python 3.11 or higher
- Redis 7 or higher
- Docker and Docker Compose (recommended)
- pip package manager

### Docker Deployment

1. Clone the repository:
```bash
git clone https://github.com/berkaykhrmn/flask-url-shortener-api
cd flask-url-shortener-api
```

2. Create a `.env` file in the project root:
(You can either manually create a new .env file or rename the existing .env.example file to .env, then update the values as needed)
```env
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
BASE_URL=http://localhost:5001
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRES=604800
URL_EXPIRY_SECONDS=604800
```

3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

⚠️ Important: Docker Desktop must be running before you execute any docker or docker compose commands. On Windows and macOS, make sure the Docker Desktop application is open and the Docker engine is started.

The application will be available at:
- Web Interface: `http://localhost:5001`
- API Documentation: `http://localhost:5001/docs`

## ⚙️ Configuration

### Rate Limiting

The application implements the following rate limits:
- **Registration**: 5 per hour
- **Login**: 10 per hour
- **URL Shortening**: 10 per minute
- **Redirects**: 100 per minute
- **Statistics**: 30 per minute
- **User Links**: 30 per minute
- **Default**: 200 per day, 50 per hour

## 🎯 Usage

### Web Interface

1. Navigate to `http://localhost:5001`
2. **Guest Mode**:
   - Paste a URL and click "Shorten URL"
   - URLs expire in 24 hours
   - No custom codes or analytics
3. **Registered User**:
   - Click "Register" to create an account
   - After login, you can:
     - Create custom short codes
     - View click analytics
     - Manage all your links
     - URLs expire in 7 days

The application includes interactive API documentation powered by APIFlask:

- **Swagger UI**: `http://localhost:5001/docs`
- **OpenAPI Spec**: `http://localhost:5001/openapi.json`


## 📁 Project Structure

```
flask-url-shortener-api/
├── app.py                      
├── config.py                   
├── models.py                   
├── schemas.py                  
├── auth_schemas.py             
├── shortener.py                
├── worker.py                   
├── templates/
│   └── index.html              
├── requirements.txt            
├── Dockerfile                  
├── docker-compose.yml          
├── pytest.ini                  
├── tests/
├── .env.example                
└── README.md                   
```

## 🧪 Testing

The project includes a comprehensive test suite using pytest.

### Run Tests with Docker

```bash
docker-compose --profile test up --build
```

### Run Tests Manually

1. Install test dependencies:
```bash
pip install pytest pytest-flask pytest-cov fakeredis
```

2. Run tests:
```bash
pytest -v
```

3. Run tests with coverage:
```bash
pytest --cov=. --cov-report=html
```

### Test Configuration

Tests use `fakeredis` to mock Redis operations, ensuring tests run without external dependencies. The test environment is configured via `TESTING=true` environment variable.

## 🏗️ Architecture

### Technology Stack

- **Framework**: Flask + APIFlask for API documentation
- **Database**: Redis for caching and data storage
- **Authentication**: Flask-JWT-Extended with Argon2 password hashing
- **Task Queue**: Celery with Redis broker
- **Rate Limiting**: Flask-Limiter with Redis backend
- **Web Scraping**: BeautifulSoup4 for URL preview fetching
- **Testing**: Pytest with fakeredis

### Background Tasks

1. **URL Preview Fetching**: When a new URL is shortened by authenticated users, Celery asynchronously fetches the page title and meta description
2. **Cleanup Task**: Runs every hour to remove expired link references from user sets

## 🔒 Security Features

- **Password Hashing**: Argon2
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Prevents abuse and DDoS attacks
- **Input Validation**: Pydantic schemas validate all inputs
- **URL Validation**: Ensures URLs start with http:// or https://
- **Custom Code Validation**: Only alphanumeric characters (4-16 length)

## 🐳 Docker Services

The `docker-compose.yml` defines four services:

1. **redis**: Redis 7 Alpine with health checks and persistent volume
2. **web**: Flask application (port 5001)
3. **worker**: Celery worker for background tasks
4. **beat**: Celery beat for scheduled tasks
5. **test**: Test runner (profile: test)
