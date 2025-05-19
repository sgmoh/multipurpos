from app import app, db

# Import models to ensure they are registered with SQLAlchemy
import models

# Create tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)