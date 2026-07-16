# BuildVision 3D - Backend

Flask REST API backend for the **BuildVision 3D** Smart 3D Construction Planning System.

## Technologies

- Python 3.12+
- Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended
- MySQL, PyMySQL
- Flask-CORS

## Project Structure

```
backend/
├── app/
│   ├── models/        # SQLAlchemy models
│   ├── controllers/   # Business logic
│   ├── routes/        # API endpoints
│   ├── services/      # Calculation & domain services
│   └── seeders/       # Sample data
├── migrations/
├── run.py
└── run_seeders.py
```

## Setup

### 1. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate       # Linux/Mac
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and update your MySQL credentials:

```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret
DB_HOST=localhost
DB_PORT=3306
DB_NAME=buildvision
DB_USER=root
DB_PASSWORD=your_password
```

### 4. Create MySQL database

```sql
CREATE DATABASE buildvision;
```

### 5. Run migrations

```bash
flask db init
flask db migrate -m "Initial Migration"
flask db upgrade
```

### 6. Seed database

```bash
python run_seeders.py
```

Default admin credentials: `admin@buildvision.com` / `admin123`

### 7. Run server

```bash
python run.py
```

Server: `http://127.0.0.1:5000`

Health check: `GET /api/health`

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/refresh` | Refresh token |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects/` | List projects |
| POST | `/api/projects/` | Create project |
| GET | `/api/projects/<id>` | Get project |
| PUT | `/api/projects/<id>` | Update project |
| DELETE | `/api/projects/<id>` | Delete project |

### Buildings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/buildings/project/<project_id>` | List buildings |
| POST | `/api/buildings/project/<project_id>` | Create building |
| GET | `/api/buildings/<id>` | Get building |
| PUT | `/api/buildings/<id>` | Update building |
| DELETE | `/api/buildings/<id>` | Delete building |

### Floors
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/floors/building/<building_id>` | List floors |
| POST | `/api/floors/building/<building_id>` | Add floor |
| PUT | `/api/floors/<id>` | Update floor |
| DELETE | `/api/floors/<id>` | Delete floor |

### Pillars
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/pillars/floor/<floor_id>` | List pillars |
| POST | `/api/pillars/floor/<floor_id>` | Create pillar |
| PUT | `/api/pillars/<id>/move` | Move pillar |
| PUT | `/api/pillars/<id>/resize` | Resize pillar |
| DELETE | `/api/pillars/<id>` | Delete pillar |

### Beams & Slabs
Similar CRUD patterns under `/api/beams/` and `/api/slabs/`.

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/summary` | Project summary |
| GET | `/api/dashboard/building/<id>/statistics` | Building stats |
| GET | `/api/dashboard/floor/<id>/materials` | Material info |

## Authentication

Include JWT token in requests:

```
Authorization: Bearer <your_token>
```

## Developer

**Sripavan Jukkirthan** — BuildVision 3D (Educational Project)
