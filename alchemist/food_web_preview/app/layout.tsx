import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: '菜品 · 3D 预览',
  description: '在网页中旋转、缩放并查看 Alchemist 菜品模型。',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="dark">
      <body>{children}</body>
    </html>
  );
}
