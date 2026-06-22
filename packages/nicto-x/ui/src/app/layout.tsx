import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'NICTO X',
  description: 'Frontier AI Platform',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-nicto-bg text-nicto-text min-h-screen">{children}</body>
    </html>
  )
}
