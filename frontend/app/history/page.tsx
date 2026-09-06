import type { Metadata } from "next";
import DetectionHistory from "@/components/detection-history";

export const metadata: Metadata = {
  title: "Detection History | Varuna",
  description: "Review completed underwater sonar detection scans and reports.",
};

export default function HistoryPage() {
  return <DetectionHistory />;
}
