import pymongo

uri = "mongodb+srv://dharanibarru13:ficYJ1nFgRFtrGrY@student-collab-cluster.8eiaja5.mongodb.net/?retryWrites=true&w=majority&appName=student-collab-cluster"
client = pymongo.MongoClient(uri)

db = client["student_collab_db"]

print("✅ Connected to DB:", db.name)
print("📂 Collections:", db.list_collection_names())
