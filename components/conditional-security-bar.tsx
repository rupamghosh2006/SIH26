"use client";

import { SecurityClassifiedBar } from "./security-classified-bar";

export function ConditionalSecurityBar() {
  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      <SecurityClassifiedBar />
    </div>
  );
}
