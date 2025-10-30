'use client'

import { useState } from 'react'
import { FileUpload } from '@/components/FileUpload'
import { QueryInterface } from '@/components/QueryInterface'
import { PaperList } from '@/components/PaperList'
import { QueryHistory } from '@/components/QueryHistory'
import { BookOpen, Upload, Search, History } from 'lucide-react'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'query' | 'upload' | 'papers' | 'history'>('query')
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handleUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1)
    setActiveTab('papers')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-primary-600 p-2 rounded-lg">
                <BookOpen className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Research Paper Assistant
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  AI-powered RAG system for academic papers
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="flex items-center space-x-2 px-3 py-1.5 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                <span>Online</span>
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('query')}
              className={`
                flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === 'query'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <Search className="w-5 h-5" />
              <span>Query Papers</span>
            </button>

            <button
              onClick={() => setActiveTab('upload')}
              className={`
                flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === 'upload'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <Upload className="w-5 h-5" />
              <span>Upload Papers</span>
            </button>

            <button
              onClick={() => setActiveTab('papers')}
              className={`
                flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === 'papers'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <BookOpen className="w-5 h-5" />
              <span>My Papers</span>
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`
                flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === 'history'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
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
      <footer className="mt-auto py-6 bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            Built with Next.js, React, FastAPI, Qdrant & Ollama
          </p>
        </div>
      </footer>
    </div>
  )
}
