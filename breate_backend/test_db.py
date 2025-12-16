from database import SessionLocal
import models

db = SessionLocal()

print("📦 Archetypes:")
for archetype in db.query(models.Archetype).all():
    print(f"- ID: {archetype.id}, Name: {archetype.name}, Description: {archetype.description}")

print("\n🏆 Tiers:")
for tier in db.query(models.Tier).all():
    print(f"- ID: {tier.id}, Name: {tier.name}, Level: {tier.level}, Description: {tier.description}")

db.close()
