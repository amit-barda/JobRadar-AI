"""Seed demo data. Run: python seed.py"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from app.database import SessionLocal, init_db
from app.models.user import User
from app.models.job import Job, JobSource, JobAnalysis, JobStatus, WorkType, SourceType, SyncStatus
from app.utils.auth import get_password_hash


def seed():
    init_db()
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == "demo@jobradar.ai").first():
            print("Seed data already exists. Skipping.")
            return

        user = User(
            email="demo@jobradar.ai",
            hashed_password=get_password_hash("demo123"),
            full_name="Demo User",
            is_active=True,
        )
        db.add(user)
        db.flush()

        sources = [
            JobSource(user_id=user.id, name="LinkedIn Alerts", source_type=SourceType.email, is_enabled=True),
            JobSource(user_id=user.id, name="Glassdoor Alerts", source_type=SourceType.email, is_enabled=True),
            JobSource(user_id=user.id, name="Drushim RSS", source_type=SourceType.rss, url="https://www.drushim.co.il/rss", is_enabled=False),
            JobSource(user_id=user.id, name="Jobnet", source_type=SourceType.manual_url, is_enabled=True),
            JobSource(user_id=user.id, name="AllJobs", source_type=SourceType.manual_url, is_enabled=True),
        ]
        for s in sources:
            db.add(s)
        db.flush()

        sample_jobs = [
            {
                "title": "Junior Product Manager",
                "company": "TechCorp Ltd",
                "location": "Tel Aviv, Israel",
                "work_type": WorkType.hybrid,
                "source": "LinkedIn",
                "url": "https://linkedin.com/jobs/demo-1",
                "description": "We are looking for a Junior Product Manager to join our growing product team. You will work closely with engineering and design to define requirements, manage the product backlog, and ship impactful features. 0–2 years experience required.",
                "required_experience": "0–2 years",
                "status": JobStatus.new,
            },
            {
                "title": "Associate Product Manager",
                "company": "StartupXYZ",
                "location": "Remote",
                "work_type": WorkType.remote,
                "source": "Glassdoor",
                "url": "https://glassdoor.com/jobs/demo-2",
                "description": "APM role for our B2B SaaS platform. Work on user research, roadmap planning, and feature prioritization. Entry level position. Great opportunity to grow in product.",
                "required_experience": "0–1 years",
                "status": JobStatus.saved,
            },
            {
                "title": "Product Owner",
                "company": "FinTech Solutions",
                "location": "Herzliya, Israel",
                "work_type": WorkType.onsite,
                "source": "AllJobs",
                "url": "https://alljobs.co.il/jobs/demo-3",
                "description": "Product Owner for our banking platform. Manage the product backlog, write user stories, and collaborate with agile development teams. 1–2 years experience.",
                "required_experience": "1–2 years",
                "status": JobStatus.applied,
            },
            {
                "title": "Project Coordinator",
                "company": "ConsultGroup",
                "location": "Tel Aviv, Israel",
                "work_type": WorkType.hybrid,
                "source": "LinkedIn",
                "url": "https://linkedin.com/jobs/demo-4",
                "description": "Coordinate projects across multiple client-facing teams. Create timelines, track milestones, prepare status reports and presentations. Entry level.",
                "required_experience": "Entry Level",
                "status": JobStatus.new,
            },
            {
                "title": "Technical Project Manager",
                "company": "DevStudio",
                "location": "Remote",
                "work_type": WorkType.remote,
                "source": "Drushim",
                "url": "https://drushim.co.il/jobs/demo-5",
                "description": "Bridge technical and business teams as a Technical PM. Manage sprints, coordinate releases, and ensure delivery of high-quality software. Agile/Scrum experience a plus. 1–3 years.",
                "required_experience": "1–3 years",
                "status": JobStatus.interview,
            },
            {
                "title": "Product Manager – Growth",
                "company": "E-commerce Platform",
                "location": "Tel Aviv, Israel",
                "work_type": WorkType.hybrid,
                "source": "Jobnet",
                "url": "https://jobnet.co.il/jobs/demo-6",
                "description": "Drive growth initiatives for our marketplace platform. Own the experimentation roadmap, A/B testing, and user acquisition funnels. Looking for analytical thinkers.",
                "required_experience": "1–2 years",
                "status": JobStatus.new,
            },
        ]

        for i, jd in enumerate(sample_jobs):
            job = Job(
                user_id=user.id,
                is_analyzed=True,
                date_added=datetime.utcnow() - timedelta(days=i * 2),
                **jd,
            )
            db.add(job)
            db.flush()

            analysis = JobAnalysis(
                job_id=job.id,
                role_category="Product Manager" if "Product" in job.title else "Project Manager",
                seniority_level="junior",
                required_years_experience=1.0,
                required_skills=["Product Roadmap", "User Research", "Agile", "Communication", "Stakeholder Management", "User Stories"],
                nice_to_have_skills=["SQL", "Data Analysis", "Figma", "JIRA", "Confluence", "A/B Testing"],
                tools=["JIRA", "Confluence", "Figma", "Slack", "Notion"],
                responsibilities=["Define product requirements", "Manage product backlog", "Collaborate with engineering", "Analyze user feedback", "Report to stakeholders"],
                ats_keywords=["product manager", "agile", "scrum", "roadmap", "user stories", "KPIs", "stakeholders", "backlog"],
                industry="Technology",
                red_flags=[],
                is_junior_fit=True,
            )
            db.add(analysis)

        db.commit()
        print("✓ Seed complete!")
        print("  Login: demo@jobradar.ai / demo123")
        print(f"  Created: {len(sample_jobs)} jobs, {len(sources)} sources")
    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
