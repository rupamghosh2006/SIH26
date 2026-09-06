"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Brain,
  Target,
  BarChart3,
  Zap,
  Shield,
  Lock,
  Radar,
  Waves,
  Cpu,
  Network,
  Satellite,
  ArrowRight,
  Play,
  Sparkles,
  TrendingUp,
  Activity,
  Gauge,
  Monitor,
  CheckCircle2,
  Image as ImageIcon,
  Video,
  Eye,
  Layers,
  ChevronDown,
  Crosshair,
  Globe,
  Anchor,
} from "lucide-react";
import { SonarGridBackground } from "@/components/sonar-grid-background";
import { ImageSlideshow } from "@/components/image-slideshow";
import { TacticalCornerBrackets } from "@/components/tactical-corner-brackets";
import { SecurityFooter } from "@/components/security-classified-bar";
import {
  useScrollAnimation,
  useParallax,
  useMouseParallax,
} from "@/hooks/use-scroll-animation";

function RevealSection({
  children,
  className = "",
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const { ref, isVisible } = useScrollAnimation({ threshold: 0.1 });
  return (
    <div
      ref={ref}
      className={`reveal-up ${isVisible ? "visible" : ""} ${className}`}
      style={{ transitionDelay: `${delay}s` }}
    >
      {children}
    </div>
  );
}

export function HomePageEnhanced() {
  const router = useRouter();
  const [activeFeature, setActiveFeature] = useState(0);
  const [heroLoaded, setHeroLoaded] = useState(false);
  const parallaxOffset = useParallax(0.3);
  const mouseOffset = useMouseParallax(0.015);

  const deepSeaImages = [
    "/deep-sea-images/security1.jpg",
    "/deep-sea-images/security2.jpg",
    "/deep-sea-images/security3.jpg",
    "/deep-sea-images/security4.jpg",
  ];

  useEffect(() => {
    // Stagger hero entrance
    const timer = setTimeout(() => setHeroLoaded(true), 100);

    // Auto-rotate features
    const featureInterval = setInterval(() => {
      setActiveFeature((prev) => (prev + 1) % 3);
    }, 4000);

    return () => {
      clearTimeout(timer);
      clearInterval(featureInterval);
    };
  }, []);

  const features = [
    {
      icon: Target,
      title: "YOLOv8 & U-Net Debris Detection",
      description:
        "Automated detection and segmentation for ghost nets / entangled debris, pipes and cylinders, shipwrecks, and unknown seafloor anomalies",
      color: "emerald",
      highlights: ["Ghost Nets", "Pipe Cylinders", "Shipwreck Frags", "Unknown Anomaly"],
      href: "/detection",
    },
    {
      icon: Brain,
      title: "Acoustic Shadow & Noise Filter",
      description:
        "Physics-based acoustic shadow validation and speckle noise suppression minimizing false alarms from rock clusters and sand ripples",
      color: "cyan",
      highlights: ["Shadow Physics", "Speckle Reduction", "0-100% Score"],
      href: "/detection",
    },
    {
      icon: BarChart3,
      title: "Geotagged Anomaly Reports",
      description:
        "Parses sonar ping headers and metadata to generate structured JSON & CSV reports with precise latitude, longitude, and dimensions",
      color: "blue",
      highlights: ["JSON/CSV Export", "Lat/Lon Geotag", "Ping Tracking"],
      href: "/analytics",
    },
  ];

  const capabilities = [
    { icon: Target, title: "Ghost Net AI", desc: "ALDFG detection" },
    { icon: Shield, title: "Shadow Validation", desc: "Acoustic physics" },
    { icon: Radar, title: "Side-Scan Sonar", desc: "Waterfall sweeps" },
    { icon: Cpu, title: "Edge Ready", desc: "AUV onboard" },
    { icon: Network, title: "Geotagging", desc: "Lat/Lon coordinates" },
    { icon: Layers, title: "Noise Filter", desc: "Speckle suppression" },
  ];

  const techStack = [
    { icon: Brain, label: "YOLOv8", desc: "Debris Detection" },
    { icon: Globe, label: "Next.js 14", desc: "Tactical Dashboard" },
    { icon: Cpu, label: "FastAPI / ONNX", desc: "Edge Inference" },
  ];

  const validationMetrics = [
    { label: "mAP@50", value: "95.9%", detail: "Detection accuracy" },
    { label: "mAP@50–95", value: "85.2%", detail: "Across IoU thresholds" },
    { label: "Precision", value: "86.7%", detail: "Positive predictions" },
    { label: "Recall", value: "91.8%", detail: "Targets recovered" },
  ];

  return (
    <main className="relative overflow-hidden">
      <SonarGridBackground />

      {/* ═══════════════════════════════════════════════ */}
      {/* HERO SECTION - Cinematic Entrance                */}
      {/* ═══════════════════════════════════════════════ */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-28">
        {/* Parallax Background Orbs */}
        <div
          className="absolute inset-0 opacity-15 pointer-events-none"
          style={{
            transform: `translateY(${parallaxOffset * 0.5}px) translateX(${mouseOffset.x}px)`,
          }}
        >
          <div className="absolute top-20 left-1/4 w-[500px] h-[500px] bg-cyan-500 rounded-full blur-[120px]" />
          <div className="absolute bottom-1/4 right-1/3 w-[400px] h-[400px] bg-blue-500 rounded-full blur-[100px]" />
          <div className="absolute top-1/2 left-1/2 w-[300px] h-[300px] bg-emerald-500 rounded-full blur-[80px]" />
        </div>

        {/* Floating Particles */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(15)].map((_, i) => (
            <div
              key={i}
              className="absolute w-1.5 h-1.5 bg-cyan-400/20 rounded-full animate-float"
              style={{
                left: `${(i * 7 + 3) % 100}%`,
                top: `${(i * 13 + 5) % 100}%`,
                animationDelay: `${i * 0.7}s`,
                animationDuration: `${6 + (i % 4)}s`,
              }}
            />
          ))}
        </div>

        {/* Main Hero Content */}
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* Left Side - Text */}
            <div className="text-left space-y-6 flex flex-col items-start">
              {/* Tactical Badge */}
              <div
                className={`transition-all duration-700 ${heroLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
              >
                <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-cyan-500/10 border border-cyan-500/20 rounded-full mb-3">
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                  <span className="text-[11px] font-space-mono text-cyan-300/80 font-bold uppercase tracking-[0.15em]">
                    Sonar Debris Intelligence Active
                  </span>
                </div>
              </div>

              {/* Main Title */}
              <div
                className={`w-full transition-all duration-700 delay-150 ${heroLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
              >
                <h1 className="text-5xl md:text-7xl lg:text-[5.5rem] font-black leading-[0.95] mb-4 text-left font-orbitron">
                  <span className="block gradient-text-ocean animate-gradient bg-[length:200%_200%] tracking-normal">
                    VARUNA AI
                  </span>
                  <span className="block text-2xl md:text-4xl lg:text-5xl mt-3 text-white/90 font-orbitron tracking-normal">
                    SONAR DEBRIS INTELLIGENCE
                  </span>
                </h1>
              </div>

              {/* Subtitle */}
              <div
                className={`w-full transition-all duration-700 delay-300 ${heroLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
              >
                <p className="text-base md:text-lg text-cyan-200/70 max-w-xl text-left leading-relaxed font-space-mono">
                  Automated underwater debris and anomaly detection from side-scan sonar: ghost nets / entangled debris, pipes and cylinders, shipwrecks, and unknown seafloor anomalies.
                </p>
              </div>

              {/* Feature Pills */}
              <div
                className={`flex flex-wrap gap-2.5 justify-start transition-all duration-700 delay-[450ms] ${heroLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
              >
                {[
                  { icon: Zap, label: "Real-Time", color: "cyan" },
                  { icon: Shield, label: "Shadow Validated", color: "blue" },
                  { icon: Crosshair, label: "YOLOv8 AI", color: "emerald" },
                ].map((pill, i) => (
                  <div
                    key={i}
                    className={`group flex items-center gap-2 px-3.5 py-1.5 rounded-full border transition-all duration-300 cursor-default hover-glow ${
                      pill.color === "cyan"
                        ? "bg-cyan-500/5 border-cyan-500/20 hover:bg-cyan-500/15"
                        : pill.color === "blue"
                          ? "bg-blue-500/5 border-blue-500/20 hover:bg-blue-500/15"
                          : "bg-emerald-500/5 border-emerald-500/20 hover:bg-emerald-500/15"
                    }`}
                  >
                    <pill.icon
                      className={`w-3.5 h-3.5 group-hover:scale-110 transition-transform ${
                        pill.color === "cyan"
                          ? "text-cyan-400"
                          : pill.color === "blue"
                            ? "text-blue-400"
                            : "text-emerald-400"
                      }`}
                    />
                    <span
                      className={`text-xs font-space-mono font-bold ${
                        pill.color === "cyan"
                          ? "text-cyan-300/80"
                          : pill.color === "blue"
                            ? "text-blue-300/80"
                            : "text-emerald-300/80"
                      }`}
                    >
                      {pill.label}
                    </span>
                  </div>
                ))}
              </div>

              {/* CTA Buttons */}
              <div
                className={`flex flex-col sm:flex-row gap-3.5 justify-start items-start sm:items-center transition-all duration-700 delay-[600ms] ${heroLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
              >
                <Link href="/detection">
                  <button className="group relative px-7 py-3.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-black text-sm rounded-xl shadow-2xl shadow-cyan-500/30 hover:shadow-cyan-500/50 transition-all duration-300 hover:scale-[1.03] font-orbitron tracking-wider overflow-hidden cursor-pointer">
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/15 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                    <span className="relative z-10 flex items-center gap-2">
                      <Target className="w-4 h-4" />
                      LAUNCH DEBRIS DETECTION
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </span>
                  </button>
                </Link>
              </div>

              {/* Tech Stack Mini Row */}
              <div
                className={`transition-all duration-700 delay-[750ms] ${heroLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
              >
                <div className="flex items-center gap-4 justify-start pt-2">
                  <span className="text-[9px] font-space-mono text-cyan-400/40 uppercase tracking-widest">
                    Powered by
                  </span>
                  <div className="flex items-center gap-3">
                    {techStack.map((tech, i) => (
                      <div
                        key={i}
                        className="group flex items-center gap-1.5 cursor-default"
                        title={tech.desc}
                      >
                        <tech.icon className="w-3.5 h-3.5 text-cyan-500/40 group-hover:text-cyan-400 transition-colors" />
                        <span className="text-[10px] font-space-mono text-cyan-300/30 group-hover:text-cyan-300/70 transition-colors font-bold">
                          {tech.label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Right Side - Visual */}
            <div
              className={`relative space-y-6 transition-all duration-1000 delay-500 ${heroLoaded ? "opacity-100 translate-x-0" : "opacity-0 translate-x-12"}`}
            >
              <div className="relative group">
                <TacticalCornerBrackets
                  className="w-full h-full"
                  color="cyan"
                />

                {/* Main Image Card */}
                <div className="relative w-full h-80 lg:h-[460px] rounded-xl overflow-hidden border border-cyan-500/30 glass-card shadow-2xl shadow-cyan-500/10 group-hover:shadow-cyan-500/25 transition-all duration-700 group-hover:border-cyan-400/50">
                  <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-transparent to-blue-500/5" />
                  <ImageSlideshow
                    images={deepSeaImages}
                    autoSlide={true}
                    slideInterval={5000}
                  />

                  {/* Pipeline Overlay */}
                  <div className="absolute bottom-0 left-0 right-0 z-10 bg-gradient-to-t from-slate-950 via-slate-950/80 to-transparent p-5">
                    <div className="space-y-2">
                      <h3 className="font-orbitron font-bold text-white text-xs tracking-[0.15em] text-glow-cyan">
                        AI DEBRIS DETECTION PIPELINE
                      </h3>
                      <div className="flex items-center justify-between text-[10px] font-space-mono text-cyan-300 space-x-1.5">
                        <span className="px-2 py-0.5 rounded bg-cyan-500/15 border border-cyan-500/30">
                          SSS SCAN
                        </span>
                        <ArrowRight className="w-3 h-3 text-cyan-500/40" />
                        <span className="px-2 py-0.5 rounded bg-blue-500/15 border border-blue-500/30">
                          FILTER NOISE
                        </span>
                        <ArrowRight className="w-3 h-3 text-cyan-500/40" />
                        <span className="px-2 py-0.5 rounded bg-emerald-500/15 border border-emerald-500/30">
                          YOLOv8 DETECT
                        </span>
                        <ArrowRight className="w-3 h-3 text-cyan-500/40" />
                        <span className="px-2 py-0.5 rounded bg-amber-500/15 border border-amber-500/30">
                          GEOTAG & AUDIT
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* HUD Scanning Effect */}
                  <div className="absolute inset-0 pointer-events-none">
                    <div
                      className="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-500/[0.03] to-transparent animate-scan"
                      style={{ animationDuration: "3s" }}
                    />
                  </div>
                </div>
              </div>

              {/* Mini Capability Cards */}
              <div className="grid grid-cols-3 gap-3">
                {[
                  { icon: Zap, label: "Real-Time", sub: "< 50ms" },
                  { icon: Shield, label: "Secure", sub: "AES-256" },
                  { icon: Radar, label: "Active", sub: "24/7" },
                ].map((item, i) => (
                  <div
                    key={i}
                    className="group glass-card rounded-lg p-3 text-center hover-lift cursor-default"
                  >
                    <item.icon className="w-5 h-5 text-cyan-400/70 mx-auto mb-1.5 group-hover:text-cyan-300 group-hover:scale-110 transition-all" />
                    <div className="text-[10px] text-cyan-300/70 font-space-mono uppercase tracking-wider font-bold">
                      {item.label}
                    </div>
                    <div className="text-[9px] text-cyan-300/40 font-space-mono mt-0.5">
                      {item.sub}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div
          className={`absolute bottom-8 left-1/2 transform -translate-x-1/2 transition-all duration-700 delay-[1200ms] ${heroLoaded ? "opacity-100" : "opacity-0"}`}
        >
          <div className="flex flex-col items-center gap-2 animate-bounce">
            <span className="text-[8px] font-space-mono text-cyan-400/40 uppercase tracking-[0.2em]">
              Scroll
            </span>
            <ChevronDown className="w-4 h-4 text-cyan-400/30" />
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════ */}
      {/* FEATURES SECTION - Scroll Revealed              */}
      {/* ═══════════════════════════════════════════════ */}
      <section className="relative py-24 lg:py-32 bg-gradient-to-b from-slate-950 via-blue-950/50 to-slate-950 overflow-hidden">
        {/* Section Divider */}
        <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <RevealSection>
            <div className="text-center mb-16">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-cyan-500/5 border border-cyan-500/15 rounded-full mb-6">
                <Sparkles className="w-3 h-3 text-cyan-400/60" />
                <span className="text-[10px] font-space-mono text-cyan-300/60 font-bold uppercase tracking-widest">
                  Core Features
                </span>
              </div>
              <h2 className="text-4xl md:text-6xl font-black mb-4 gradient-text-ocean font-orbitron">
                POWERFUL FEATURES
              </h2>
              <p className="text-base text-cyan-200/50 max-w-2xl mx-auto font-space-mono">
                Cutting-edge AI technology for automated marine debris detection & seafloor surveys
              </p>
            </div>
          </RevealSection>

          {/* Premium Feature Cards */}
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            {features.map((feature, index) => (
              <RevealSection key={index} delay={index * 0.15}>
                <Link href={feature.href}>
                  <div
                    onMouseEnter={() => setActiveFeature(index)}
                    className={`group relative cursor-pointer h-full transition-all duration-700 transform ${
                      activeFeature === index
                        ? "scale-105"
                        : "hover:scale-102"
                    }`}
                  >
                    {/* Premium Card Background */}
                    <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-slate-900/60 via-slate-900/40 to-slate-900/20 backdrop-blur-xl border border-cyan-500/30 group-hover:border-cyan-400/60 transition-all duration-500" />
                    
                    {/* Animated gradient border */}
                    <div className={`absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${
                      feature.color === "cyan"
                        ? "bg-gradient-to-br from-cyan-500/20 to-transparent"
                        : feature.color === "emerald"
                          ? "bg-gradient-to-br from-emerald-500/20 to-transparent"
                          : "bg-gradient-to-br from-blue-500/20 to-transparent"
                    }`} />

                    {/* Card Content */}
                    <div className="relative z-10 p-8 h-full flex flex-col space-y-6">
                      {/* Icon Container - Premium */}
                      <div className={`w-16 h-16 rounded-xl flex items-center justify-center border-2 transition-all duration-300 group-hover:scale-110 ${
                        activeFeature === index
                          ? "scale-110"
                          : ""
                      } ${
                        feature.color === "cyan"
                          ? "bg-gradient-to-br from-cyan-500/20 to-cyan-600/5 border-cyan-500/50 group-hover:border-cyan-400/80 group-hover:shadow-lg group-hover:shadow-cyan-500/30"
                          : feature.color === "emerald"
                            ? "bg-gradient-to-br from-emerald-500/20 to-emerald-600/5 border-emerald-500/50 group-hover:border-emerald-400/80 group-hover:shadow-lg group-hover:shadow-emerald-500/30"
                            : "bg-gradient-to-br from-blue-500/20 to-blue-600/5 border-blue-500/50 group-hover:border-blue-400/80 group-hover:shadow-lg group-hover:shadow-blue-500/30"
                      }`}>
                        <feature.icon
                          className={`w-8 h-8 group-hover:scale-125 transition-transform duration-300 ${
                            feature.color === "cyan"
                              ? "text-cyan-300"
                              : feature.color === "emerald"
                                ? "text-emerald-300"
                                : "text-blue-300"
                          }`}
                        />
                      </div>

                      {/* Title & Description */}
                      <div>
                        <h3 className={`text-xl font-orbitron font-bold mb-2 group-hover:text-cyan-100 transition-colors duration-300 ${
                          feature.color === "cyan"
                            ? "text-cyan-200"
                            : feature.color === "emerald"
                              ? "text-emerald-200"
                              : "text-blue-200"
                        }`}>
                          {feature.title}
                        </h3>
                        <p className="text-sm text-cyan-200/60 group-hover:text-cyan-200/80 transition-colors font-space-mono leading-relaxed">
                          {feature.description}
                        </p>
                      </div>

                      {/* Tags */}
                      <div className="flex flex-wrap gap-2 mt-auto pt-4 border-t border-cyan-500/10">
                        {feature.highlights.map((h, idx) => (
                          <span
                            key={idx}
                            className={`px-3 py-1.5 rounded-lg text-xs font-space-mono font-bold transition-all duration-300 group-hover:scale-105 ${
                              feature.color === "cyan"
                                ? "bg-gradient-to-r from-cyan-500/20 to-cyan-600/10 text-cyan-300 border border-cyan-500/30 group-hover:border-cyan-400/60 group-hover:bg-cyan-500/30"
                                : feature.color === "emerald"
                                  ? "bg-gradient-to-r from-emerald-500/20 to-emerald-600/10 text-emerald-300 border border-emerald-500/30 group-hover:border-emerald-400/60 group-hover:bg-emerald-500/30"
                                  : "bg-gradient-to-r from-blue-500/20 to-blue-600/10 text-blue-300 border border-blue-500/30 group-hover:border-blue-400/60 group-hover:bg-blue-500/30"
                            }`}
                          >
                            {h}
                          </span>
                        ))}
                      </div>

                      {/* Premium CTA Arrow */}
                      <div className="mt-auto pt-4 flex items-center text-cyan-400 group-hover:text-cyan-300 transition-colors">
                        <span className="text-xs font-orbitron font-bold uppercase tracking-wider">Explore</span>
                        <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                      </div>
                    </div>
                  </div>
                </Link>
              </RevealSection>
            ))}
          </div>

          {/* Capabilities Grid */}
          <RevealSection delay={0.2}>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {capabilities.map((cap, index) => (
                <div
                  key={index}
                  className="group glass-light rounded-xl p-4 hover:border-cyan-400/30 transition-all duration-300 hover-lift text-center"
                >
                  <cap.icon className="w-6 h-6 text-cyan-400/50 mx-auto mb-2 group-hover:text-cyan-300 group-hover:scale-110 transition-all" />
                  <h4 className="text-[11px] font-bold text-white/80 mb-0.5 font-orbitron">
                    {cap.title}
                  </h4>
                  <p className="text-[10px] text-cyan-200/40 font-space-mono">
                    {cap.desc}
                  </p>
                </div>
              ))}
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════ */}
      {/* MODEL PERFORMANCE SECTION                       */}
      {/* ═══════════════════════════════════════════════ */}
      <section id="model-performance" className="relative overflow-hidden bg-gradient-to-b from-slate-950 via-cyan-950/25 to-slate-950 py-24 lg:py-28">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-400/30 to-transparent" />
        <div className="absolute left-1/2 top-1/2 h-96 w-96 -translate-x-1/2 -translate-y-1/2 rounded-full bg-emerald-400/[0.05] blur-[120px]" />

        <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <RevealSection>
            <div className="mx-auto mb-12 max-w-3xl text-center">
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/[0.06] px-3 py-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-300" />
                <span className="font-space-mono text-[10px] font-bold uppercase tracking-widest text-emerald-200/80">
                  Validated results
                </span>
              </div>
              <h2 className="font-orbitron text-4xl font-black gradient-text-ocean md:text-5xl">
                MODEL PERFORMANCE
              </h2>
              <p className="mt-4 text-base font-space-mono text-cyan-100/55">
                Measured performance from a clean, leak-free validation split.
              </p>
            </div>
          </RevealSection>

          <RevealSection delay={0.1}>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {validationMetrics.map((metric, index) => (
                <div key={metric.label} className="group relative overflow-hidden rounded-2xl border border-cyan-400/15 bg-slate-900/60 p-5 backdrop-blur-xl transition-colors duration-300 hover:border-emerald-300/40">
                  <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-300/50 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                  <div className="mb-5 flex items-center justify-between">
                    <span className="font-space-mono text-[10px] font-bold uppercase tracking-widest text-cyan-200/55">
                      {metric.label}
                    </span>
                    <Gauge className={`h-4 w-4 ${index % 2 === 0 ? "text-cyan-300" : "text-emerald-300"}`} />
                  </div>
                  <div className="font-orbitron text-3xl font-black text-emerald-300">
                    {metric.value}
                  </div>
                  <p className="mt-2 font-space-mono text-xs text-slate-400">{metric.detail}</p>
                </div>
              ))}
            </div>
          </RevealSection>

          <RevealSection delay={0.2}>
            <p className="mx-auto mt-7 max-w-4xl rounded-xl border border-cyan-400/10 bg-slate-950/40 px-5 py-4 text-center font-space-mono text-sm leading-relaxed text-cyan-100/65">
              Validated on a clean, leak-free split of real AUV sonar imagery (AI4Shipwrecks, NOMBO/MILCO) and physics-modeled synthetic sonar for ghost net detection.
            </p>
          </RevealSection>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════ */}
      {/* SOLUTIONS SECTION                               */}
      {/* ═══════════════════════════════════════════════ */}
      <section className="relative py-24 lg:py-32 bg-gradient-to-br from-slate-950 via-blue-950/30 to-slate-950 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-blue-500/20 to-transparent" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <RevealSection>
            <div className="text-center mb-16">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-500/5 border border-blue-500/15 rounded-full mb-6">
                <Anchor className="w-3 h-3 text-blue-400/60" />
                <span className="text-[10px] font-space-mono text-blue-300/60 font-bold uppercase tracking-widest">
                  Solutions
                </span>
              </div>
              <h2 className="text-4xl md:text-6xl font-black mb-4 gradient-text-ocean font-orbitron">
                AI-POWERED SOLUTIONS
              </h2>
              <p className="text-base text-cyan-200/50 max-w-2xl mx-auto font-space-mono">
                Debris detection and geotagged reporting for side-scan sonar surveys.
              </p>
            </div>
          </RevealSection>

          <div className="max-w-2xl mx-auto">
            {/* Detection Card */}
            <RevealSection delay={0.1}>
              <Link href="/detection" className="block h-full">
                <div className="group relative glass-card rounded-2xl p-7 hover:border-emerald-400/50 transition-all duration-500 hover-lift overflow-hidden h-full">
                  <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl" />

                  <div className="relative z-10">
                    <div className="w-16 h-16 mb-5 bg-gradient-to-br from-emerald-500/15 to-cyan-500/15 rounded-xl flex items-center justify-center group-hover:scale-110 transition-all duration-300 border border-emerald-500/20">
                      <Target className="w-8 h-8 text-emerald-400" />
                    </div>

                    <h3 className="text-2xl font-black text-white mb-3 font-orbitron group-hover:text-emerald-100 transition-colors">
                      DEBRIS DETECTION
                    </h3>
                    <p className="text-sm text-cyan-200/50 mb-5 leading-relaxed">
                      YOLOv8 detects ghost nets / entangled debris, pipe or cylinder targets, shipwrecks, and unknown seafloor anomalies.
                    </p>

                    <div className="space-y-2 mb-5">
                      {[
                        "YOLOv8 Detection",
                        "Acoustic Shadow Verification",
                        "4 Debris Categories",
                        "Ecological Risk Assessment",
                      ].map((f, i) => (
                        <div
                          key={i}
                          className="flex items-center text-emerald-400/70 group-hover:text-emerald-300/80 transition-colors"
                        >
                          <CheckCircle2 className="w-4 h-4 mr-2.5 flex-shrink-0" />
                          <span className="text-sm font-space-mono">{f}</span>
                        </div>
                      ))}
                    </div>

                    <div className="flex items-center text-emerald-400/60 group-hover:text-emerald-300 font-bold font-orbitron text-sm tracking-wider transition-colors">
                      <span>Explore</span>
                      <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1.5 transition-transform" />
                    </div>
                  </div>
                </div>
              </Link>
            </RevealSection>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════ */}
      {/* CTA FOOTER SECTION                              */}
      {/* ═══════════════════════════════════════════════ */}
      <section className="relative py-24 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-cyan-950/20 to-transparent" />

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <RevealSection>
            <div className="text-center">
              <h2 className="text-3xl md:text-5xl font-black mb-4 text-white font-orbitron">
                Ready to <span className="gradient-text-cyan">Restore</span> the
                Ocean?
              </h2>
              <p className="text-base text-cyan-200/40 max-w-xl mx-auto mb-8 font-space-mono">
                Deploy advanced AI for automated underwater marine debris detection,
                side-scan sonar image processing, and seafloor cleanup intelligence.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Link href="/detection">
                  <button className="group relative px-8 py-3.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-black text-sm rounded-xl shadow-2xl shadow-cyan-500/30 hover:shadow-cyan-500/50 transition-all duration-300 hover:scale-[1.03] font-orbitron tracking-wider overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                    <span className="relative z-10 flex items-center gap-2">
                      <Target className="w-4 h-4" />
                      LAUNCH DEBRIS DETECTION
                    </span>
                  </button>
                </Link>
                <Link href="/contact">
                  <button className="px-8 py-3.5 glass-card hover:border-cyan-400/30 text-cyan-300 hover:text-cyan-200 font-black text-sm rounded-xl transition-all duration-300 hover:scale-[1.03] font-orbitron tracking-wider">
                    GET IN TOUCH
                  </button>
                </Link>
              </div>
            </div>
          </RevealSection>
        </div>
      </section>

      {/* Security Footer */}
      <SecurityFooter />
    </main>
  );
}
