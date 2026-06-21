export interface User {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  created_at: string
}

export interface Job {
  id: string
  user_id: string
  source_id: string | null
  title: string
  company: string
  location: string | null
  work_type: "remote" | "hybrid" | "onsite" | "unknown"
  source: string | null
  url: string | null
  description: string | null
  requirements: string | null
  responsibilities: string | null
  required_experience: string | null
  salary: string | null
  date_posted: string | null
  date_added: string
  status: JobStatus
  is_analyzed: boolean
  created_at: string
  updated_at: string
  analysis?: JobAnalysis
  best_match?: JobCVMatch
}

export type JobStatus =
  | "new" | "saved" | "applied" | "interview"
  | "rejected" | "offer" | "archived" | "not_relevant"

export interface JobAnalysis {
  id: string
  job_id: string
  role_category: string | null
  seniority_level: string | null
  required_years_experience: number | null
  required_skills: string[]
  nice_to_have_skills: string[]
  tools: string[]
  responsibilities: string[]
  ats_keywords: string[]
  industry: string | null
  red_flags: string[]
  is_junior_fit: boolean
  created_at: string
}

export interface JobSource {
  id: string
  name: string
  source_type: "email" | "api" | "rss" | "manual_url" | "manual"
  url: string | null
  is_enabled: boolean
  keywords: string[]
  last_sync_at: string | null
  sync_status: "idle" | "syncing" | "error" | "success"
  config: Record<string, unknown> | null
  created_at: string
}

export interface CV {
  id: string
  user_id: string
  filename: string
  original_filename: string
  file_size: number
  file_type: "pdf" | "docx"
  is_active: boolean
  is_analyzed: boolean
  created_at: string
  analysis?: CVAnalysis
}

export interface CVAnalysis {
  id: string
  cv_id: string
  professional_summary: string | null
  skills: string[]
  tools: string[]
  work_experience: WorkExperience[]
  education: Education[]
  certifications: string[]
  projects: string[]
  languages: string[]
  achievements: string[]
  product_management_indicators: string[]
  project_management_indicators: string[]
  weak_areas: string[]
}

export interface WorkExperience {
  company: string
  title: string
  duration: string
  responsibilities: string[]
}

export interface Education {
  institution: string
  degree: string
  field: string
  year: string
}

export interface JobCVMatch {
  id: string
  job_id: string
  cv_id: string
  final_score: number
  recommendation: "apply" | "maybe" | "skip"
  confidence: "low" | "medium" | "high"
  score_breakdown: ScoreBreakdown
  matching_skills: string[]
  missing_required_skills: string[]
  missing_nice_to_have_skills: string[]
  matching_tools: string[]
  missing_tools: string[]
  matching_keywords: string[]
  missing_keywords: string[]
  transferable_experience: string[]
  experience_gap: string | null
  role_fit_reason: string | null
  ats_feedback: string | null
  cv_improvement_suggestions: string[]
  suggested_cv_bullets: string[]
  cover_letter_angle: string | null
  cover_letter_text: string | null
  risk_flags: string[]
  created_at: string
}

export interface ScoreBreakdown {
  required_skills_match: number
  experience_match: number
  role_fit: number
  ats_keyword_match: number
  tools_match: number
  education_certifications_match: number
}

export interface InterviewPreparation {
  id: string
  job_id: string
  hr_questions: string[]
  product_questions: string[]
  technical_questions: string[]
  behavioral_questions: string[]
  star_suggestions: string[]
  company_preparation: string[]
  created_at: string
}

export interface MockInterview {
  id: string
  job_id: string
  status: "active" | "completed"
  current_question_index: number
  questions: string[]
  answers: string[]
  feedbacks: MockFeedback[]
}

export interface MockFeedback {
  score?: number
  strengths?: string[]
  improvements?: string[]
  star_assessment?: Record<string, string>
  example_better_answer?: string
  feedback?: string
  improved_answer?: string
  error?: string
}

export interface DashboardStats {
  total_jobs: number
  new_jobs: number
  saved_jobs: number
  applied_jobs: number
  interview_jobs: number
  avg_cv_match_score: number
  best_matches: Job[]
  top_missing_skills: { skill: string; count: number }[]
  top_companies: { company: string; count: number }[]
  high_priority_jobs: Job[]
  jobs_by_source: { source: string; count: number }[]
  jobs_by_status: Record<string, number>
  recent_jobs: Job[]
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
}

export type JobListResponse = PaginatedResponse<Job>
