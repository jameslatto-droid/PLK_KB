import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import LayoutShell from "@/components/LayoutShell";
import { PipelineLogProvider } from "@/components/PipelineLogContext";
import { UserContextProvider } from "@/components/UserContext";

export const metadata: Metadata = {
  title: "PLK_KB",
  description: "Visible pipeline UI shell for PLK_KB.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <UserContextProvider>
          <PipelineLogProvider>
            <LayoutShell>{children}</LayoutShell>
          </PipelineLogProvider>
        </UserContextProvider>
      </body>
    </html>
  );
}
