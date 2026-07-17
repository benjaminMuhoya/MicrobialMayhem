import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "./progression.css";
import "./resilience.css";
import "./accessibility.css";
import "./performance.css";
import { PwaRuntime } from "./components/PwaRuntime";

/* eslint-disable @next/next/no-css-tags -- the static mobile export packages this offline scene stylesheet */

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Microbial Mayhem — A Microscopic Battle to Survive",
  description: "A vibrant, biologically grounded microbial battle game for the web.",
  manifest: "/manifest.webmanifest",
  themeColor: "#071a16",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head><link rel="stylesheet" href="./colony.css" /><link rel="stylesheet" href="./environment.css" /><link rel="stylesheet" href="./battle.css" /><link rel="stylesheet" href="./tutorial.css" /><link rel="stylesheet" href="./results.css" /></head>
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <PwaRuntime />{children}
      </body>
    </html>
  );
}
