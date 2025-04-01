# URL Shortener API

A FastAPI-based URL shortening service with analytics and management features.

## Features

- Create, read, update, and delete short URLs
- Custom URL aliases
- URL expiration
- URL analytics (access count, last accessed)
- User authentication
- Redis caching for improved performance
- PostgreSQL database for data persistence

## API Endpoints

### URL Management

- `POST /api/v1/links/shorten` - Create a new short URL
- `GET /api/v1/links/{short_code}` - Redirect to original URL
- `DELETE /api/v1/links/{short_code}` - Delete a URL (requires authentication)
- `PUT /api/v1/links/{short_code}` - Update a URL (requires authentication)
- `GET /api/v1/links/{short_code}/stats` - Get URL statistics
- `GET /api/v1/links/search` - Search URL by original URL

### User Management

- `POST /api/v1/users/register` - Register a new user
- `POST /api/v1/users/login` - Login and get access token
- `GET /api/v1/users/me` - Get current user information
- `PUT /api/v1/users/me` - Update current user information

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd url-shortener
```

2. Create a `.env` file in the root directory (optional, for local development):
```env
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=url_shortener
REDIS_HOST=localhost
REDIS_PORT=6379
SECRET_KEY=your-secret-key
```

3. Start the application using Docker Compose:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`

## API Documentation

Once the application is running, you can access:
- Swagger UI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## Development

To run the application locally without Docker:

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start PostgreSQL and Redis (using Docker):
```bash
docker-compose up db redis -d
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## Testing

To run tests:
```bash
pytest
```

## License

MIT License # fastapi_project
