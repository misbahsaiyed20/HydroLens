import type { Metadata } from "next";
import "./globals.css";
import Nav from "@/components/Nav";
import { AuthProvider } from "@/contexts/AuthContext";

export const metadata: Metadata = {
  title: "HydroLens",
  description: "AI-powered environmental intelligence for citizen-reported water observations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 font-sans text-slate-900 antialiased">
        <AuthProvider>
          <Nav />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
