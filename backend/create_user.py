"""Create test user with unique email."""
import sys
from pathlib import Path

base_path = Path("D:/OwnProjects/mealmate_y/backend")
sys.path.insert(0, str(base_path))

from app.database import SessionLocal
from app.models import User

db = SessionLocal()

# Check existing
user = db.query(User).filter(User.email == 'test123@test.com').first()

if not user:
    user = User(email='test123@test.com', name='Test User')
    from bcrypt import hashpw, gensalt
    user.password_hash = hashpw(b'test123', gensalt()).decode()
    db.add(user)
    db.commit()
    print('Created user!')
else:
    print('User already exists')

db.close()