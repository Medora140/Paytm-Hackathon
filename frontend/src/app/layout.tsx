import type { Metadata } from "next";
import "./globals.css";
import Navigation from "../components/Navigation";
import DisclaimerBanner from "../components/DisclaimerBanner";

export const metadata: Metadata = {
  title: "Docs Decoded — Understand your policy before you sign or claim",
  description:
    "Grounded AI financial document analyzer backed by real IRDAI and RBI ombudsman dispute data. Detect red flags, compare market benchmarks, and converse with your policy.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-canvas-soft text-ink flex flex-col min-h-screen">
        <DisclaimerBanner />
        <Navigation />
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
          {children}
        </main>
        <footer className="bg-ink text-canvas-soft py-12 px-6 lg:px-8 mt-12 border-t border-ink/20">
          <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-6 text-sm">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-6 h-6 rounded-lg bg-primary text-ink font-black text-xs flex items-center justify-center">
                  W
                </div>
                <span className="font-extrabold text-white text-base tracking-tight">
                  Docs<span className="text-primary font-black">Decoded</span>
                </span>
              </div>
              <p className="text-mute text-xs max-w-md">
                Grounded in empirical IRDAI & RBI insurance dispute patterns. Empowering consumers with radical clause transparency.
              </p>
            </div>
            <div className="flex flex-wrap gap-6 text-xs font-semibold text-canvas-soft/80">
              <span>DPDP Act 2023 Compliant</span>
              <span>Zero Insurer Data Sharing</span>
              <span>AES-256 Encrypted</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
