from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from fastapi.testclient import TestClient
from app.main import create_app

HEAD={"X-Routiq-Timezone":"UTC"}

def test_preferences_rewards_restart_and_undo(tmp_path):
    path=tmp_path/"records.sqlite3"
    now=lambda:datetime(2026,10,18,12,tzinfo=timezone.utc)
    with TestClient(create_app(path,now),base_url="http://127.0.0.1") as c:
        c.headers.update(HEAD)
        h=c.post("/api/habits",json={"name":"Read a page","reason":"A little learning","small_action":"One page","cue":"After breakfast"}).json()
        assert h["cue"]=="After breakfast"
        prefs=c.get("/api/settings").json()
        prefs.update(theme="dark",display_name="  Alex  ",notifications=True)
        prefs["reminders"]={h["id"]:{"enabled":True,"time":"12:05"}}
        saved=c.put("/api/settings",json=prefs)
        assert saved.status_code==200 and saved.json()["display_name"]=="Alex"
        url=f"/api/habits/{h['id']}/completions/2026-10-18"
        for _ in range(2):assert c.put(url).status_code==200
        rewards=c.get("/api/rewards").json()
        assert rewards["points"]==10 and rewards["milestones"][0]["earned"]
        prefs["gamification"]=False
        assert c.put("/api/settings",json=prefs).status_code==200
        assert c.get("/api/rewards").json()["points"]==10
        for _ in range(2):assert c.delete(url).status_code==200
        assert c.get("/api/rewards").json()["points"]==0
        assert not c.get("/api/rewards").json()["milestones"][0]["earned"]
        assert c.get("/api/version").json()["reminder_delivery"]=="in_app_while_open"
        for endpoint in ("/api/assist/chat","/api/coach/chat"):
            reply=c.post(endpoint,json={"message":"How do reminders work?"})
            assert reply.status_code==200 and "while Routiq is open" in reply.json()["message"]
    with TestClient(create_app(path,now),base_url="http://127.0.0.1") as c:
        assert c.get("/api/settings").json()["theme"]=="dark"
        c.headers.update(HEAD)
        assert c.get("/api/habits").json()["habits"][0]["reason"]=="A little learning"

def test_preferences_validation_preserves_previous_data(tmp_path):
    with TestClient(create_app(tmp_path/"records.sqlite3"),base_url="http://127.0.0.1") as c:
        before=c.get("/api/settings").json()
        for changes in ({"theme":"neon"},{"quiet_hours":True,"quiet_start":"10:00","quiet_end":"10:00"},
                        {"quiet_start":"25:00"},{"notifications":"yes"},{"reminders":{"unknown":{"enabled":True,"time":"09:00"}}},
                        {"timezone":"Other/Zone"},{"display_name":"x"*81}):
            assert c.put("/api/settings",json={**before,**changes}).status_code==422
            assert c.get("/api/settings").json()==before

def test_migration_preserves_existing_records(tmp_path):
    path=tmp_path/"old.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE app_metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        db.execute("INSERT INTO app_metadata VALUES('application','routiq')")
        db.execute("CREATE TABLE habits(id TEXT PRIMARY KEY,name TEXT NOT NULL,description TEXT NOT NULL,created_at TEXT NOT NULL,start_date TEXT NOT NULL)")
        db.execute("CREATE TABLE completions(habit_id TEXT NOT NULL,day TEXT NOT NULL,PRIMARY KEY(habit_id,day))")
        db.execute("INSERT INTO habits VALUES('old','Original habit','','2026-10-17T12:00:00Z','2026-10-17')")
        db.execute("INSERT INTO completions VALUES('old','2026-10-17')")
        db.execute("PRAGMA user_version=2")
    with TestClient(create_app(path,lambda:datetime(2026,10,18,12,tzinfo=timezone.utc)),base_url="http://127.0.0.1") as c:
        c.headers.update(HEAD)
        assert c.get("/api/habits").json()["habits"][0]["cue"]==""
        assert c.get("/api/rewards").json()["points"]==10
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0]==3
        assert db.execute("SELECT count(*) FROM completions").fetchone()[0]==1

def test_new_feature_followups_remain_related_and_prepared():
    from app.assignment import create_assignment_app
    from app.coach_suggestions import FEATURE_GROUPS
    with TestClient(create_assignment_app([], ["testserver"])) as client:
        for topic, questions in FEATURE_GROUPS.items():
            ids={q["id"] for q in questions}
            for q in questions:
                data=client.post("/api/assist/chat",json={"message":q["question"]}).json()
                assert data["source"]=="application_help"
                assert len(data["suggestions"])==4
                assert {x["id"] for x in data["suggestions"]}==ids-{q["id"]}



def test_photo_preferences_persist_remove_and_reject_invalid(tmp_path):
    import base64
    photo = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff\xe0sample\xff\xd9").decode()
    path = tmp_path / "photo.sqlite3"
    with TestClient(create_app(path), base_url="http://127.0.0.1") as c:
        before = c.get("/api/settings").json()
        assert before["avatar_image"] == ""
        assert c.put("/api/settings", json={**before, "avatar_image":photo}).status_code == 200
    with TestClient(create_app(path), base_url="http://127.0.0.1") as c:
        saved = c.get("/api/settings").json()
        assert saved["avatar_image"] == photo
        for invalid in ("data:image/svg+xml;base64,PHN2Zz4=", "https://example.com/a.jpg", "data:image/jpeg;base64,invalid!", "data:image/jpeg;base64," + "a"*200001):
            assert c.put("/api/settings", json={**saved,"avatar_image":invalid}).status_code == 422
            assert c.get("/api/settings").json() == saved
        assert c.put("/api/settings", json={**saved,"avatar_image":""}).status_code == 200
        assert c.get("/api/settings").json()["avatar_image"] == ""
        legacy = {k:v for k,v in before.items() if k != "avatar_image"}
        assert c.put("/api/settings", json=legacy).json()["avatar_image"] == ""
