## StarFAVs (Django + DRF)

Star Wars favorites service built with Django and Django REST Framework.

### Prerequisites

- Python 3.10+
- PostgreSQL 13+ running locally
- pip, venv

### 1) Clone and enter

```bash
git clone <your-repo-url> starfavs
cd starfavs
```

### 2) Create and activate virtualenv

```bash
python3 -m venv env
source env/bin/activate
# Windows PowerShell: .\env\Scripts\Activate.ps1
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

If you don’t have a requirements file yet, install the core libs:

```bash
pip install django==4.2.7 djangorestframework==3.16.1 psycopg2-binary==2.9.10
```

### 4) Configure database

This project uses PostgreSQL by default. Update `project/settings.py` if needed:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'starwarsfav',
        'USER': YOUR_DB_USER_NAME,
        'PASSWORD': YOUR_DB_PASSWORD,
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Create the database in Postgres if it doesn't exist:

```sql
CREATE DATABASE starwarsfav;
CREATE USER YOUR_DB_USER_NAME WITH PASSWORD YOUR_DB_PASSWORD;
GRANT ALL PRIVILEGES ON DATABASE starwarsfav TO YOUR_DB_USER_NAME;
```

### 5) Run migrations

```bash
python manage.py migrate
```

### 6) Run dev server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

### 7) API endpoints

- List content with customizations:
  - `GET /api/favorites/content/?user_id=<int>&record_type=movie|planet&page=1&limit=10&search=...`
- Favorites CRUD:
  - `POST /api/favorites/` create
  - `PATCH /api/favorites/<id>/` update title
  - `DELETE /api/favorites/<id>/` delete by id
  - `GET /api/favorites/?user_id=<int>&record_type=movie|planet` list by user/type
  - `DELETE /api/favorites/by-type/?user_id=<int>&record_type=movie|planet&external_record_id=<optional>` bulk delete

### 8) Notes

- External SW API is cached in-memory (see `CACHES` in `project/settings.py`).
- Response schemas for content are typed in `starfavs/favorites/presentation/types.py`.
- Business logic is under:
  - Data layer: `starfavs/favorites/data/`
  - Domain/use-cases: `starfavs/favorites/domain/`
  - Presentation (views/serializers/types): `starfavs/favorites/presentation/`
