from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")

# ─── In-Memory Storage (no database — Project 2 style) ────────────
cars = []
next_car_id = 1

bookings = []
next_booking_id = 1

VALID_CATEGORIES = {"audi", "bmw", "supercar", "muscle", "electric"}


# ─── Helpers ────────────────────────────────────────────────────────
def find_car(car_id):
    return next((c for c in cars if c["id"] == car_id), None)


def find_booking(booking_id):
    return next((b for b in bookings if b["id"] == booking_id), None)


def validate_car(data, update=False):
    errors = []

    if not update:
        for field in ["brand", "name", "price", "horsepower", "category"]:
            if field not in data or data[field] in (None, ""):
                errors.append(f"{field} is required.")

    if "name" in data:
        if not str(data["name"]).strip():
            errors.append("Name cannot be empty.")
        else:
            existing = next((c for c in cars if c["name"] == str(data["name"]).strip()), None)
            if existing and (not update or existing["id"] != data.get("_current_id")):
                errors.append(f"A car named '{data['name']}' already exists.")

    if "price" in data:
        try:
            price = float(data["price"])
            if price <= 0:
                errors.append("Price must be a positive number.")
        except (ValueError, TypeError):
            errors.append("Price must be a valid number.")

    if "horsepower" in data:
        try:
            hp = float(data["horsepower"])
            if hp <= 0:
                errors.append("Horsepower must be a positive number.")
        except (ValueError, TypeError):
            errors.append("Horsepower must be a valid number.")

    if "category" in data and data["category"] not in VALID_CATEGORIES:
        errors.append(f"Category must be one of: {', '.join(VALID_CATEGORIES)}.")

    return errors


def validate_booking(data):
    errors = []
    if not data.get("name") or not str(data["name"]).strip():
        errors.append("Name is required.")
    if not data.get("email") or "@" not in str(data.get("email", "")):
        errors.append("A valid email is required.")
    if not data.get("car_id") and not data.get("model"):
        errors.append("car_id or model (preferred car name) is required.")
    return errors


# ════════════════════════════════════════════════════════════════════
#  FRONTEND
# ════════════════════════════════════════════════════════════════════
@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api", methods=["GET"])
def api_home():
    return jsonify({
        "message": "Apex Autohaus API",
        "version": "1.0",
        "storage": "in-memory (no database — resets on restart)",
        "endpoints": {
            "GET    /api/cars":          "Get all cars (supports ?category= and ?search=)",
            "POST   /api/cars":          "Add a new car",
            "GET    /api/cars/<id>":     "Get car by ID",
            "PUT    /api/cars/<id>":     "Update car by ID",
            "DELETE /api/cars/<id>":     "Delete car by ID",
            "POST   /api/bookings":      "Submit a test-drive/visit booking",
            "GET    /api/bookings":      "Get all bookings",
            "DELETE /api/bookings/<id>": "Delete a booking",
        }
    }), 200


# ════════════════════════════════════════════════════════════════════
#  CARS — full CRUD
# ════════════════════════════════════════════════════════════════════
@app.route("/api/cars", methods=["GET"])
def get_cars():
    result = cars

    category = request.args.get("category")
    if category and category != "all":
        result = [c for c in result if c["category"] == category]

    search = request.args.get("search")
    if search:
        term = search.lower()
        result = [c for c in result if term in c["name"].lower() or term in c["brand"].lower()]

    return jsonify(result), 200


@app.route("/api/cars/<int:car_id>", methods=["GET"])
def get_car(car_id):
    car = find_car(car_id)
    if not car:
        return jsonify({"error": f"Car with ID {car_id} not found."}), 404
    return jsonify(car), 200


@app.route("/api/cars", methods=["POST"])
def create_car():
    global next_car_id

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required. Send JSON data."}), 400

    errors = validate_car(data)
    if errors:
        return jsonify({"error": "Validation failed.", "details": errors}), 400

    car = {
        "id": next_car_id,
        "brand": str(data["brand"]).strip(),
        "name": str(data["name"]).strip(),
        "description": data.get("description", ""),
        "price": float(data["price"]),
        "horsepower": float(data["horsepower"]),
        "image_url": data.get("image_url", ""),
        "category": data["category"],
    }
    cars.append(car)
    next_car_id += 1

    return jsonify({"message": "Car added successfully.", "car": car}), 201


@app.route("/api/cars/<int:car_id>", methods=["PUT"])
def update_car(car_id):
    car = find_car(car_id)
    if not car:
        return jsonify({"error": f"Car with ID {car_id} not found."}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    data["_current_id"] = car_id
    errors = validate_car(data, update=True)
    if errors:
        return jsonify({"error": "Validation failed.", "details": errors}), 400

    for field in ["brand", "name", "description", "category"]:
        if field in data:
            car[field] = str(data[field]).strip() if field != "description" else data[field]
    if "price" in data:
        car["price"] = float(data["price"])
    if "horsepower" in data:
        car["horsepower"] = float(data["horsepower"])
    if "image_url" in data:
        car["image_url"] = data["image_url"]

    return jsonify({"message": "Car updated successfully.", "car": car}), 200


@app.route("/api/cars/<int:car_id>", methods=["DELETE"])
def delete_car(car_id):
    car = find_car(car_id)
    if not car:
        return jsonify({"error": f"Car with ID {car_id} not found."}), 404

    cars.remove(car)
    return jsonify({"message": f"Car '{car['name']}' deleted successfully."}), 200


# ════════════════════════════════════════════════════════════════════
#  BOOKINGS
# ════════════════════════════════════════════════════════════════════
@app.route("/api/bookings", methods=["POST"])
def create_booking():
    global next_booking_id

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    errors = validate_booking(data)
    if errors:
        return jsonify({"error": "Validation failed.", "details": errors}), 400

    car = None
    if data.get("car_id"):
        car = find_car(data["car_id"])
    elif data.get("model"):
        car = next((c for c in cars if c["name"] == data["model"]), None)

    if not car:
        return jsonify({"error": "No matching car found for this booking."}), 400

    booking = {
        "id": next_booking_id,
        "name": str(data["name"]).strip(),
        "email": str(data["email"]).strip(),
        "message": data.get("message", ""),
        "car_id": car["id"],
        "car_name": car["name"],
    }
    bookings.append(booking)
    next_booking_id += 1

    return jsonify({"message": "Booking created successfully.", "booking": booking}), 201


@app.route("/api/bookings", methods=["GET"])
def get_bookings():
    return jsonify(bookings), 200


@app.route("/api/bookings/<int:booking_id>", methods=["DELETE"])
def delete_booking(booking_id):
    booking = find_booking(booking_id)
    if not booking:
        return jsonify({"error": f"Booking with ID {booking_id} not found."}), 404

    bookings.remove(booking)
    return jsonify({"message": f"Booking {booking_id} deleted."}), 200


# ════════════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ════════════════════════════════════════════════════════════════════
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found. Check /api for available routes."}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed on this endpoint."}), 405


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error."}), 500


# ════════════════════════════════════════════════════════════════════
#  SEED DATA (in-memory, resets on restart)
# ════════════════════════════════════════════════════════════════════
def seed_cars():
    global next_car_id
    seed_data = [
        ("Audi", "Audi R8 V10", "audi", 158000, 602,
         "V10 coupe, quattro grip, carbon interior and track-inspired cockpit.",
         "https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=900&q=80"),
        ("BMW", "BMW M4 Competition", "bmw", 84000, 503,
         "Twin-turbo power, sharp steering and daily comfort with M performance.",
         "https://images.unsplash.com/photo-1556189250-72ba954cfc2b?auto=format&fit=crop&w=900&q=80"),
        ("Porsche", "Porsche 911 Carrera", "supercar", 116000, 379,
         "Rear-engine balance, timeless design and responsive grand touring feel.",
         "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=900&q=80"),
        ("AMG", "Mercedes-AMG GT", "supercar", 132000, 523,
         "Long-hood coupe with premium cabin materials and serious acceleration.",
         "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=900&q=80"),
        ("Ferrari", "Ferrari F8 Tributo", "supercar", 276000, 710,
         "Mid-engine supercar with razor-sharp handling and dramatic Italian styling.",
         "https://images.unsplash.com/photo-1592198084033-aade902d1aae?auto=format&fit=crop&w=900&q=80"),
        ("Lamborghini", "Lamborghini Huracan", "supercar", 248000, 631,
         "V10 excitement, low stance and aggressive performance for weekend drives.",
         "https://images.unsplash.com/photo-1511919884226-fd3cad34687c?auto=format&fit=crop&w=900&q=80"),
        ("Tesla", "Tesla Model S Plaid", "electric", 91000, 1020,
         "Electric luxury sedan with instant torque, clean cabin and extreme speed.",
         "https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&w=900&q=80"),
        ("Ford", "Ford Mustang GT", "muscle", 48000, 486,
         "Classic American V8 muscle with bold design and strong road presence.",
         "https://images.unsplash.com/photo-1584345604476-8ec5e12e42dd?auto=format&fit=crop&w=900&q=80"),
        ("Nissan", "Nissan GT-R Nismo", "supercar", 215000, 600,
         "All-wheel-drive icon with race-bred tuning and explosive acceleration.",
         "https://images.unsplash.com/photo-1600712242805-5f78671b24da?auto=format&fit=crop&w=900&q=80"),
        ("McLaren", "McLaren 720S", "supercar", 305000, 710,
         "Lightweight carbon construction, twin-turbo power and futuristic cabin.",
         "https://images.unsplash.com/photo-1621135802920-133df287f89c?auto=format&fit=crop&w=900&q=80"),
    ]

    for brand, name, category, price, hp, desc, img in seed_data:
        cars.append({
            "id": next_car_id,
            "brand": brand,
            "name": name,
            "description": desc,
            "price": price,
            "horsepower": hp,
            "image_url": img,
            "category": category,
        })
        next_car_id += 1


seed_cars()


if __name__ == "__main__":
    print("Apex Autohaus API (Project 2 — no database) running...")
    print("Visit: http://127.0.0.1:5000/")
    app.run(debug=True, port=5000)
