'use client'

import { useState } from 'react'
import axios from 'axios'
import { Upload, Check, AlertCircle } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface FileUploadProps {
  onUploadSuccess?: () => void
}

export function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [files, setFiles] = useState<FileList | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFiles(e.target.files)
    setError(null)
    setSuccess(null)
  }

  const handleUpload = async () => {
    if (!files || files.length === 0) {
      setError('Please select at least one PDF file')
      return
    }

    setUploading(true)
    setError(null)
    setSuccess(null)

    const formData = new FormData()
    Array.from(files).forEach((file) => {
      formData.append('files', file)
    })

    try {
      const response = await axios.post(`${API_URL}/api/papers/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setSuccess(`Successfully uploaded ${files.length} paper(s)!`)
      setFiles(null)
      
      // Reset file input
      const fileInput = document.getElementById('file-upload') as HTMLInputElement
      if (fileInput) fileInput.value = ''

      if (onUploadSuccess) {
        onUploadSuccess()
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload papers. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Upload Research Papers</h2>
        <p className="text-gray-600 mb-6">
          Upload PDF research papers to index them in the RAG system. Papers will be processed, chunked, and vectorized for semantic search.
        </p>

        {/* File Upload Area */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-400 transition-colors">
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <label htmlFor="file-upload" className="cursor-pointer">
            <span className="text-primary-600 hover:text-primary-700 font-medium">
              Click to upload
            </span>
            <span className="text-gray-600"> or drag and drop</span>
            <p className="text-sm text-gray-500 mt-2">PDF files only (max 10MB each)</p>
          </label>
          <input
            id="file-upload"
            type="file"
            multiple
            accept=".pdf"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>

        {/* Selected Files */}
        {files && files.length > 0 && (
          <div className="mt-6 space-y-2">
            <p className="font-medium text-gray-700">Selected files:</p>
            {Array.from(files).map((file, index) => (
              <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded">
                <span className="text-sm text-gray-700">{file.name}</span>
                <span className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
              </div>
            ))}
          </div>
        )}

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={!files || files.length === 0 || uploading}
          className={`
            w-full mt-6 px-6 py-3 rounded-lg font-medium flex items-center justify-center space-x-2
            ${!files || files.length === 0 || uploading
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800'
            }
          `}
        >
          {uploading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              <span>Uploading...</span>
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              <span>Upload Papers</span>
            </>
          )}
        </button>

        {/* Success Message */}
        {success && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start space-x-3">
            <Check className="w-5 h-5 text-green-600 mt-0.5" />
            <div>
              <p className="font-medium text-green-900">Success!</p>
              <p className="text-sm text-green-700 mt-1">{success}</p>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
            <div>
              <p className="font-medium text-red-900">Error</p>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
