"""Seed HR-AIAAS with synthetic development data.

Usage:
  uv run python scripts/seed_dummy_data.py
  uv run python scripts/seed_dummy_data.py --reset-seed

Safety:
- SQLite only.
- Refuses database filenames without test/dev/demo/local in the name.
- Uses example.test addresses and synthetic records.
- Idempotent through the system_metadata marker `seed.synthetic.v1`.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from pwdlib import PasswordHash
from sqlalchemy import text

from hr_aiaas.config import get_settings
from hr_aiaas.db.session import engine

SEED_KEY = "seed.synthetic.v1"
ADMIN_EMAIL = "admin@example.test"
ADMIN_PASSWORD = "Change-Me-Admin-123!"
RECRUITER_EMAIL = "recruiter@example.test"
RECRUITER_PASSWORD = "Change-Me-Recruiter-123!"

NOW = datetime.now(timezone.utc).replace(microsecond=0)
PASSWORD_HASH = PasswordHash.recommended()


def iso(value: datetime | date | None) -> str | None:
    return value.isoformat() if value is not None else None


def uid(value: int) -> str:
    return str(UUID(int=value))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed synthetic HR-AIAAS development data.")
    parser.add_argument(
        "--reset-seed",
        action="store_true",
        help="Delete only records inserted by this seed, then recreate them.",
    )
    return parser.parse_args()


def validate_target() -> Path:
    settings = get_settings()
    prefix = "sqlite+aiosqlite:///"
    if not settings.database_url.startswith(prefix):
        raise SystemExit("This seed script supports SQLite only.")

    path = Path(settings.database_url.removeprefix(prefix)).resolve()
    safe_tokens = {"test", "dev", "demo", "local", "dummy", "sample"}
    if not any(token in path.name.lower() for token in safe_tokens):
        raise SystemExit(
            f"Refusing to seed database without a development marker in its filename: {path.name}"
        )
    if not path.exists():
        raise SystemExit(f"Database does not exist: {path}. Run Alembic migrations first.")
    return path


async def required_tables(connection) -> None:
    result = await connection.execute(
        text("SELECT name FROM sqlite_master WHERE type = 'table'")
    )
    existing = {row[0] for row in result}
    required = {
        "system_metadata", "users", "roles", "permissions", "user_roles",
        "role_permissions", "sessions", "login_events", "candidates",
        "candidate_contacts", "experiences", "education_records", "skills",
        "candidate_skills", "certifications", "candidate_languages", "documents",
        "document_versions", "document_text_blocks", "ingestion_jobs",
        "model_registry", "prompt_versions", "extraction_runs", "extracted_facts",
        "fact_evidence", "ai_runs", "jobs", "job_requirements", "scorecards",
        "scorecard_criteria", "match_runs", "candidate_job_scores",
        "score_contributions", "shortlists", "shortlist_entries", "talent_pools",
        "talent_pool_memberships", "audit_events", "retention_rules",
        "deletion_requests", "legal_holds",
    }
    missing = sorted(required - existing)
    if missing:
        raise SystemExit(f"Missing migrated tables: {missing}")


async def marker_exists(connection) -> bool:
    result = await connection.execute(
        text("SELECT COUNT(*) FROM system_metadata WHERE key = :key"), {"key": SEED_KEY}
    )
    return int(result.scalar_one()) > 0


async def reset_seed(connection) -> None:
    # Delete in reverse dependency order. IDs below are reserved for this seed.
    statements = [
        "DELETE FROM legal_holds WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM deletion_requests WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM retention_rules WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM audit_events WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM talent_pool_memberships WHERE talent_pool_id BETWEEN 9000 AND 9999",
        "DELETE FROM talent_pools WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM shortlist_entries WHERE shortlist_id BETWEEN 9000 AND 9999",
        "DELETE FROM shortlists WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM score_contributions WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM candidate_job_scores WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM match_runs WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM scorecard_criteria WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM scorecards WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM job_requirements WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM jobs WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM ai_runs WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM fact_evidence WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM extracted_facts WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM extraction_runs WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM prompt_versions WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM model_registry WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM ingestion_jobs WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM document_text_blocks WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM document_versions WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM documents WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM candidate_languages WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM certifications WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM candidate_skills WHERE candidate_id BETWEEN 9000 AND 9999",
        "DELETE FROM skills WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM education_records WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM experiences WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM candidate_contacts WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM candidates WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM login_events WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM sessions WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM role_permissions WHERE role_id BETWEEN 9000 AND 9999",
        "DELETE FROM user_roles WHERE user_id BETWEEN 9000 AND 9999",
        "DELETE FROM permissions WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM roles WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM users WHERE id BETWEEN 9000 AND 9999",
        "DELETE FROM system_metadata WHERE key = :key",
    ]
    for statement in statements:
        await connection.execute(text(statement), {"key": SEED_KEY})


async def seed(connection) -> None:
    n = iso(NOW)
    admin_hash = PASSWORD_HASH.hash(ADMIN_PASSWORD)
    recruiter_hash = PASSWORD_HASH.hash(RECRUITER_PASSWORD)

    await connection.execute(text("INSERT INTO users (id, public_id, email, password_hash, full_name, is_active, is_superuser, last_login_at, created_at, updated_at) VALUES (:id,:public_id,:email,:password_hash,:full_name,1,:superuser,NULL,:created_at,:updated_at)"), [
        {"id": 9001, "public_id": uid(9001), "email": ADMIN_EMAIL, "password_hash": admin_hash, "full_name": "Synthetic Administrator", "superuser": 1, "created_at": n, "updated_at": n},
        {"id": 9002, "public_id": uid(9002), "email": RECRUITER_EMAIL, "password_hash": recruiter_hash, "full_name": "Synthetic Recruiter", "superuser": 0, "created_at": n, "updated_at": n},
    ])

    await connection.execute(text("INSERT INTO roles (id,name,description,created_at,updated_at) VALUES (:id,:name,:description,:created_at,:updated_at)"), [
        {"id":9001,"name":"System Administrator","description":"Synthetic administrator role","created_at":n,"updated_at":n},
        {"id":9002,"name":"Recruiter","description":"Synthetic recruiter role","created_at":n,"updated_at":n},
    ])
    permissions = [
        (9001,"users.read","users","read"),(9002,"users.write","users","write"),
        (9003,"candidate.read","candidate","read"),(9004,"candidate.write","candidate","write"),
        (9005,"documents.upload","documents","upload"),(9006,"jobs.manage","jobs","manage"),
        (9007,"matches.run","matches","run"),(9008,"audit.read","audit","read"),
    ]
    await connection.execute(text("INSERT INTO permissions (id,code,resource,action,description,created_at) VALUES (:id,:code,:resource,:action,:description,:created_at)"), [
        {"id":i,"code":c,"resource":r,"action":a,"description":f"Synthetic permission {c}","created_at":n}
        for i,c,r,a in permissions
    ])
    await connection.execute(text("INSERT INTO user_roles (user_id,role_id,assigned_by_id,assigned_at) VALUES (:user_id,:role_id,9001,:assigned_at)"), [
        {"user_id":9001,"role_id":9001,"assigned_at":n}, {"user_id":9002,"role_id":9002,"assigned_at":n}
    ])
    await connection.execute(text("INSERT INTO role_permissions (role_id,permission_id,assigned_at) VALUES (:role_id,:permission_id,:assigned_at)"), [
        *[{"role_id":9001,"permission_id":i,"assigned_at":n} for i,_,_,_ in permissions],
        *[{"role_id":9002,"permission_id":i,"assigned_at":n} for i in (9001,9003,9004,9005,9006,9007)],
    ])
    await connection.execute(text("INSERT INTO login_events (id,user_id,email_attempted,result,ip_address,user_agent,created_at) VALUES (9001,9002,:email,'success','127.0.0.1','Synthetic Seed Client',:created_at)"), {"email":RECRUITER_EMAIL,"created_at":n})

    candidates = [
        (9001,"Alex Morgan","Data Engineer","reviewed"),
        (9002,"Sam Rivera","Backend Developer","reviewed"),
        (9003,"Jordan Lee","AI Engineer","needs_review"),
    ]
    await connection.execute(text("INSERT INTO candidates (id,public_id,full_name,current_title,professional_summary,profile_status,source_language,is_archived,created_by_id,created_at,updated_at,archived_at) VALUES (:id,:public_id,:name,:title,:summary,:status,'en',0,9002,:created_at,:updated_at,NULL)"), [
        {"id":i,"public_id":uid(i),"name":name,"title":title,"summary":"Synthetic candidate profile for local testing only.","status":status,"created_at":n,"updated_at":n}
        for i,name,title,status in candidates
    ])
    await connection.execute(text("INSERT INTO candidate_contacts (id,candidate_id,contact_type,value,is_primary,created_at) VALUES (:id,:candidate_id,'email',:value,1,:created_at)"), [
        {"id":9001,"candidate_id":9001,"value":"alex.morgan@example.test","created_at":n},
        {"id":9002,"candidate_id":9002,"value":"sam.rivera@example.test","created_at":n},
        {"id":9003,"candidate_id":9003,"value":"jordan.lee@example.test","created_at":n},
    ])
    await connection.execute(text("INSERT INTO experiences (id,candidate_id,company_name,job_title,start_date,end_date,is_current,description,created_at,updated_at) VALUES (:id,:candidate_id,:company,:title,:start_date,NULL,1,:description,:created_at,:updated_at)"), [
        {"id":9001,"candidate_id":9001,"company":"Example Analytics","title":"Data Engineer","start_date":"2022-01-01","description":"Synthetic experience.","created_at":n,"updated_at":n},
        {"id":9002,"candidate_id":9002,"company":"Example Systems","title":"Backend Developer","start_date":"2021-06-01","description":"Synthetic experience.","created_at":n,"updated_at":n},
        {"id":9003,"candidate_id":9003,"company":"Example AI Lab","title":"AI Engineer","start_date":"2023-01-01","description":"Synthetic experience.","created_at":n,"updated_at":n},
    ])
    await connection.execute(text("INSERT INTO education_records (id,candidate_id,institution_name,degree_name,field_of_study,start_date,end_date,description,created_at) VALUES (:id,:candidate_id,'Example University','BSc',:field,'2017-09-01','2021-06-01','Synthetic education.',:created_at)"), [
        {"id":9001,"candidate_id":9001,"field":"Computer Science","created_at":n},
        {"id":9002,"candidate_id":9002,"field":"Software Engineering","created_at":n},
        {"id":9003,"candidate_id":9003,"field":"Data Science","created_at":n},
    ])
    skills=[(9001,"python","Python","Programming"),(9002,"sql","SQL","Data"),(9003,"fastapi","FastAPI","Backend"),(9004,"machine-learning","Machine Learning","AI")]
    await connection.execute(text("INSERT INTO skills (id,normalized_name,display_name,category,is_active,created_at) VALUES (:id,:normalized,:display,:category,1,:created_at)"), [
        {"id":i,"normalized":x,"display":d,"category":c,"created_at":n} for i,x,d,c in skills
    ])
    await connection.execute(text("INSERT INTO candidate_skills (candidate_id,skill_id,proficiency_level,confidence,evidence_summary,last_used_at,created_at) VALUES (:candidate_id,:skill_id,'advanced',:confidence,'Synthetic evidence',:last_used,:created_at)"), [
        {"candidate_id":9001,"skill_id":9001,"confidence":0.95,"last_used":n,"created_at":n},
        {"candidate_id":9001,"skill_id":9002,"confidence":0.90,"last_used":n,"created_at":n},
        {"candidate_id":9002,"skill_id":9001,"confidence":0.90,"last_used":n,"created_at":n},
        {"candidate_id":9002,"skill_id":9003,"confidence":0.92,"last_used":n,"created_at":n},
        {"candidate_id":9003,"skill_id":9004,"confidence":0.94,"last_used":n,"created_at":n},
    ])
    await connection.execute(text("INSERT INTO certifications (id,candidate_id,name,issuer,issued_at,expires_at,credential_id,credential_url,created_at) VALUES (9001,9001,'Synthetic Data Certification','Example Institute','2024-01-01',NULL,'SYN-9001',NULL,:created_at)"), {"created_at":n})
    await connection.execute(text("INSERT INTO candidate_languages (id,candidate_id,language_code,language_name,proficiency_level,confidence,created_at) VALUES (:id,:candidate_id,'en','English','professional',0.95,:created_at)"), [
        {"id":i,"candidate_id":i,"created_at":n} for i in (9001,9002,9003)
    ])

    digest = hashlib.sha256(b"synthetic-cv").hexdigest()
    await connection.execute(text("INSERT INTO documents (id,public_id,candidate_id,original_filename,document_type,mime_type,size_bytes,sha256,status,uploaded_by_id,uploaded_at,deleted_at) VALUES (9001,:public_id,9001,'synthetic_alex_cv.pdf','cv','application/pdf',2048,:sha,'processed',9002,:uploaded_at,NULL)"), {"public_id":uid(19001),"sha":digest,"uploaded_at":n})
    await connection.execute(text("INSERT INTO document_versions (id,document_id,version_number,storage_key,sha256,size_bytes,created_at) VALUES (9001,9001,1,'documents/synthetic/alex-v1.pdf',:sha,2048,:created_at)"), {"sha":digest,"created_at":n})
    evidence = "Synthetic CV evidence: Python and SQL experience."
    await connection.execute(text("INSERT INTO document_text_blocks (id,document_version_id,page_number,section_name,block_index,start_offset,end_offset,content,created_at) VALUES (9001,9001,1,'experience',0,0,:end_offset,:content,:created_at)"), {"end_offset":len(evidence),"content":evidence,"created_at":n})
    await connection.execute(text("INSERT INTO ingestion_jobs (id,public_id,document_version_id,status,attempt_count,maximum_attempts,current_stage,safe_error_code,safe_error_message,queued_at,started_at,heartbeat_at,completed_at) VALUES (9001,:public_id,9001,'COMPLETED',1,3,'INDEXING',NULL,NULL,:queued,:started,:heartbeat,:completed)"), {"public_id":uid(29001),"queued":n,"started":n,"heartbeat":n,"completed":n})

    await connection.execute(text("INSERT INTO model_registry (id,name,model_type,provider,version,digest,context_size,embedding_dimension,is_active,created_at) VALUES (9001,'synthetic-local-model','chat','ollama','test','synthetic-digest',8192,NULL,1,:created_at)"), {"created_at":n})
    await connection.execute(text("INSERT INTO prompt_versions (id,prompt_key,version_number,purpose,template,output_schema,status,created_by_id,approved_by_id,created_at,approved_at) VALUES (9001,'cv.extract',1,'Synthetic extraction','Extract structured facts','{}','approved',9001,9001,:created_at,:approved_at)"), {"created_at":n,"approved_at":n})
    await connection.execute(text("INSERT INTO extraction_runs (id,document_version_id,model_id,prompt_version_id,schema_version,status,overall_confidence,started_at,completed_at) VALUES (9001,9001,9001,9001,'1.0','COMPLETED',0.95,:started,:completed)"), {"started":n,"completed":n})
    await connection.execute(text("INSERT INTO extracted_facts (id,extraction_run_id,candidate_id,field_path,value_type,value_json,confidence,review_status,reviewed_by_id,reviewed_at,created_at) VALUES (9001,9001,9001,'skills[0].name','string',:value,0.95,'confirmed',9002,:reviewed,:created_at)"), {"value":json.dumps("Python"),"reviewed":n,"created_at":n})
    await connection.execute(text("INSERT INTO fact_evidence (id,extracted_fact_id,text_block_id,start_offset,end_offset,evidence_text,created_at) VALUES (9001,9001,9001,23,29,'Python',:created_at)"), {"created_at":n})
    await connection.execute(text("INSERT INTO ai_runs (id,model_id,prompt_version_id,user_id,run_type,resource_type,resource_public_id,status,input_tokens,output_tokens,duration_ms,safe_error_code,created_at,completed_at) VALUES (9001,9001,9001,9002,'cv_extraction','document',:resource_id,'completed',300,80,950,NULL,:created_at,:completed_at)"), {"resource_id":uid(19001),"created_at":n,"completed_at":n})

    await connection.execute(text("INSERT INTO jobs (id,public_id,title,department,location,employment_type,description,status,created_by_id,created_at,updated_at) VALUES (9001,:public_id,'Senior Backend Engineer','Engineering','Remote','Full-time','Synthetic test job.','open',9002,:created_at,:updated_at)"), {"public_id":uid(39001),"created_at":n,"updated_at":n})
    await connection.execute(text("INSERT INTO job_requirements (id,job_id,skill_id,requirement_type,required_level,minimum_years,is_mandatory,created_at) VALUES (:id,9001,:skill_id,:type,:level,:years,:mandatory,:created_at)"), [
        {"id":9001,"skill_id":9001,"type":"required","level":"advanced","years":3,"mandatory":1,"created_at":n},
        {"id":9002,"skill_id":9003,"type":"preferred","level":"intermediate","years":1,"mandatory":0,"created_at":n},
    ])
    await connection.execute(text("INSERT INTO scorecards (id,job_id,version_number,status,created_by_id,approved_by_id,created_at,approved_at) VALUES (9001,9001,1,'approved',9002,9001,:created_at,:approved_at)"), {"created_at":n,"approved_at":n})
    await connection.execute(text("INSERT INTO scorecard_criteria (id,scorecard_id,criterion_code,name,description,weight,configuration_json,display_order) VALUES (:id,9001,:code,:name,:description,:weight,'{}',:order_num)"), [
        {"id":9001,"code":"required_skills","name":"Required skills","description":"Documented required skills","weight":60.0,"order_num":1},
        {"id":9002,"code":"experience","name":"Relevant experience","description":"Documented experience","weight":40.0,"order_num":2},
    ])
    await connection.execute(text("INSERT INTO match_runs (id,public_id,job_id,scorecard_id,created_by_id,status,created_at,completed_at) VALUES (9001,:public_id,9001,9001,9002,'completed',:created_at,:completed_at)"), {"public_id":uid(49001),"created_at":n,"completed_at":n})
    scores=[(9001,9001,88.0,"strong documented match"),(9002,9002,84.0,"strong documented match"),(9003,9003,76.0,"documented match")]
    await connection.execute(text("INSERT INTO candidate_job_scores (id,match_run_id,candidate_id,total_score,match_label,explanation,created_at) VALUES (:id,9001,:candidate_id,:score,:label,'Synthetic deterministic score.',:created_at)"), [
        {"id":i,"candidate_id":c,"score":s,"label":l,"created_at":n} for i,c,s,l in scores
    ])
    await connection.execute(text("INSERT INTO score_contributions (id,candidate_job_score_id,criterion_id,awarded_points,maximum_points,explanation,evidence_json) VALUES (:id,9001,:criterion_id,:awarded,:maximum,:explanation,:evidence)"), [
        {"id":9001,"criterion_id":9001,"awarded":55.0,"maximum":60.0,"explanation":"Python and SQL evidence","evidence":json.dumps({"skill_ids":[9001,9002]})},
        {"id":9002,"criterion_id":9002,"awarded":33.0,"maximum":40.0,"explanation":"Relevant experience","evidence":json.dumps({"experience_ids":[9001]})},
    ])

    await connection.execute(text("INSERT INTO shortlists (id,job_id,name,created_by_id,created_at,updated_at) VALUES (9001,9001,'Initial review',9002,:created_at,:updated_at)"), {"created_at":n,"updated_at":n})
    await connection.execute(text("INSERT INTO shortlist_entries (shortlist_id,candidate_id,added_by_id,reason,added_at) VALUES (9001,:candidate_id,9002,:reason,:added_at)"), [
        {"candidate_id":9001,"reason":"Strong documented match","added_at":n},
        {"candidate_id":9002,"reason":"Strong documented match","added_at":n},
    ])
    await connection.execute(text("INSERT INTO talent_pools (id,name,description,created_by_id,created_at,updated_at) VALUES (9001,'Backend Engineering','Synthetic talent pool',9002,:created_at,:updated_at)"), {"created_at":n,"updated_at":n})
    await connection.execute(text("INSERT INTO talent_pool_memberships (talent_pool_id,candidate_id,added_by_id,reason,added_at,review_at,expires_at) VALUES (9001,9002,9002,'Relevant backend profile',:added_at,:review_at,NULL)"), {"added_at":n,"review_at":iso(NOW+timedelta(days=90))})

    await connection.execute(text("INSERT INTO audit_events (id,user_id,action,resource_type,resource_public_id,outcome,reason,details_json,request_id,ip_address,created_at) VALUES (9001,9002,'candidate.read','candidate',:resource_id,'success','Synthetic audit event',:details,'seed-request','127.0.0.1',:created_at)"), {"resource_id":uid(9001),"details":json.dumps({"source":"seed.synthetic.v1"}),"created_at":n})
    await connection.execute(text("INSERT INTO retention_rules (id,resource_type,retention_days,is_active,updated_by_id,updated_at) VALUES (9001,'candidate',730,1,9001,:updated_at)"), {"updated_at":n})
    await connection.execute(text("INSERT INTO deletion_requests (id,candidate_id,status,reason,requested_by_id,approved_by_id,requested_at,approved_at,completed_at) VALUES (9001,9003,'pending','Synthetic deletion workflow test',9002,NULL,:requested_at,NULL,NULL)"), {"requested_at":n})
    await connection.execute(text("INSERT INTO legal_holds (id,candidate_id,reason,is_active,created_by_id,created_at,released_at) VALUES (9001,9001,'Synthetic legal-hold workflow test',1,9001,:created_at,NULL)"), {"created_at":n})

    await connection.execute(text("INSERT INTO system_metadata (key,value,updated_at) VALUES (:key,:value,:updated_at)"), {"key":SEED_KEY,"value":"synthetic development data; never use in production","updated_at":n})


async def main() -> None:
    args = parse_args()
    path = validate_target()
    async with engine.begin() as connection:
        await connection.execute(text("PRAGMA foreign_keys = ON"))
        await required_tables(connection)
        exists = await marker_exists(connection)
        if exists and not args.reset_seed:
            raise SystemExit("Synthetic seed already exists. Use --reset-seed to recreate it.")
        if args.reset_seed:
            await reset_seed(connection)
        await seed(connection)

    print(f"Seeded synthetic data into: {path}")
    print("Development login credentials:")
    print(f"  Admin:     {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"  Recruiter: {RECRUITER_EMAIL} / {RECRUITER_PASSWORD}")
    print("Change these passwords or delete the seed before any shared deployment.")


if __name__ == "__main__":
    asyncio.run(main())
