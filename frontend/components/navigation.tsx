"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X, Home, Radar, Upload, CircleHelp, Radio, History } from "lucide-react";

const navItems = [
  { href: "/", label: "Overview", icon: Home },
  { href: "/detection", label: "Detection", icon: Radar },
  { href: "/history", label: "History", icon: History },
];

export function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const pathname = usePathname();

  return (
    <header className="fixed inset-x-0 top-0 z-[60] border-b border-cyan-400/15 bg-slate-950/85 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[1600px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          className="no-underline flex min-w-0 items-center gap-3 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
          aria-label="Varuna home"
        >
          <span className="grid h-9 w-9 shrink-0 place-items-center overflow-hidden rounded-xl border border-cyan-300/35 bg-cyan-400/10 shadow-[0_0_24px_rgba(34,211,238,0.12)]">
            <img src="/logos/varuna-logo.png" alt="" className="h-full w-full object-cover" />
          </span>
          <span className="min-w-0">
            <span className="block truncate font-orbitron text-sm font-bold tracking-[0.12em] text-slate-100">
              VARUNA<span className="text-cyan-300">.AI</span>
            </span>
            <span className="hidden text-[10px] font-space-mono uppercase tracking-[0.12em] text-slate-500 sm:block">
              Ocean intelligence platform
            </span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 rounded-xl border border-white/5 bg-slate-900/60 p-1 md:flex" aria-label="Primary navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`no-underline flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-cyan-400/15 text-cyan-200 shadow-sm ring-1 ring-cyan-300/20"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-100"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2 sm:gap-3">
          <div className="hidden items-center gap-2 rounded-full border border-emerald-400/15 bg-emerald-400/[0.07] px-3 py-1.5 text-[10px] font-space-mono font-bold uppercase tracking-wide text-emerald-300 lg:flex">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-50" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            Live system
          </div>
          <Link
            href="/detection"
            className="no-underline hidden items-center gap-2 rounded-lg bg-cyan-300 px-3.5 py-2 text-xs font-semibold text-slate-950 transition-colors hover:bg-cyan-200 sm:flex"
          >
            <Upload className="h-3.5 w-3.5" />
            Upload sonar
          </Link>
          <Link
            href="/contact"
            aria-label="Contact Varuna"
            className="no-underline hidden rounded-lg p-2 text-slate-400 transition-colors hover:bg-white/5 hover:text-cyan-200 lg:block"
          >
            <CircleHelp className="h-4 w-4" />
          </Link>
          <button
            type="button"
            onClick={() => setIsMenuOpen((open) => !open)}
            className="rounded-lg border border-cyan-300/15 p-2 text-cyan-200 transition-colors hover:bg-cyan-400/10 md:hidden"
            aria-label={isMenuOpen ? "Close navigation" : "Open navigation"}
            aria-expanded={isMenuOpen}
          >
            {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      <div className={`overflow-hidden border-t border-white/5 transition-[max-height,opacity] duration-300 md:hidden ${isMenuOpen ? "max-h-72 opacity-100" : "max-h-0 opacity-0"}`}>
        <nav className="space-y-1 bg-slate-950/95 px-4 py-3" aria-label="Mobile navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsMenuOpen(false)}
                className={`no-underline flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium ${
                  isActive ? "bg-cyan-400/10 text-cyan-200" : "text-slate-300 hover:bg-white/5"
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
          <Link
            href="/detection"
            onClick={() => setIsMenuOpen(false)}
            className="no-underline mt-2 flex items-center justify-center gap-2 rounded-lg bg-cyan-300 px-3 py-3 text-sm font-semibold text-slate-950"
          >
            <Upload className="h-4 w-4" />
            Upload sonar log
          </Link>
          <div className="flex items-center gap-2 px-3 py-2 text-[10px] font-space-mono uppercase tracking-wide text-emerald-300">
            <Radio className="h-3.5 w-3.5" />
            Live system online
          </div>
        </nav>
      </div>
    </header>
  );
}
