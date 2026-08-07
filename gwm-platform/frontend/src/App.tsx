import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Layout from './layouts/Layout'
import Dashboard from './pages/Dashboard'
import GenerateDataset from './pages/GenerateDataset'
import GeneratePrompt from './pages/GeneratePrompt'
import Jobs from './pages/Jobs'
import Projects from './pages/Projects'
import DatasetQuality from './pages/DatasetQuality'
import CountryProfiles from './pages/CountryProfiles'
import Geography from './pages/Geography'
import WorldGeneration from './pages/WorldGeneration'
import Login from './pages/Login'
import Register from './pages/Register'
import React from 'react'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 0,
      refetchOnWindowFocus: true,
      retry: 2,
    },
  },
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" />
  return <Layout>{children}</Layout>
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/"          element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/projects"  element={<ProtectedRoute><Projects /></ProtectedRoute>} />
            <Route path="/generate"  element={<ProtectedRoute><GenerateDataset /></ProtectedRoute>} />
            <Route path="/generate-prompt" element={<ProtectedRoute><GeneratePrompt /></ProtectedRoute>} />
            <Route path="/jobs"      element={<ProtectedRoute><Jobs /></ProtectedRoute>} />
            <Route path="/quality"   element={<ProtectedRoute><DatasetQuality /></ProtectedRoute>} />
            <Route path="/countries" element={<ProtectedRoute><CountryProfiles /></ProtectedRoute>} />
             <Route path="/geography" element={<ProtectedRoute><Geography /></ProtectedRoute>} />
             <Route path="/world" element={<ProtectedRoute><WorldGeneration /></ProtectedRoute>} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
