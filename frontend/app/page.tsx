'use client'

import { useState } from 'react'
import { FileUpload } from '@/components/FileUpload'
import { QueryInterface } from '@/components/QueryInterface'
import { PaperList } from '@/components/PaperList'
import { QueryHistory } from '@/components/QueryHistory'
import { PapersSidebar } from '@/components/PapersSidebar'
import { BookOpen, Upload, Search, History } from 'lucide-react'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'query' | 'upload' | 'papers' | 'history'>('query')
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handleUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1)
    // Don't auto-switch tabs anymore, just refresh sidebar
  }

  const handlePaperClick = (paperId: number) => {
    setActiveTab('papers')
    // Could add logic to highlight/scroll to specific paper
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Left Sidebar with Papers */}
      <PapersSidebar refreshTrigger={refreshTrigger} onPaperClick={handlePaperClick} />

      {/* Main Content Area (shifted right to accommodate sidebar) */}
      <div className="ml-80">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-md shadow-sm border-b border-gray-200/50 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="bg-gradient-to-br from-blue-600 to-indigo-600 p-3 rounded-xl shadow-lg">
                <BookOpen className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  Research Paper Assistant
                </h1>
                <p className="text-sm text-gray-600 mt-1 font-medium">
                  AI-powered RAG system for academic papers
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <span className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 text-green-700 rounded-full text-sm font-semibold shadow-sm">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-lg shadow-green-500/50"></span>
                <span>System Online</span>
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white/70 backdrop-blur-sm border-b border-gray-200/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-2" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('query')}
              className={`
                flex items-center space-x-2 py-4 px-6 border-b-3 font-semibold text-sm transition-all rounded-t-lg
                ${activeTab === 'query'
                  ? 'border-b-4 border-blue-600 text-blue-700 bg-blue-50/50'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50/50'
                }
              `}
            >
              <Search className="w-5 h-5" />
              <span>Query Papers</span>
            </button>

            <button
              onClick={() => setActiveTab('upload')}
              className={`
                flex items-center space-x-2 py-4 px-6 border-b-3 font-semibold text-sm transition-all rounded-t-lg
                ${activeTab === 'upload'
                  ? 'border-b-4 border-blue-600 text-blue-700 bg-blue-50/50'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50/50'
                }
              `}
            >
              <Upload className="w-5 h-5" />
              <span>Upload Papers</span>
            </button>

            <button
              onClick={() => setActiveTab('papers')}
              className={`
                flex items-center space-x-2 py-4 px-6 border-b-3 font-semibold text-sm transition-all rounded-t-lg
                ${activeTab === 'papers'
                  ? 'border-b-4 border-blue-600 text-blue-700 bg-blue-50/50'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50/50'
                }
              `}
            >
              <BookOpen className="w-5 h-5" />
              <span>My Papers</span>
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`
                flex items-center space-x-2 py-4 px-6 border-b-3 font-semibold text-sm transition-all rounded-t-lg
                ${activeTab === 'history'
                  ? 'border-b-4 border-blue-600 text-blue-700 bg-blue-50/50'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50/50'
                }
              `}
            >
              <History className="w-5 h-5" />
              <span>Query History</span>
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'query' && <QueryInterface />}
        {activeTab === 'upload' && <FileUpload onUploadSuccess={handleUploadSuccess} />}
        {activeTab === 'papers' && <PaperList key={refreshTrigger} />}
        {activeTab === 'history' && <QueryHistory />}
      </main>

        {/* Footer */}
        <footer className="mt-auto py-8 bg-gradient-to-r from-gray-50 to-slate-50 border-t border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <p className="text-center text-sm text-gray-600 font-medium">
              Built with <span className="text-blue-600">Next.js</span>, <span className="text-blue-600">FastAPI</span>, <span className="text-blue-600">Qdrant</span> & <span className="text-blue-600">Ollama</span>
            </p>
          </div>
        </footer>
      </div>
    </div>
  )
}
