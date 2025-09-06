"""
MongoDB database configuration and setup for Mergington High School API
"""

from pymongo import MongoClient
from argon2 import PasswordHasher
import copy

# In-memory fallback storage
_in_memory_activities = {}
_in_memory_teachers = {}
_use_memory_fallback = False

# Try to connect to MongoDB
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
    client.server_info()  # This will raise an exception if MongoDB is not available
    db = client['mergington_high']
    activities_collection = db['activities']
    teachers_collection = db['teachers']
    print("Connected to MongoDB successfully")
except Exception as e:
    print(f"MongoDB not available, using in-memory storage: {e}")
    _use_memory_fallback = True
    activities_collection = None
    teachers_collection = None

# Methods
def hash_password(password):
    """Hash password using Argon2"""
    ph = PasswordHasher()
    return ph.hash(password)

class MemoryCollection:
    """Simple in-memory collection that mimics basic MongoDB operations"""
    
    def __init__(self, storage_dict):
        self.storage = storage_dict
    
    def find(self, query=None):
        """Find documents matching query"""
        results = []
        for key, doc in self.storage.items():
            if query is None or self._matches_query(doc, query):
                result_doc = copy.deepcopy(doc)
                result_doc['_id'] = key
                results.append(result_doc)
        return results
    
    def find_one(self, query):
        """Find one document matching query"""
        if isinstance(query, dict) and '_id' in query:
            key = query['_id']
            if key in self.storage:
                result_doc = copy.deepcopy(self.storage[key])
                result_doc['_id'] = key
                return result_doc
        return None
    
    def update_one(self, query, update):
        """Update one document"""
        if isinstance(query, dict) and '_id' in query:
            key = query['_id']
            if key in self.storage:
                if '$push' in update:
                    for field, value in update['$push'].items():
                        if field in self.storage[key]:
                            self.storage[key][field].append(value)
                        else:
                            self.storage[key][field] = [value]
                        return type('UpdateResult', (), {'modified_count': 1})()
                elif '$pull' in update:
                    for field, value in update['$pull'].items():
                        if field in self.storage[key] and value in self.storage[key][field]:
                            self.storage[key][field].remove(value)
                        return type('UpdateResult', (), {'modified_count': 1})()
        return type('UpdateResult', (), {'modified_count': 0})()
    
    def _matches_query(self, doc, query):
        """Simple query matching for basic operations"""
        for key, value in query.items():
            if key == 'difficulty':
                if isinstance(value, dict) and '$exists' in value:
                    # Handle $exists operator
                    exists_requirement = value['$exists']
                    has_field = 'difficulty' in doc
                    if exists_requirement and not has_field:
                        return False
                    elif not exists_requirement and has_field:
                        return False
                elif doc.get('difficulty') != value:
                    return False
            elif key == 'schedule_details.days':
                if '$in' in value:
                    target_days = value['$in']
                    if 'schedule_details' in doc and 'days' in doc['schedule_details']:
                        doc_days = doc['schedule_details']['days']
                        if not any(day in doc_days for day in target_days):
                            return False
                    else:
                        return False
            elif key == 'schedule_details.start_time':
                if '$gte' in value:
                    target_time = value['$gte']
                    if 'schedule_details' in doc and 'start_time' in doc['schedule_details']:
                        if doc['schedule_details']['start_time'] < target_time:
                            return False
                    else:
                        return False
            elif key == 'schedule_details.end_time':
                if '$lte' in value:
                    target_time = value['$lte']
                    if 'schedule_details' in doc and 'end_time' in doc['schedule_details']:
                        if doc['schedule_details']['end_time'] > target_time:
                            return False
                    else:
                        return False
        return True

# Create collection objects after initialization
activities_collection = None
teachers_collection = None

def get_activities_collection():
    """Get the activities collection, ensuring it's initialized"""
    if activities_collection is None:
        init_database()
    return activities_collection

def get_teachers_collection():
    """Get the teachers collection, ensuring it's initialized"""
    if teachers_collection is None:
        init_database()
    return teachers_collection

def init_database():
    """Initialize database if empty"""
    global _in_memory_activities, _in_memory_teachers, activities_collection, teachers_collection
    
    if _use_memory_fallback:
        # Initialize in-memory storage if empty
        if not _in_memory_activities:
            _in_memory_activities = copy.deepcopy(initial_activities)
        if not _in_memory_teachers:
            _in_memory_teachers = {teacher["username"]: teacher for teacher in initial_teachers}
        
        # Create collection objects now that data is initialized
        activities_collection = MemoryCollection(_in_memory_activities)
        teachers_collection = MemoryCollection(_in_memory_teachers)
    else:
        # Initialize activities if empty
        if activities_collection.count_documents({}) == 0:
            for name, details in initial_activities.items():
                activities_collection.insert_one({"_id": name, **details})
                
        # Initialize teacher accounts if empty
        if teachers_collection.count_documents({}) == 0:
            for teacher in initial_teachers:
                teachers_collection.insert_one({"_id": teacher["username"], **teacher})

# Initial database if empty
initial_activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Mondays and Fridays, 3:15 PM - 4:45 PM",
        "schedule_details": {
            "days": ["Monday", "Friday"],
            "start_time": "15:15",
            "end_time": "16:45"
        },
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
        "difficulty": "beginner"
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 7:00 AM - 8:00 AM",
        "schedule_details": {
            "days": ["Tuesday", "Thursday"],
            "start_time": "07:00",
            "end_time": "08:00"
        },
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
        "difficulty": "intermediate"
    },
    "Morning Fitness": {
        "description": "Early morning physical training and exercises",
        "schedule": "Mondays, Wednesdays, Fridays, 6:30 AM - 7:45 AM",
        "schedule_details": {
            "days": ["Monday", "Wednesday", "Friday"],
            "start_time": "06:30",
            "end_time": "07:45"
        },
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Tuesday", "Thursday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and compete in basketball tournaments",
        "schedule": "Wednesdays and Fridays, 3:15 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Wednesday", "Friday"],
            "start_time": "15:15",
            "end_time": "17:00"
        },
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore various art techniques and create masterpieces",
        "schedule": "Thursdays, 3:15 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Thursday"],
            "start_time": "15:15",
            "end_time": "17:00"
        },
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Monday", "Wednesday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and prepare for math competitions",
        "schedule": "Tuesdays, 7:15 AM - 8:00 AM",
        "schedule_details": {
            "days": ["Tuesday"],
            "start_time": "07:15",
            "end_time": "08:00"
        },
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Friday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "amelia@mergington.edu"]
    },
    "Weekend Robotics Workshop": {
        "description": "Build and program robots in our state-of-the-art workshop",
        "schedule": "Saturdays, 10:00 AM - 2:00 PM",
        "schedule_details": {
            "days": ["Saturday"],
            "start_time": "10:00",
            "end_time": "14:00"
        },
        "max_participants": 15,
        "participants": ["ethan@mergington.edu", "oliver@mergington.edu"],
        "difficulty": "advanced"
    },
    "Science Olympiad": {
        "description": "Weekend science competition preparation for regional and state events",
        "schedule": "Saturdays, 1:00 PM - 4:00 PM",
        "schedule_details": {
            "days": ["Saturday"],
            "start_time": "13:00",
            "end_time": "16:00"
        },
        "max_participants": 18,
        "participants": ["isabella@mergington.edu", "lucas@mergington.edu"],
        "difficulty": "advanced"
    },
    "Sunday Chess Tournament": {
        "description": "Weekly tournament for serious chess players with rankings",
        "schedule": "Sundays, 2:00 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Sunday"],
            "start_time": "14:00",
            "end_time": "17:00"
        },
        "max_participants": 16,
        "participants": ["william@mergington.edu", "jacob@mergington.edu"]
    },
    "Manga Maniacs": {
        "description": "Dive into the captivating world of Japanese Manga! Discover epic adventures, unforgettable heroes, and mind-bending storylines that have inspired millions worldwide. From action-packed shonen to heartwarming slice-of-life tales, explore the art and storytelling techniques that make manga a unique form of visual literature.",
        "schedule": "Tuesdays, 7:00 PM - 8:30 PM",
        "schedule_details": {
            "days": ["Tuesday"],
            "start_time": "19:00",
            "end_time": "20:30"
        },
        "max_participants": 15,
        "participants": []
    }
}

initial_teachers = [
    {
        "username": "mrodriguez",
        "display_name": "Ms. Rodriguez",
        "password": hash_password("art123"),
        "role": "teacher"
     },
    {
        "username": "mchen",
        "display_name": "Mr. Chen",
        "password": hash_password("chess456"),
        "role": "teacher"
    },
    {
        "username": "principal",
        "display_name": "Principal Martinez",
        "password": hash_password("admin789"),
        "role": "admin"
    }
]

