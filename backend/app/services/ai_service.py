import json
import re
import logging
from typing import Optional
import httpx
from openai import AsyncOpenAI
from bs4 import BeautifulSoup
from ..config import settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )
        self.model = settings.OPENAI_MODEL

    async def _chat(self, messages: list, temperature: float = 0.3) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "{}"

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except Exception:
                    pass
        return {}

    async def analyze_job(self, job_text: str) -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert job analyst specializing in Product Management and Project Management roles. "
                    "Analyze job postings and return ONLY valid JSON with no additional text."
                ),
            },
            {
                "role": "user",
                "content": f"""Analyze this job posting and return a JSON object with these exact fields:
{{
  "role_category": "Product Manager | Project Manager | Product Owner | Other",
  "seniority_level": "junior | mid | senior | lead | executive",
  "required_years_experience": <number or null>,
  "required_skills": ["skill1", "skill2"],
  "nice_to_have_skills": ["skill1", "skill2"],
  "tools": ["JIRA", "Confluence", "Figma"],
  "responsibilities": ["responsibility1", "responsibility2"],
  "ats_keywords": ["keyword1", "keyword2"],
  "industry": "Technology | Finance | Healthcare | etc",
  "red_flags": ["flag1"],
  "is_junior_fit": true
}}

is_junior_fit should be true if the role requires 0-2 years experience or is entry-level.

Job posting:
{job_text}""",
            },
        ]
        result = await self._chat(messages)
        data = self._parse_json(result)
        defaults = {
            "role_category": "Other",
            "seniority_level": "junior",
            "required_years_experience": None,
            "required_skills": [],
            "nice_to_have_skills": [],
            "tools": [],
            "responsibilities": [],
            "ats_keywords": [],
            "industry": None,
            "red_flags": [],
            "is_junior_fit": True,
        }
        defaults.update(data)
        return defaults

    async def analyze_cv(self, cv_text: str) -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert CV analyst for Product and Project Management roles. "
                    "Extract structured information and return ONLY valid JSON."
                ),
            },
            {
                "role": "user",
                "content": f"""Analyze this CV and return a JSON object:
{{
  "professional_summary": "2-3 sentence summary",
  "skills": ["skill1", "skill2"],
  "tools": ["JIRA", "Figma", "Confluence"],
  "work_experience": [
    {{"company": "...", "title": "...", "duration": "Jan 2022 - Present", "responsibilities": ["..."]}}
  ],
  "education": [
    {{"institution": "...", "degree": "...", "field": "...", "year": "2020"}}
  ],
  "certifications": ["cert1"],
  "projects": ["project description"],
  "languages": ["English", "Hebrew"],
  "achievements": ["achievement1"],
  "product_management_indicators": ["items that show PM experience"],
  "project_management_indicators": ["items that show PjM experience"],
  "weak_areas": ["areas that need improvement for PM/PO roles"]
}}

CV text:
{cv_text}""",
            },
        ]
        result = await self._chat(messages)
        data = self._parse_json(result)
        defaults = {
            "professional_summary": None,
            "skills": [],
            "tools": [],
            "work_experience": [],
            "education": [],
            "certifications": [],
            "projects": [],
            "languages": [],
            "achievements": [],
            "product_management_indicators": [],
            "project_management_indicators": [],
            "weak_areas": [],
        }
        defaults.update(data)
        return defaults

    async def match_cv_to_job(
        self, cv_analysis: dict, job_analysis: dict, cv_text: str, job_text: str
    ) -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an ATS expert scoring CVs against job descriptions. "
                    "Use the weighted scoring rubric. Return ONLY valid JSON."
                ),
            },
            {
                "role": "user",
                "content": f"""Score this CV against the job using this EXACT formula:
final_score = required_skills_match*0.30 + experience_match*0.20 + role_fit*0.15 + ats_keyword_match*0.15 + tools_match*0.10 + education_certifications_match*0.10

Recommendation: "apply" if final_score>=80, "maybe" if >=60, else "skip"

Return this exact JSON structure:
{{
  "final_score": <0-100>,
  "recommendation": "apply | maybe | skip",
  "confidence": "low | medium | high",
  "score_breakdown": {{
    "required_skills_match": <0-100>,
    "experience_match": <0-100>,
    "role_fit": <0-100>,
    "ats_keyword_match": <0-100>,
    "tools_match": <0-100>,
    "education_certifications_match": <0-100>
  }},
  "matching_skills": [],
  "missing_required_skills": [],
  "missing_nice_to_have_skills": [],
  "matching_tools": [],
  "missing_tools": [],
  "matching_keywords": [],
  "missing_keywords": [],
  "transferable_experience": [],
  "experience_gap": "description of experience gap",
  "role_fit_reason": "why candidate fits or doesn't fit this role",
  "ats_feedback": "ATS optimization advice",
  "cv_improvement_suggestions": ["suggestion1"],
  "suggested_cv_bullets": ["bullet1 tailored for this job"],
  "cover_letter_angle": "best angle for cover letter",
  "risk_flags": []
}}

CV Analysis: {json.dumps(cv_analysis)}

Job Analysis: {json.dumps(job_analysis)}""",
            },
        ]
        result = await self._chat(messages, temperature=0.2)
        data = self._parse_json(result)
        defaults = {
            "final_score": 0,
            "recommendation": "skip",
            "confidence": "low",
            "score_breakdown": {
                "required_skills_match": 0,
                "experience_match": 0,
                "role_fit": 0,
                "ats_keyword_match": 0,
                "tools_match": 0,
                "education_certifications_match": 0,
            },
            "matching_skills": [],
            "missing_required_skills": [],
            "missing_nice_to_have_skills": [],
            "matching_tools": [],
            "missing_tools": [],
            "matching_keywords": [],
            "missing_keywords": [],
            "transferable_experience": [],
            "experience_gap": "",
            "role_fit_reason": "",
            "ats_feedback": "",
            "cv_improvement_suggestions": [],
            "suggested_cv_bullets": [],
            "cover_letter_angle": "",
            "risk_flags": [],
        }
        defaults.update(data)
        return defaults

    async def generate_cover_letter(
        self, cv_text: str, job_text: str, match_data: dict, company: str, role: str
    ) -> str:
        matching_skills = match_data.get("matching_skills", [])
        angle = match_data.get("cover_letter_angle", "")
        messages = [
            {
                "role": "system",
                "content": "You are an expert career coach writing personalized cover letters. Write professionally and concisely.",
            },
            {
                "role": "user",
                "content": f"""Write a personalized cover letter for:
Role: {role}
Company: {company}
Key angle: {angle}
Matching strengths: {", ".join(matching_skills[:5])}

The letter should:
- Be 3 paragraphs, professional tone
- Highlight most relevant experience
- Show genuine interest in the role
- End with a clear call to action
- NOT include placeholder brackets
- Be ready to send as-is

CV summary (use for facts):
{cv_text[:2000]}

Job highlights:
{job_text[:1500]}""",
            },
        ]
        result = await self._chat(messages, temperature=0.7)
        return result.strip()

    async def generate_interview_prep(
        self, job_text: str, company: str, role: str, cv_analysis: dict
    ) -> dict:
        messages = [
            {
                "role": "system",
                "content": "You are an expert interview coach for Product and Project Management roles. Return ONLY valid JSON.",
            },
            {
                "role": "user",
                "content": f"""Generate interview preparation for:
Role: {role}
Company: {company}

Return this JSON:
{{
  "hr_questions": ["Tell me about yourself", "Why do you want to work here?", ...5 questions],
  "product_questions": ["How would you prioritize a product backlog?", ...5 PM/PO questions],
  "technical_questions": ["How do you measure product success?", ...3-5 questions],
  "behavioral_questions": ["Tell me about a time you managed stakeholders", ...5 STAR questions],
  "star_suggestions": {{
    "Tell me about a time you managed stakeholders": "Situation: ... Action: ... Result: ..."
  }},
  "company_preparation": "Tips for researching {company} and preparing for the specific role"
}}

Job context:
{job_text[:2000]}

Candidate skills:
{json.dumps(cv_analysis.get("skills", [])[:15])}""",
            },
        ]
        result = await self._chat(messages, temperature=0.5)
        data = self._parse_json(result)
        defaults = {
            "hr_questions": [],
            "product_questions": [],
            "technical_questions": [],
            "behavioral_questions": [],
            "star_suggestions": {},
            "company_preparation": f"Research {company}'s products, recent news, and culture before the interview.",
        }
        defaults.update(data)
        return defaults

    async def evaluate_mock_answer(
        self, question: str, answer: str, job_context: str
    ) -> dict:
        messages = [
            {
                "role": "system",
                "content": "You are an interview coach evaluating candidate answers. Return ONLY valid JSON.",
            },
            {
                "role": "user",
                "content": f"""Evaluate this interview answer for a {job_context} role:

Question: {question}
Answer: {answer}

Return JSON:
{{
  "score": <0-10>,
  "feedback": {{
    "clarity": "...",
    "structure": "...",
    "relevance": "...",
    "confidence": "...",
    "missing_details": "..."
  }},
  "improved_answer": "A stronger version of the answer using STAR method if applicable"
}}""",
            },
        ]
        result = await self._chat(messages, temperature=0.3)
        data = self._parse_json(result)
        defaults = {
            "score": 5,
            "feedback": {
                "clarity": "Answer was clear",
                "structure": "Could benefit from STAR structure",
                "relevance": "Relevant to the question",
                "confidence": "Moderate confidence shown",
                "missing_details": "Consider adding specific metrics",
            },
            "improved_answer": answer,
        }
        defaults.update(data)
        return defaults

    async def scrape_job_url(self, url: str) -> dict:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                html = response.text
        except Exception as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            return {"title": "Failed to fetch", "company": "", "description": str(e)}

        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        title = ""
        company = ""
        location = ""
        description = ""
        work_type = "unknown"

        title_selectors = [
            "h1.job-title", "h1[data-testid='jobTitle']", ".job-title h1",
            "h1.jobsearch-JobInfoHeader-title", "h1",
        ]
        for sel in title_selectors:
            el = soup.select_one(sel)
            if el:
                title = el.get_text(strip=True)
                break

        meta_title = soup.find("meta", property="og:title")
        if not title and meta_title:
            title = meta_title.get("content", "")

        body_text = soup.get_text(separator="\n", strip=True)
        body_text = re.sub(r"\n{3,}", "\n\n", body_text)[:8000]

        if not title:
            lines = [l.strip() for l in body_text.split("\n") if l.strip()]
            title = lines[0] if lines else "Unknown Title"

        url_lower = url.lower()
        if "remote" in body_text.lower():
            work_type = "remote"
        elif "hybrid" in body_text.lower():
            work_type = "hybrid"
        elif "onsite" in body_text.lower() or "on-site" in body_text.lower():
            work_type = "onsite"

        messages = [
            {
                "role": "system",
                "content": "Extract job details from webpage text. Return ONLY valid JSON.",
            },
            {
                "role": "user",
                "content": f"""Extract from this job page text:
{{
  "title": "exact job title",
  "company": "company name",
  "location": "city, country",
  "description": "full job description (500+ words if available)",
  "requirements": "requirements section text",
  "responsibilities": "responsibilities section text",
  "work_type": "remote | hybrid | onsite | unknown"
}}

Page text:
{body_text}""",
            },
        ]
        result = await self._chat(messages)
        data = self._parse_json(result)
        if not data.get("title"):
            data["title"] = title
        if not data.get("work_type"):
            data["work_type"] = work_type
        return data

    async def parse_email_for_jobs(self, email_content: str) -> list:
        messages = [
            {
                "role": "system",
                "content": "Extract job listings from job alert emails. Return ONLY valid JSON array.",
            },
            {
                "role": "user",
                "content": f"""Extract all job listings from this email and return a JSON array:
[
  {{
    "title": "job title",
    "company": "company name",
    "location": "city",
    "url": "job URL if present",
    "description": "brief description",
    "source": "LinkedIn | Glassdoor | etc"
  }}
]

Return empty array [] if no jobs found.

Email content:
{email_content[:5000]}""",
            },
        ]
        result = await self._chat(messages)
        try:
            data = json.loads(result.strip())
            if isinstance(data, list):
                return data
        except Exception:
            match = re.search(r"\[[\s\S]*\]", result)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
        return []
