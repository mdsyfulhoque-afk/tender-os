import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "TenderOS · Evidence-led decisions",
  description:
    "Owner-controlled tender readiness workspace. Local development pilot.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
