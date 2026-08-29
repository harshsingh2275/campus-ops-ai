"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { UserPublic } from "@/lib/auth";

interface AuthContextType {
  user: UserPublic | null;
  role: string | null;
  isAdmin: boolean;
  isStudent: boolean;
  isLoading: boolean;
  loginUser: (user: UserPublic) => void;
  logoutUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const USER_STORAGE_KEY = "campus_ops_user";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(USER_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setUser(parsed);
      }
    } catch {
      // Ignore JSON parse errors from local storage
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loginUser = (userData: UserPublic) => {
    setUser(userData);
    try {
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(userData));
    } catch {
      // localStorage may fail in restricted browser modes
    }
  };

  const logoutUser = async () => {
    setUser(null);
    try {
      localStorage.removeItem(USER_STORAGE_KEY);
      await fetch("/api/auth/logout", { method: "POST" });
    } catch {
      // Ignore network errors during logout
    }
  };

  const role = user?.role || null;
  const isAdmin = role === "admin";
  const isStudent = role === "student" || (!isAdmin && !!user);

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        isAdmin,
        isStudent,
        isLoading,
        loginUser,
        logoutUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
