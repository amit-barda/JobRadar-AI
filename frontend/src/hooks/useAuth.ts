"use client"
import { useState, useEffect, useCallback } from "react"
import Cookies from "js-cookie"
import { authApi } from "@/lib/api"
import type { User } from "@/types"

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const fetchUser = useCallback(async () => {
    const token = Cookies.get("token") || localStorage.getItem("token")
    if (!token) { setIsLoading(false); return }
    try {
      const { data } = await authApi.me()
      setUser(data)
    } catch {
      Cookies.remove("token")
      localStorage.removeItem("token")
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { fetchUser() }, [fetchUser])

  const login = async (email: string, password: string) => {
    const { data } = await authApi.login(email, password)
    const token = data.access_token
    Cookies.set("token", token, { expires: 7 })
    localStorage.setItem("token", token)
    await fetchUser()
    return data
  }

  const register = async (email: string, password: string, full_name: string) => {
    const { data } = await authApi.register(email, password, full_name)
    const token = data.access_token
    Cookies.set("token", token, { expires: 7 })
    localStorage.setItem("token", token)
    await fetchUser()
    return data
  }

  const logout = () => {
    Cookies.remove("token")
    localStorage.removeItem("token")
    setUser(null)
    window.location.href = "/login"
  }

  return { user, isLoading, isAuthenticated: !!user, login, logout, register, refetch: fetchUser }
}
