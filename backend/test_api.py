import os
import unittest
import base64
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test database path before imports
os.environ["DATABASE_URL"] = "sqlite:///./test_campus_dashboard.db"

from .main import app
from .database import Base, get_db
from .routers.academics import seed_academics

# Create testing engine
engine = create_engine("sqlite:///./test_campus_dashboard.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestCampusDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        # Seed test db
        db = TestingSessionLocal()
        seed_academics(db)
        db.close()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test_campus_dashboard.db"):
            try:
                os.remove("./test_campus_dashboard.db")
            except Exception:
                pass

    def setUp(self):
        self.db = TestingSessionLocal()
        def override_get_db():
            try:
                yield self.db
            finally:
                self.db.close()
        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        self.db.close()
        app.dependency_overrides.clear()

    def get_auth_headers(self, email, password):
        login_res = self.client.post("/auth/login", json={"email": email, "password": password})
        token = login_res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_01_auth_flow(self):
        # 1. Register new user
        reg_data = {
            "name": "Jane Doe",
            "roll_number": "CS2026999",
            "email": "jane.doe@campus.edu",
            "password": "securepassword123"
        }
        res = self.client.post("/auth/register", json=reg_data)
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.json())

        # 2. Register duplicate email
        res_dup_email = self.client.post("/auth/register", json={
            "name": "Jane Duplicate",
            "roll_number": "CS2026111",
            "email": "jane.doe@campus.edu",
            "password": "securepassword123"
        })
        self.assertEqual(res_dup_email.status_code, 400)
        self.assertEqual(res_dup_email.json()["detail"], "email already exists")

        # 3. Register duplicate roll number
        res_dup_roll = self.client.post("/auth/register", json={
            "name": "Jane Duplicate",
            "roll_number": "CS2026999",
            "email": "jane2@campus.edu",
            "password": "securepassword123"
        })
        self.assertEqual(res_dup_roll.status_code, 400)
        self.assertEqual(res_dup_roll.json()["detail"], "roll_number already exists")

        # 4. Login correct credentials
        res_login = self.client.post("/auth/login", json={
            "email": "jane.doe@campus.edu",
            "password": "securepassword123"
        })
        self.assertEqual(res_login.status_code, 200)
        self.assertIn("access_token", res_login.json())

        # 5. Login incorrect credentials
        res_login_bad = self.client.post("/auth/login", json={
            "email": "jane.doe@campus.edu",
            "password": "wrongpassword"
        })
        self.assertEqual(res_login_bad.status_code, 401)

    def test_02_library_mcp(self):
        headers = self.get_auth_headers("jane.doe@campus.edu", "securepassword123")
        
        # Check all books
        res = self.client.get("/mcp/library/books", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.json()), 10)

        # Search book
        res_search = self.client.get("/mcp/library/search?q=Algorithms", headers=headers)
        self.assertEqual(res_search.status_code, 200)
        self.assertTrue(any("Algorithms" in b["title"] for b in res_search.json()))

        # Book availability
        res_avail = self.client.get("/mcp/library/availability/lib-001", headers=headers)
        self.assertEqual(res_avail.status_code, 200)
        self.assertEqual(res_avail.json()["status"], "Available")

    def test_03_profile_and_calendar(self):
        headers = self.get_auth_headers("jane.doe@campus.edu", "securepassword123")

        # 1. Borrow book - Valid due date (tomorrow)
        tomorrow = "2026-06-16"
        res_borrow = self.client.post("/profile/books", headers=headers, json={
            "book_id": "lib-001",
            "title": "Introduction to Algorithms",
            "due_date": tomorrow
        })
        self.assertEqual(res_borrow.status_code, 201)

        # 2. Borrow book - Past due date (should fail)
        res_borrow_past = self.client.post("/profile/books", headers=headers, json={
            "book_id": "lib-003",
            "title": "Clean Code",
            "due_date": "2020-01-01"
        })
        self.assertEqual(res_borrow_past.status_code, 400)
        self.assertIn("Due date must be today or later.", res_borrow_past.json()["detail"])

        # 3. Toggle Event flag
        res_flag = self.client.post("/profile/events", headers=headers, json={"event_id": "evt-001"})
        self.assertEqual(res_flag.status_code, 200)
        self.assertEqual(res_flag.json()["event_id"], "evt-001")

        # 4. Like Cafeteria menu day
        res_like = self.client.post("/profile/cafeteria", headers=headers, json={"day": "Monday"})
        self.assertEqual(res_like.status_code, 200)
        self.assertEqual(res_like.json()["day"], "Monday")

        # 5. Fetch calendar and check items
        res_cal = self.client.get("/profile/calendar", headers=headers)
        self.assertEqual(res_cal.status_code, 200)
        cal_items = res_cal.json()
        self.assertTrue(any(c["type"] == "book_due" for c in cal_items))
        self.assertTrue(any(c["type"] == "event" for c in cal_items))
        self.assertTrue(any(c["type"] == "liked_menu" for c in cal_items))

    def test_04_academics_mcp(self):
        headers = self.get_auth_headers("jane.doe@campus.edu", "securepassword123")

        # Search PDFs
        res_search = self.client.get("/mcp/academics/search?q=Calculus", headers=headers)
        self.assertEqual(res_search.status_code, 200)
        self.assertTrue(any("Calculus" in p["title"] for p in res_search.json()))

        # Upload - invalid type (non-PDF)
        bad_file = {"file": ("test.txt", b"some txt content", "text/plain")}
        res_upload_bad = self.client.post(
            "/mcp/academics/upload",
            headers=headers,
            data={"title": "Text File", "subject": "CS"},
            files=bad_file
        )
        self.assertEqual(res_upload_bad.status_code, 400)
        self.assertEqual(res_upload_bad.json()["detail"], "Only PDF files are supported.")

        # Upload - Valid PDF
        pdf_content = b"%PDF-1.4 ... Hello World PDF Content ... %%EOF"
        good_file = {"file": ("test.pdf", pdf_content, "application/pdf")}
        res_upload = self.client.post(
            "/mcp/academics/upload",
            headers=headers,
            data={"title": "Test PDF Syllabus", "subject": "Syllabus"},
            files=good_file
        )
        self.assertEqual(res_upload.status_code, 201)
        pdf_id = res_upload.json()["id"]

        # Download PDF
        res_download = self.client.get(f"/mcp/academics/download/{pdf_id}")
        self.assertEqual(res_download.status_code, 200)
        self.assertEqual(res_download.headers["content-type"], "application/pdf")
        self.assertEqual(res_download.content, pdf_content)

    def test_05_ai_graceful_degradation(self):
        # Ensure GEMINI_API_KEY is unset or empty during test
        old_key = os.environ.get("GEMINI_API_KEY")
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
            
        headers = self.get_auth_headers("jane.doe@campus.edu", "securepassword123")
        res = self.client.post("/ai/chat", headers=headers, json={"query": "Is clean code available?"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["response"], "AI assistant is currently unavailable — missing API configuration")

        if old_key is not None:
            os.environ["GEMINI_API_KEY"] = old_key
