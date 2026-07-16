# BuildVision 3D API — Routes Reference

Base URL: `http://localhost:5000/api` (adjust host/port per your environment)

All endpoints return JSON in this envelope:

```json
{
  "success": true,
  "message": "Success",
  "data": { }
}
```

Error responses:

```json
{
  "success": false,
  "message": "Error description"
}
```

### Authentication

All routes except `/auth/register` and `/auth/login` require a JWT access token:

```
Authorization: Bearer <access_token>
```

---

## Table of Contents

- [BuildVision 3D API — Routes Reference](#buildvision-3d-api--routes-reference)
    - [Authentication](#authentication)
  - [Table of Contents](#table-of-contents)
  - [Auth](#auth)
    - [Register](#register)
    - [Login](#login)
    - [Refresh Token](#refresh-token)
  - [Users](#users)
  - [Projects](#projects)
  - [Buildings](#buildings)
  - [Floors](#floors)
  - [Pillars](#pillars)
  - [Beams](#beams)
  - [Slabs](#slabs)
  - [Dashboard](#dashboard)
  - [Health Check](#health-check)
  - [Common Error Responses](#common-error-responses)
  - [Example: Full cURL Flow](#example-full-curl-flow)

---

## Auth

Base path: `/api/auth`

### Register
`POST /api/auth/register`

**Body**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "secret123",
  "role": "engineer"
}
```
`role` is optional (defaults to `"engineer"`).

**Response `201`**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "engineer",
    "created_at": "2026-07-15T10:00:00+00:00",
    "updated_at": "2026-07-15T10:00:00+00:00"
  }
}
```

### Login
`POST /api/auth/login`

**Body**
```json
{
  "email": "john@example.com",
  "password": "secret123"
}
```

**Response `200`**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": { "id": 1, "name": "John Doe", "email": "john@example.com", "role": "engineer" },
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi..."
  }
}
```

### Refresh Token
`POST /api/auth/refresh`
Requires `Authorization: Bearer <refresh_token>`

**Response `200`**
```json
{
  "success": true,
  "message": "Token refreshed",
  "data": { "access_token": "eyJhbGciOi..." }
}
```

---

## Users

Base path: `/api/users` (JWT required)

| Method | Route | Description |
|---|---|---|
| GET | `/` | List all users |
| GET | `/<user_id>` | Get a single user |
| POST | `/` | Create a user |
| PUT | `/<user_id>` | Update a user (self or admin) |
| DELETE | `/<user_id>` | Delete a user (self or admin) |

**Create — `POST /api/users/`**
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "password": "secret123",
  "role": "admin"
}
```

**Update — `PUT /api/users/2`**
```json
{
  "name": "Jane S.",
  "role": "manager"
}
```
Any of `name`, `email`, `role`, `password` may be included.

---

## Projects

Base path: `/api/projects` (JWT required, scoped to the current user)

| Method | Route | Description |
|---|---|---|
| GET | `/` | List projects owned by current user |
| GET | `/<project_id>` | Get a project (includes buildings) |
| POST | `/` | Create a project |
| PUT | `/<project_id>` | Update a project |
| DELETE | `/<project_id>` | Delete a project |

**Create — `POST /api/projects/`**
```json
{
  "name": "Riverside Tower",
  "description": "Mixed-use residential/commercial tower",
  "location": "Kandy, LK",
  "status": "planning"
}
```
Only `name` is required.

**Response `201`**
```json
{
  "success": true,
  "message": "Project created",
  "data": {
    "id": 5,
    "name": "Riverside Tower",
    "description": "Mixed-use residential/commercial tower",
    "location": "Kandy, LK",
    "status": "planning",
    "user_id": 1,
    "created_at": "2026-07-15T10:05:00+00:00",
    "updated_at": "2026-07-15T10:05:00+00:00"
  }
}
```

**Get single — `GET /api/projects/5`** returns the project with a nested `"buildings": [...]` array.

---

## Buildings

Base path: `/api/buildings` (JWT required, scoped via parent project ownership)

| Method | Route | Description |
|---|---|---|
| GET | `/project/<project_id>` | List buildings in a project |
| GET | `/<building_id>` | Get a building (includes floors) |
| POST | `/project/<project_id>` | Create a building under a project |
| PUT | `/<building_id>` | Update a building |
| DELETE | `/<building_id>` | Delete a building |

**Create — `POST /api/buildings/project/5`**
```json
{
  "name": "Tower A",
  "building_type": "commercial",
  "total_floors": 12,
  "width": 30.0,
  "length": 40.0,
  "height": 45.0
}
```
Only `name` is required.

---

## Floors

Base path: `/api/floors` (JWT required, scoped via parent building/project ownership)

| Method | Route | Description |
|---|---|---|
| GET | `/building/<building_id>` | List floors in a building |
| GET | `/<floor_id>` | Get a floor (includes pillars, beams, slabs) |
| POST | `/building/<building_id>` | Create a floor under a building |
| PUT | `/<floor_id>` | Update a floor |
| DELETE | `/<floor_id>` | Delete a floor |

**Create — `POST /api/floors/building/8`**
```json
{
  "name": "Ground Floor",
  "floor_number": 0,
  "height": 3.5,
  "area": 500.0
}
```
`name` and `floor_number` are required.

**Get single — `GET /api/floors/14`** returns the floor plus `"pillars"`, `"beams"`, `"slabs"` arrays.

---

## Pillars

Base path: `/api/pillars` (JWT required, scoped via parent floor/building/project ownership)

| Method | Route | Description |
|---|---|---|
| GET | `/floor/<floor_id>` | List pillars on a floor |
| GET | `/<pillar_id>` | Get a pillar |
| POST | `/floor/<floor_id>` | Create a pillar |
| PUT | `/<pillar_id>` | Update a pillar (any field) |
| PUT | `/<pillar_id>/move` | Move a pillar (position only) |
| PUT | `/<pillar_id>/resize` | Resize a pillar (dimensions only) |
| DELETE | `/<pillar_id>` | Delete a pillar |

**Create — `POST /api/pillars/floor/14`**
```json
{
  "name": "P1",
  "x_position": 0.0,
  "y_position": 0.0,
  "width": 0.3,
  "depth": 0.3,
  "height": 3.0,
  "material": "concrete"
}
```
Only `name` is required; other fields default (`width` 0.3, `depth` 0.3, `height` = floor height, `material` "concrete"). `load_capacity` is calculated automatically.

**Move — `PUT /api/pillars/22/move`**
```json
{
  "x_position": 5.0,
  "y_position": 2.5
}
```

**Resize — `PUT /api/pillars/22/resize`**
```json
{
  "width": 0.4,
  "depth": 0.4,
  "height": 3.2
}
```

**Response `200` (example, any pillar endpoint)**
```json
{
  "success": true,
  "message": "Pillar updated",
  "data": {
    "id": 22,
    "name": "P1",
    "x_position": 5.0,
    "y_position": 2.5,
    "width": 0.4,
    "depth": 0.4,
    "height": 3.2,
    "material": "concrete",
    "load_capacity": 812.5,
    "floor_id": 14,
    "created_at": "2026-07-15T10:10:00+00:00",
    "updated_at": "2026-07-15T10:12:00+00:00"
  }
}
```

---

## Beams

Base path: `/api/beams` (JWT required, scoped via parent floor/building/project ownership)

| Method | Route | Description |
|---|---|---|
| GET | `/floor/<floor_id>` | List beams on a floor |
| GET | `/<beam_id>` | Get a beam |
| POST | `/floor/<floor_id>` | Create a beam |
| PUT | `/<beam_id>` | Update a beam |
| DELETE | `/<beam_id>` | Delete a beam |

**Create — `POST /api/beams/floor/14`**
```json
{
  "name": "B1",
  "start_x": 0.0,
  "start_y": 0.0,
  "end_x": 5.0,
  "end_y": 0.0,
  "width": 0.25,
  "depth": 0.4,
  "material": "concrete"
}
```
Only `name` is required. `length` and `load_bearing` are computed automatically from the coordinates and material.

**Response `201`**
```json
{
  "success": true,
  "message": "Beam created",
  "data": {
    "id": 9,
    "name": "B1",
    "start_x": 0.0,
    "start_y": 0.0,
    "end_x": 5.0,
    "end_y": 0.0,
    "width": 0.25,
    "depth": 0.4,
    "length": 5.0,
    "material": "concrete",
    "load_bearing": 320.0,
    "floor_id": 14,
    "created_at": "2026-07-15T10:15:00+00:00",
    "updated_at": "2026-07-15T10:15:00+00:00"
  }
}
```

---

## Slabs

Base path: `/api/slabs` (JWT required, scoped via parent floor/building/project ownership)

| Method | Route | Description |
|---|---|---|
| GET | `/floor/<floor_id>` | List slabs on a floor |
| GET | `/<slab_id>` | Get a slab |
| POST | `/floor/<floor_id>` | Create a slab |
| PUT | `/<slab_id>` | Update a slab |
| DELETE | `/<slab_id>` | Delete a slab |

**Create — `POST /api/slabs/floor/14`**
```json
{
  "name": "S1",
  "thickness": 0.15,
  "area": 25.0,
  "material": "concrete",
  "reinforcement": "standard"
}
```
Only `name` is required (`area` defaults to the floor's area). `load_capacity` is computed automatically.

---

## Dashboard

Base path: `/api/dashboard` (JWT required)

| Method | Route | Description |
|---|---|---|
| GET | `/summary` | Summary of all of the current user's projects |
| GET | `/building/<building_id>/statistics` | Aggregate statistics for a building |
| GET | `/floor/<floor_id>/materials` | Material estimates + component counts for a floor |

**Project summary — `GET /api/dashboard/summary`**

**Response `200`**
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "total_projects": 2,
    "projects": [
      {
        "project": { "id": 5, "name": "Riverside Tower", "status": "planning" },
        "building_count": 1,
        "floor_count": 3
      }
    ]
  }
}
```

**Floor materials — `GET /api/dashboard/floor/14/materials`**

**Response `200`**
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "floor": { "id": 14, "name": "Ground Floor", "floor_number": 0 },
    "materials": { "concrete_volume": 12.5, "steel_weight": 850.0 },
    "components": { "pillars": 4, "beams": 6, "slabs": 2 }
  }
}
```
*(exact keys under `materials` depend on `CalculationService.estimate_materials`)*

---

## Health Check

`GET /api/health` — no auth required

**Response `200`**
```json
{
  "status": "ok",
  "service": "BuildVision 3D API"
}
```

---

## Common Error Responses

| Status | Meaning | Example |
|---|---|---|
| 400 | Validation error | `{"success": false, "message": "Missing required fields: name"}` |
| 401 | Missing/invalid auth | `{"success": false, "message": "Unauthorized"}` |
| 403 | Not the resource owner | `{"success": false, "message": "Forbidden"}` |
| 404 | Resource not found | `{"success": false, "message": "Project not found"}` |

## Example: Full cURL Flow

```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"secret123"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"secret123"}'

# Create a project (use access_token from login response)
curl -X POST http://localhost:5000/api/projects/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"name":"Riverside Tower"}'
```