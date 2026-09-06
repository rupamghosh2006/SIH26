import type React from "react";
import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import { Orbitron, Space_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";
import { Suspense } from "react";
import { ConditionalNavigation } from "@/components/conditional-navigation";
import { Chatbot } from "@/components/chatbot";
import { PageTransition } from "@/components/page-transition";
import { Toaster } from "sonner";

import "./globals.css";
import "leaflet/dist/leaflet.css";

const orbitron = Orbitron({
  subsets: ["latin"],
  variable: "--font-orbitron",
  weight: ["400", "700", "900"],
});

const spaceMono = Space_Mono({
  subsets: ["latin"],
  variable: "--font-space-mono",
  weight: ["400", "700"],
});

export const metadata: Metadata = {
  title: "Varuna - Underwater Marine Debris & Anomaly Detection System",
  description:
    "Advanced AI-powered platform for deep-sea underwater marine debris detection (ghost nets, shipwrecks, pipe cylinders) using side-scan sonar, water quality monitoring, and conservation insights using cutting-edge machine learning and environmental DNA analysis.",
  keywords:
    "marine debris detection, ghost nets, side-scan sonar, YOLOv8, acoustic shadow validation, Varuna, AI, environmental DNA, water quality, conservation, marine biology",
  authors: [{ name: "AI-Driven Biodiversity Research Team" }],
  openGraph: {
    title: "Varuna - Underwater Marine Debris & Anomaly Detection System",
    description:
      "Revolutionary AI platform for marine conservation and species discovery",
    type: "website",
  },
  icons: {
    icon: [
      { url: "/logos/varuna-logo.png", href: "/logos/varuna-logo.png" },
      { url: "/favicon.ico", href: "/favicon.ico" },
      { url: "/icon.png", href: "/icon.png" }
    ],
    shortcut: "/logos/varuna-logo.png",
    apple: "/logos/varuna-logo.png",
  },
  generator: "v0.app",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" type="image/png" href="/logos/varuna-logo.png?v=2" />
        <link rel="shortcut icon" href="/logos/varuna-logo.png?v=2" />
        <link rel="apple-touch-icon" href="/logos/varuna-logo.png?v=2" />
      </head>
      <body
        className={`font-body ${GeistSans.variable} ${GeistMono.variable} ${orbitron.variable} ${spaceMono.variable}`}
      >
        <ConditionalNavigation />
        <Suspense
          fallback={
            <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-cyan-950" />
          }
        >
          <PageTransition>{children}</PageTransition>
        </Suspense>

        <Chatbot />
        {/* <VarunaVoiceAssistant /> */}
        <Toaster richColors position="top-right" theme="dark" />

        <Analytics />
      </body>
    </html>
  );
}
