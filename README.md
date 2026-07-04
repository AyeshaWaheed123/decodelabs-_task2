# Apex Autohaus — Backend API (Project 2: Backend API Development)

Flask backend for the Apex Autohaus car showroom, using **in-memory storage**
(no database). This is the Project 2 milestone — it proves CRUD logic,
RESTful endpoint design, input validation, and proper HTTP status codes,
before database persistence is added in Project 3.

## ⚠️ Note
Data is stored in Python lists (`cars`, `bookings`) in memory. Restarting the
server resets everything back to the 10 seeded cars — this is expected and
matches the scope of Project 2 (Backend API Development, not database work).

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Visit `http://127.0.0.1:5000` for the showroom, or `http://127.0.0.1:5000/api`
for the API endpoint list.

## API Endpoints

| Method | Endpoint                | Description                                          |
|--------|--------------------------|-------------------------------------------------------|
| GET    | /api/cars                | List all cars (supports `?category=` and `?search=`) |
| GET    | /api/cars/<id>            | Get a single car                                       |
| POST   | /api/cars                | Create a new car                                       |
| PUT    | /api/cars/<id>            | Update an existing car                                 |
| DELETE | /api/cars/<id>            | Delete a car                                           |
| POST   | /api/bookings             | Submit a test-drive / visit request                    |
| GET    | /api/bookings             | List all booking requests                              |
| DELETE | /api/bookings/<id>        | Delete a booking                                       |

## Validation Rules
- `brand`, `name`, `price`, `horsepower`, `category` are required to create a car
- `name` must be unique
- `price` and `horsepower` must be positive numbers
- `category` must be one of: audi, bmw, supercar, muscle, electric
- Bookings require `name`, a valid `email`, and either `car_id` or `model`

## HTTP Status Codes Used
| Code | Meaning |
|------|---------|
| 200  | OK |
| 201  | Created |
| 400  | Bad Request — validation failed |
| 404  | Not Found |
| 405  | Method Not Allowed |
| 500  | Internal Server Error |

---
*Project 2 of 3 — followed by Project 3 (Database Integration) which adds
PostgreSQL/SQLite persistence, schema constraints, and a Bookings→Cars
foreign key relationship.*
