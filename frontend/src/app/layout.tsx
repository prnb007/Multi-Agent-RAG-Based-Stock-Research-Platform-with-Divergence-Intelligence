import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Divergence Intelligence",
  description: "Multi-agent AI stock research with Divergence Intelligence.",
};

import { TopNavBar } from "@/components/TopNavBar";
import { AnalysisProvider } from "@/context/AnalysisContext";
import { ThemeProvider } from "@/components/ThemeProvider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600&family=Barlow:wght@400;600&family=Instrument+Serif:ital,wght@0,400;1,400&display=swap" rel="stylesheet" />
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0..1,0&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-full bg-background text-on-background font-body-md text-body-md">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
          <AnalysisProvider>
            <TopNavBar />
            {children}
          </AnalysisProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
