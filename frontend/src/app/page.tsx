"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Loader2 } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const { user, isAdmin, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      if (isAdmin || user?.role === "admin") {
        router.replace("/operations");
      } else {
        router.replace("/student-portal");
      }
    }
  }, [user, isAdmin, isLoading, router]);

  return (
    <div className="min-h-screen bg-[#080b11] flex items-center justify-center text-gray-400 space-x-2">
      <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
      <span className="text-xs">Loading CampusOps AI...</span>
    </div>
  );
}
