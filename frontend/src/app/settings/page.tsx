"use client"
import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { useAuthContext } from "@/context/AuthContext"
import { authApi } from "@/lib/api"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Tabs } from "@/components/ui/tabs"
import { toast } from "sonner"

export default function SettingsPage() {
  const { user, refetch } = useAuthContext()
  const [tab, setTab] = useState<"profile" | "api">("profile")

  const [profileForm, setProfileForm] = useState({
    full_name: user?.full_name || "",
    email: user?.email || "",
  })
  const [pwForm, setPwForm] = useState({ current_password: "", new_password: "", confirm: "" })
  const [apiForm, setApiForm] = useState({
    openai_api_key: "",
    openai_model: "gpt-4o-mini",
    openai_base_url: "https://api.openai.com/v1",
  })

  const profileMutation = useMutation({
    mutationFn: () => authApi.updateMe({ full_name: profileForm.full_name }),
    onSuccess: () => { toast.success("Profile updated"); refetch() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Update failed"),
  })

  const pwMutation = useMutation({
    mutationFn: () => {
      if (pwForm.new_password !== pwForm.confirm) throw new Error("Passwords do not match")
      if (pwForm.new_password.length < 8) throw new Error("Password must be at least 8 characters")
      return authApi.updateMe({ current_password: pwForm.current_password, new_password: pwForm.new_password })
    },
    onSuccess: () => { toast.success("Password updated"); setPwForm({ current_password: "", new_password: "", confirm: "" }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || e?.message || "Update failed"),
  })

  const tabs = [
    { id: "profile", label: "Profile" },
    { id: "api", label: "AI / API" },
  ]

  return (
    <DashboardLayout>
      <div className="p-6 max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-sm text-muted-foreground">Manage your account and app configuration</p>
        </div>

        {/* Tab buttons */}
        <div className="flex gap-1 border-b">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id as any)}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                tab === t.id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === "profile" && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Personal Information</CardTitle>
                <CardDescription>Update your name and display information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Full Name</Label>
                  <Input
                    value={profileForm.full_name}
                    onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                    placeholder="Your name"
                  />
                </div>
                <div>
                  <Label>Email</Label>
                  <Input value={profileForm.email} disabled className="bg-muted" />
                  <p className="text-xs text-muted-foreground mt-1">Email cannot be changed</p>
                </div>
                <Button
                  onClick={() => profileMutation.mutate()}
                  disabled={profileMutation.isPending || !profileForm.full_name.trim()}
                >
                  {profileMutation.isPending ? "Saving..." : "Save Changes"}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Change Password</CardTitle>
                <CardDescription>Must be at least 8 characters</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Current Password</Label>
                  <Input
                    type="password"
                    value={pwForm.current_password}
                    onChange={(e) => setPwForm({ ...pwForm, current_password: e.target.value })}
                  />
                </div>
                <div>
                  <Label>New Password</Label>
                  <Input
                    type="password"
                    value={pwForm.new_password}
                    onChange={(e) => setPwForm({ ...pwForm, new_password: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Confirm New Password</Label>
                  <Input
                    type="password"
                    value={pwForm.confirm}
                    onChange={(e) => setPwForm({ ...pwForm, confirm: e.target.value })}
                  />
                </div>
                <Button
                  onClick={() => pwMutation.mutate()}
                  disabled={pwMutation.isPending || !pwForm.current_password || !pwForm.new_password}
                >
                  {pwMutation.isPending ? "Updating..." : "Update Password"}
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        {tab === "api" && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">OpenAI / AI Configuration</CardTitle>
                <CardDescription>
                  Configure the AI backend. These settings are read from environment variables on the server.
                  Update the <code className="bg-muted px-1 rounded text-xs">.env</code> file to change them.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-lg bg-muted/50 border p-4 text-sm space-y-2">
                  <p className="font-medium">Server-side environment variables:</p>
                  <ul className="space-y-1 text-muted-foreground font-mono text-xs">
                    <li>OPENAI_API_KEY=<span className="text-green-500">••••••••••••</span></li>
                    <li>OPENAI_MODEL=gpt-4o-mini</li>
                    <li>OPENAI_BASE_URL=https://api.openai.com/v1</li>
                  </ul>
                  <p className="text-muted-foreground text-xs mt-2">
                    To use a custom OpenAI-compatible endpoint (e.g. Ollama, Azure, Groq), set OPENAI_BASE_URL
                    and OPENAI_MODEL in your .env file and restart the backend.
                  </p>
                </div>

                <Separator />

                <div className="space-y-2">
                  <p className="text-sm font-medium">Supported Models</p>
                  <div className="grid grid-cols-2 gap-2">
                    {["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"].map((m) => (
                      <div key={m} className="text-xs bg-muted rounded px-2 py-1 font-mono">{m}</div>
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Any OpenAI-compatible model ID works. Set OPENAI_MODEL in .env.
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Account Info</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">User ID</span>
                  <span className="font-mono text-xs">{user?.id?.slice(0, 8)}…</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Email</span>
                  <span>{user?.email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Member since</span>
                  <span>{user?.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
