from faker import Faker
from app import app
from models import db, User, Note

fake = Faker()

with app.app_context():
    print("Clearing existing records...")
    Note.query.delete()
    User.query.delete()

    print("Seeding test users...")
    demo_user = User(username="demouser")
    demo_user.password_hash = "password123"

    test_user = User(username="john_doe")
    test_user.password_hash = "secret123"

    db.session.add_all([demo_user, test_user])
    db.session.commit()

    print("Seeding sample notes...")
    categories = ["Work", "Personal", "Ideas", "Study"]

    # 12 notes for demouser to test pagination
    for _ in range(12):
        note = Note(
            title=fake.sentence(nb_words=4),
            content=fake.paragraph(nb_sentences=3),
            category=fake.random_element(elements=categories),
            user_id=demo_user.id
        )
        db.session.add(note)

    # 3 notes for john_doe to verify user data isolation
    for _ in range(3):
        note = Note(
            title=fake.sentence(nb_words=4),
            content=fake.paragraph(nb_sentences=3),
            category="Personal",
            user_id=test_user.id
        )
        db.session.add(note)

    db.session.commit()
    print("Database successfully seeded!")