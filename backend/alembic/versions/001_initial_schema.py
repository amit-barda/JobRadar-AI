"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "job_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), server_default="true"),
        sa.Column("keywords", postgresql.JSON(), server_default="[]"),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("sync_status", sa.String(), server_default="idle"),
        sa.Column("config", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=False, server_default=""),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("work_type", sa.String(), server_default="unknown"),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("required_experience", sa.String(), nullable=True),
        sa.Column("salary", sa.String(), nullable=True),
        sa.Column("date_posted", sa.DateTime(), nullable=True),
        sa.Column("date_added", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("status", sa.String(), server_default="new"),
        sa.Column("is_analyzed", sa.Boolean(), server_default="false"),
        sa.Column("raw_html", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_jobs_user_id", "jobs", ["user_id"])
    op.create_index("ix_jobs_status", "jobs", ["status"])

    op.create_table(
        "job_analysis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("role_category", sa.String(), nullable=True),
        sa.Column("seniority_level", sa.String(), nullable=True),
        sa.Column("required_years_experience", sa.Float(), nullable=True),
        sa.Column("required_skills", postgresql.JSON(), server_default="[]"),
        sa.Column("nice_to_have_skills", postgresql.JSON(), server_default="[]"),
        sa.Column("tools", postgresql.JSON(), server_default="[]"),
        sa.Column("responsibilities", postgresql.JSON(), server_default="[]"),
        sa.Column("ats_keywords", postgresql.JSON(), server_default="[]"),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("red_flags", postgresql.JSON(), server_default="[]"),
        sa.Column("is_junior_fit", sa.Boolean(), server_default="true"),
        sa.Column("raw_analysis", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "cvs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="false"),
        sa.Column("is_analyzed", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "cv_analysis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cv_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("professional_summary", sa.Text(), nullable=True),
        sa.Column("skills", postgresql.JSON(), server_default="[]"),
        sa.Column("tools", postgresql.JSON(), server_default="[]"),
        sa.Column("work_experience", postgresql.JSON(), server_default="[]"),
        sa.Column("education", postgresql.JSON(), server_default="[]"),
        sa.Column("certifications", postgresql.JSON(), server_default="[]"),
        sa.Column("projects", postgresql.JSON(), server_default="[]"),
        sa.Column("languages", postgresql.JSON(), server_default="[]"),
        sa.Column("achievements", postgresql.JSON(), server_default="[]"),
        sa.Column("product_management_indicators", postgresql.JSON(), server_default="[]"),
        sa.Column("project_management_indicators", postgresql.JSON(), server_default="[]"),
        sa.Column("weak_areas", postgresql.JSON(), server_default="[]"),
        sa.Column("raw_analysis", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "job_cv_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cv_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("final_score", sa.Float(), server_default="0"),
        sa.Column("recommendation", sa.String(), server_default="skip"),
        sa.Column("confidence", sa.String(), server_default="low"),
        sa.Column("score_breakdown", postgresql.JSON(), server_default="{}"),
        sa.Column("matching_skills", postgresql.JSON(), server_default="[]"),
        sa.Column("missing_required_skills", postgresql.JSON(), server_default="[]"),
        sa.Column("missing_nice_to_have_skills", postgresql.JSON(), server_default="[]"),
        sa.Column("matching_tools", postgresql.JSON(), server_default="[]"),
        sa.Column("missing_tools", postgresql.JSON(), server_default="[]"),
        sa.Column("matching_keywords", postgresql.JSON(), server_default="[]"),
        sa.Column("missing_keywords", postgresql.JSON(), server_default="[]"),
        sa.Column("transferable_experience", postgresql.JSON(), server_default="[]"),
        sa.Column("experience_gap", sa.Text(), nullable=True),
        sa.Column("role_fit_reason", sa.Text(), nullable=True),
        sa.Column("ats_feedback", sa.Text(), nullable=True),
        sa.Column("cv_improvement_suggestions", postgresql.JSON(), server_default="[]"),
        sa.Column("suggested_cv_bullets", postgresql.JSON(), server_default="[]"),
        sa.Column("cover_letter_angle", sa.Text(), nullable=True),
        sa.Column("cover_letter_text", sa.Text(), nullable=True),
        sa.Column("risk_flags", postgresql.JSON(), server_default="[]"),
        sa.Column("raw_match", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_matches_job_cv", "job_cv_matches", ["job_id", "cv_id"])

    op.create_table(
        "interview_preparations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hr_questions", postgresql.JSON(), server_default="[]"),
        sa.Column("product_questions", postgresql.JSON(), server_default="[]"),
        sa.Column("technical_questions", postgresql.JSON(), server_default="[]"),
        sa.Column("behavioral_questions", postgresql.JSON(), server_default="[]"),
        sa.Column("star_suggestions", postgresql.JSON(), server_default="[]"),
        sa.Column("company_preparation", postgresql.JSON(), server_default="[]"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "mock_interviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(), server_default="active"),
        sa.Column("current_question_index", sa.Integer(), server_default="0"),
        sa.Column("questions", postgresql.JSON(), server_default="[]"),
        sa.Column("answers", postgresql.JSON(), server_default="[]"),
        sa.Column("feedbacks", postgresql.JSON(), server_default="[]"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=True),
        sa.Column("resource_id", sa.String(), nullable=True),
        sa.Column("details", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("type", sa.String(), server_default="info"),
        sa.Column("is_read", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    for table in [
        "notifications", "audit_logs", "mock_interviews",
        "interview_preparations", "job_cv_matches", "cv_analysis",
        "cvs", "job_analysis", "jobs", "job_sources", "users",
    ]:
        op.drop_table(table)
