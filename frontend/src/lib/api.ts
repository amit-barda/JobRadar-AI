import axios from "axios"
import Cookies from "js-cookie"

const api = axios.create({ baseURL: "/api/v1" })

api.interceptors.request.use((config) => {
  const token = Cookies.get("token") || localStorage.getItem("token")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove("token")
      localStorage.removeItem("token")
      if (typeof window !== "undefined") window.location.href = "/login"
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  register: (email: string, password: string, full_name: string) =>
    api.post("/auth/register", { email, password, full_name }),
  me: () => api.get("/auth/me"),
  updateMe: (data: { full_name?: string; email?: string; current_password?: string; new_password?: string }) =>
    api.put("/auth/me", data),
}

export const jobsApi = {
  list: (params?: Record<string, unknown>) => api.get("/jobs", { params }),
  get: (id: string) => api.get(`/jobs/${id}`),
  addUrl: (url: string) => api.post("/jobs/url", { url }),
  updateStatus: (id: string, status: string) =>
    api.put(`/jobs/${id}/status`, { status }),
  analyze: (id: string) => api.post(`/jobs/${id}/analyze`),
  delete: (id: string) => api.delete(`/jobs/${id}`),
  addEmail: (content: string) => api.post("/jobs/email", { content }),
}

export const sourcesApi = {
  list: () => api.get("/sources"),
  create: (data: Record<string, unknown>) => api.post("/sources", data),
  update: (id: string, data: Record<string, unknown>) =>
    api.put(`/sources/${id}`, data),
  delete: (id: string) => api.delete(`/sources/${id}`),
  sync: (id: string) => api.post(`/sources/${id}/sync`),
}

export const cvsApi = {
  list: () => api.get("/cvs"),
  get: (id: string) => api.get(`/cvs/${id}`),
  upload: (file: File) => {
    const fd = new FormData()
    fd.append("file", file)
    return api.post("/cvs/upload", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    })
  },
  analyze: (id: string) => api.post(`/cvs/${id}/analyze`),
  delete: (id: string) => api.delete(`/cvs/${id}`),
  setActive: (id: string) => api.put(`/cvs/${id}/set-active`),
}

export const matchesApi = {
  matchJobCv: (jobId: string, cvId: string) =>
    api.post(`/matches/job/${jobId}/cv/${cvId}`),
  getJobMatches: (jobId: string) => api.get(`/matches/job/${jobId}`),
  getCvMatches: (cvId: string) => api.get(`/matches/cv/${cvId}`),
  matchCvAllJobs: (cvId: string) =>
    api.post(`/matches/cv/${cvId}/all-jobs`),
  getMatch: (jobId: string, cvId: string) =>
    api.get(`/matches/job/${jobId}/cv/${cvId}`),
}

export const interviewsApi = {
  generate: (jobId: string) => api.post(`/interviews/job/${jobId}/prepare`),
  get: (jobId: string) => api.get(`/interviews/job/${jobId}`),
  startMock: (jobId: string) => api.post("/interviews/mock/start", { job_id: jobId }),
  submitAnswer: (sessionId: string, answer: string) =>
    api.post(`/interviews/mock/${sessionId}/answer`, { answer }),
  getMock: (sessionId: string) => api.get(`/interviews/mock/${sessionId}`),
  listMocks: (jobId?: string) => api.get("/interviews/mock", { params: jobId ? { job_id: jobId } : {} }),
}

export const coverLetterApi = {
  generate: (jobId: string, cvId: string) =>
    api.post("/cover-letter/generate", { job_id: jobId, cv_id: cvId }),
}

export const dashboardApi = {
  stats: () => api.get("/dashboard"),
}

export default api
