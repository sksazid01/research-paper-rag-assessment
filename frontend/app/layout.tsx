import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Research Paper RAG Assistant',
  description: 'Intelligent assistant for querying academic research papers',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
