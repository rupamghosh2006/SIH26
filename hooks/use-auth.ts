"use client";

import { useState, useEffect } from "react";

interface User {
  id: string;
  email?: string;
  firstName?: string;
  lastName?: string;
  role?: string;
  avatar?: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    const checkAuth = async () => {
      try {
        // First check localStorage for instant render
        let localUser: User | null = null;
        if (typeof window !== "undefined") {
          const stored = localStorage.getItem("profile") || localStorage.getItem("user");
          if (stored) {
            try {
              localUser = JSON.parse(stored);
              if (localUser && (localUser.email || localUser.id || localUser.firstName)) {
                setUser(localUser);
                setLoading(false);
              }
            } catch {}
          }
        }

        // Validate or refresh session via API in background
        const response = await fetch("/api/profile", {
          method: "GET",
          credentials: "include",
          cache: "no-store",
        });

        if (response.ok) {
          const data = await response.json();
          if (data.success && data.user) {
            const userData: User = {
              id: data.user.id || "",
              email: data.user.email,
              firstName: data.user.firstName,
              lastName: data.user.lastName,
              role: data.user.role,
              avatar: data.user.avatar,
            };
            setUser(userData);
            if (typeof window !== "undefined") {
              try {
                localStorage.setItem("profile", JSON.stringify(userData));
                localStorage.setItem("user", JSON.stringify(userData));
              } catch {}
            }
          }
        } else if (response.status === 401 && !localUser) {
          // Only clear if server explicitly rejected auth and no local profile exists
          setUser(null);
        }
      } catch (error) {
        console.warn("useAuth background check:", error);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();

    // Listen for storage changes across tabs
    if (typeof window !== "undefined") {
      const handleStorageChange = (e: StorageEvent) => {
        if (e.key === "profile" || e.key === "user") {
          if (e.newValue) {
            try {
              setUser(JSON.parse(e.newValue));
            } catch {
              setUser(null);
            }
          } else {
            setUser(null);
          }
        }
      };

      window.addEventListener("storage", handleStorageChange);
      return () => window.removeEventListener("storage", handleStorageChange);
    }
  }, [mounted]);

  const logout = async () => {
    try {
      await fetch("/api/logout", { method: "POST", credentials: "include" });
      if (typeof window !== "undefined") {
        localStorage.removeItem("profile");
        localStorage.removeItem("user");
      }
      setUser(null);
      window.location.href = "/auth/login";
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  return {
    user,
    loading,
    isAuthenticated: !!user,
    logout,
  };
}
