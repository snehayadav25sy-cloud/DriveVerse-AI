import React from 'react'
import Sidebar from '../components/Sidebar'

export default function Layout({ children }: { children?: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-[#0f111a] text-white">
      <Sidebar />
      <div className="flex-1 flex flex-col ml-64 min-h-screen">
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
