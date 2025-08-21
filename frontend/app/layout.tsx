import type { Metadata } from "next";
import { Geist, Geist_Mono, Pacifico } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "../contexts/AuthContext";
import { NotificationProvider } from '@/contexts/NotificationProvider';
import { ConfirmProvider } from '@/contexts/ConfirmContext';

const pacifico = Pacifico({
  weight: '400',
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-pacifico',
})

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "征信管理系统",
  description: "征信管理系统",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning={true}>
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${pacifico.variable} antialiased`}
      >
        <AuthProvider>
          <NotificationProvider>
            <ConfirmProvider>
              {children}
            </ConfirmProvider>
          </NotificationProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
