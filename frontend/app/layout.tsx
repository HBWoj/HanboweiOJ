import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "HanboweiOJ", description: "面向青少年信息学奥赛学习的教学型 OJ" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="zh-CN"><body>{children}</body></html>; }
