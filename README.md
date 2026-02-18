# Velo Commerce API

A production-quality mini-commerce REST API built with **Django** and **Django REST Framework**.

## Overview

Velo is a backend e-commerce API that provides endpoints for product catalog management, shopping cart operations, order processing, and user authentication. It uses JWT-based authentication, automatic API documentation via OpenAPI/Swagger, and is fully containerized with Docker.

## Tech Stack

- **Python 3.12** / **Django 5.2** / **Django REST Framework 3.16**
- **PostgreSQL 18** — primary database
- **Simple JWT** — token-based authentication (access + refresh tokens)
- **drf-spectacular** — OpenAPI 3.0 schema & Swagger/ReDoc docs
- **drf-nested-routers** — nested resource routing (e.g. product variants)
- **django-filter** — filtering, searching, and ordering
- **uv** — fast Python package manager
- **Docker & Docker Compose** — containerized deployment
- **Uvicorn** — ASGI server (via Gunicorn-compatible setup)

## Project Structure

```
velo/
├── velo/               # Django project settings & root URL config
├── users/              # Custom user model (UUID PK), registration, login, JWT auth
├── catalog/            # Products, variants, variant attributes
├── cart/               # Shopping cart & cart items
├── orders/             # Orders & order items with status tracking
├── utils/              # Shared permissions (IsAdminOrReadOnly)
├── docker-compose.yml  # PostgreSQL + web service orchestration
├── Dockerfile          # Python 3.12-slim + uv-based build
├── entry-point.sh      # Migrations, superuser creation, ASGI server start
└── pyproject.toml      # Project metadata & dependencies
```

## API Endpoints

### Authentication (`/api/auth/`)

| Method | Endpoint               | Description            |
|--------|------------------------|------------------------|
| POST   | `/api/auth/register/`  | Register a new user    |
| POST   | `/api/auth/login/`     | Obtain JWT token pair  |
| POST   | `/api/auth/token/refresh/` | Refresh access token |
| POST   | `/api/auth/logout/`    | Logout (blacklist token) |
| GET/PUT | `/api/auth/profile/`  | View/update profile    |

### Catalog (`/api/products/`)

| Method | Endpoint                                        | Description                  |
|--------|-------------------------------------------------|------------------------------|
| GET    | `/api/products/`                                | List all products            |
| POST   | `/api/products/`                                | Create a product (admin)     |
| GET    | `/api/products/{id}/`                           | Retrieve a product           |
| PUT    | `/api/products/{id}/`                           | Update a product (admin)     |
| DELETE | `/api/products/{id}/`                           | Delete a product (admin)     |
| GET    | `/api/products/{id}/variants/`                  | List variants for a product  |
| POST   | `/api/products/{id}/variants/`                  | Create a variant (admin)     |
| GET    | `/api/products/{id}/variants/{variant_id}/`     | Retrieve a variant           |
| PUT    | `/api/products/{id}/variants/{variant_id}/`     | Update a variant (admin)     |
| DELETE | `/api/products/{id}/variants/{variant_id}/`     | Delete a variant (admin)     |

### Cart (`/api/cart/`)

| Method | Endpoint       | Description               |
|--------|----------------|---------------------------|
| GET    | `/api/cart/`   | View the current user's cart |
| POST   | `/api/cart/`   | Add/update cart items     |
| DELETE | `/api/cart/`   | Clear or remove cart items |

### Orders (`/api/orders/`)

| Method | Endpoint              | Description                 |
|--------|-----------------------|-----------------------------|
| GET    | `/api/orders/`        | List the user's orders      |
| POST   | `/api/orders/`        | Place a new order from cart |
| GET    | `/api/orders/{id}/`   | Retrieve order details      |

### Documentation

| Endpoint          | Description          |
|-------------------|----------------------|
| `/api/docs/`      | Swagger UI           |
| `/api/redoc/`     | ReDoc                |
| `/api/schema/`    | Raw OpenAPI schema   |
| `/admin/`         | Django admin panel   |

## Data Models

- **User** — Custom user with UUID primary key, email as login field, optional phone number.
- **Product** — Name, description, image; has many **ProductVariant**s.
- **ProductVariant** — SKU, price, stock quantity; has many **VariantAttribute**s (key-value pairs like `color=red`, `size=L`).
- **Cart / CartItem** — One cart per user, each item references a variant with quantity and optional note.
- **Order / OrderItem** — Snapshot of cart at purchase time with status tracking (`pending` → `confirmed` → `processing` → `shipped` → `delivered` | `cancelled`).

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

### Run with Docker

```bash
# Clone the repository
git clone https://github.com/Moundher122/Velo.git
cd velo

# Start the services (PostgreSQL + Django app)
docker compose up --build
```

The entry-point script automatically:
1. Runs database migrations
2. Creates a default superuser (if missing)
3. Starts the ASGI server on port **8000**

The API will be available at **http://localhost:8000**.

### Local Development (without Docker)

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Set up environment variables (uses SQLite by default)
# Or configure PostgreSQL via DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# Run migrations
uv run manage.py migrate

# Create a superuser
uv run manage.py createsuperuser

# Start the development server
uv run manage.py runserver
```

## Environment Variables

| Variable               | Default                          | Description              |
|------------------------|----------------------------------|--------------------------|
| `DJANGO_SECRET_KEY`    | *(insecure dev key)*             | Django secret key        |
| `DJANGO_DEBUG`         | `True`                           | Debug mode               |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1`            | Comma-separated hosts    |
| `DB_ENGINE`            | `django.db.backends.sqlite3`     | Database engine          |
| `DB_NAME`              | `db.sqlite3`                     | Database name            |
| `DB_USER`              | —                                | Database user            |
| `DB_PASSWORD`          | —                                | Database password        |
| `DB_HOST`              | —                                | Database host            |
| `DB_PORT`              | —                                | Database port            |

## Authentication

The API uses **JWT (JSON Web Tokens)** via `djangorestframework-simplejwt`:

- **Access token**: expires in 60 minutes
- **Refresh token**: expires in 7 days, rotates on use
- Include the token in requests: `Authorization: Bearer <access_token>`

## Permissions

- **Read-only** endpoints (product listing, detail) are public.
- **Write** operations on catalog resources require **admin/staff** privileges.
- **Cart** and **Orders** endpoints require authentication and are scoped to the requesting user.

## Rate Limiting

- Anonymous users: **100 requests/hour**
- Authenticated users: **1,000 requests/hour**

## License

This project is for educational/demo purposes.
