from sqlalchemy.orm import Session
from breate_backend.database import SessionLocal, engine, Base
import models

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Predefined Archetypes
archetypes_data = [
    {
        "name": "Creator",
        "description": "Visionary builders who bring ideas to life through artistic, digital, or conceptual creation."
    },
    {
        "name": "Creative",
        "description": "Highly expressive individuals skilled in storytelling, design, and content production."
    },
    {
        "name": "Innovator",
        "description": "Thinkers who challenge norms and develop new concepts, tools, and approaches to complex problems."
    },
    {
        "name": "Systems Thinker",
        "description": "Analytical minds who connect patterns and processes to design efficient, scalable systems."
    }
]

# Predefined Tiers
tiers_data = [
    {
        "name": "Base",
        "level": 1,
        "description": "Entry-level or emerging creators beginning their journey."
    },
    {
        "name": "Standard",
        "level": 2,
        "description": "Intermediate users with growing experience and project involvement."
    },
    {
        "name": "Professional",
        "level": 3,
        "description": "Seasoned experts with advanced knowledge and consistent contributions."
    }
]


def seed_data():
    db: Session = SessionLocal()
    try:
        # Seed Archetypes
        for data in archetypes_data:
            existing = db.query(models.Archetype).filter_by(name=data["name"]).first()
            if not existing:
                db.add(models.Archetype(**data))

        # Seed Tiers
        for data in tiers_data:
            existing = db.query(models.Tier).filter_by(name=data["name"]).first()
            if not existing:
                db.add(models.Tier(**data))

        db.commit()
        print("✅ Archetypes and tiers seeded successfully!")

    except Exception as e:
        db.rollback()
        print("❌ Error seeding data:", e)

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
