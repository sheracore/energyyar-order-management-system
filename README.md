# Order Management System
## A backend API for managing orders, products, and order items using Django REST Framework, PostgreSQL, and Docker.
### It supports
* Order creation & updates (PUT/PATCH)
* Order listing with filters
* Token authentication
* Swagger API documentation
* Dockerized environment with PostgreSQL

### Tech Stack
* Python 3.12
* Django 5+
* Django REST Framework
* PostgreSQL
* Docker & Docker Compose
* drf-spectacular (Swagger UI)


## Setup with Docker (Recommended)
1. Clone project
```commandline
git clone [url]
cd order-management

```

2. Create .env file
```commandline
POSTGRES_DB=order_db
POSTGRES_USER=order_user
POSTGRES_PASSWORD=order_pass

DB_HOST=db
DB_PORT=5432

SECRET_KEY=your-secret-key
DEBUG=1
```

3. Run with Docker
```commandline
docker compose up --build
```

4. Create superuser
```commandline
docker compose exec web python manage.py createsuperuser
```

## API Base URL
```commandline
http://127.0.0.1:8000/
```

## API Documentation URLs
```commandline
http://127.0.0.1:8000/api/schema/swagger-ui/
http://127.0.0.1:8000/api/schema/
```

## A Usage flow
1. create superuser
2. create new user using django admin panel(customer roll)
3. generate products using django admin panel
4. login in using this url: http://127.0.0.1:8000/api/token/
5. now create orders using admin and customer rolls
6. now you can use other endpoints: list your orders, filter them, remove or update them and ...