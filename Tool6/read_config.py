from src.database import SessionLocal, ModelConfiguration

db = SessionLocal()
config = db.query(ModelConfiguration).filter_by(is_active=1).first()
print(f"Tool 4 sees: Version={config.version_id}, Threshold={config.containment_threshold}")
db.close()
