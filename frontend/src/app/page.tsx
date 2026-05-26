import { ScreenerDashboard } from "@/components/ScreenerDashboard";

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-on-background selection:bg-primary/30">
      <ScreenerDashboard />
    </div>
  );
}
