import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@services/api'
import { Save } from 'lucide-react'

export function SettingsPage() {
  const [minEv, setMinEv] = useState(5.0)
  const [minConfidence, setMinConfidence] = useState(60.0)

  useQuery({
    queryKey: ['config'],
    queryFn: () => api.getConfig(),
  })

  const mutation = useMutation({
    mutationFn: (newConfig: Record<string, unknown>) => api.updateConfig(newConfig),
  })

  const handleSave = () => {
    mutation.mutate({
      min_ev: minEv,
      min_confidence: minConfidence,
    })
  }

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Settings</h1>

      {/* Analysis Settings */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Analysis Settings</h2>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">
              Minimum EV Threshold (%)
            </label>
            <input
              type="range"
              min="0"
              max="20"
              step="0.5"
              value={minEv}
              onChange={(e) => setMinEv(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-sm text-gray-400 mt-1">
              <span>0%</span>
              <span className="text-primary-500 font-medium">{minEv}%</span>
              <span>20%</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Minimum Confidence (%)
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={minConfidence}
              onChange={(e) => setMinConfidence(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-sm text-gray-400 mt-1">
              <span>0%</span>
              <span className="text-primary-500 font-medium">{minConfidence}%</span>
              <span>100%</span>
            </div>
          </div>
        </div>

        <button
          onClick={handleSave}
          disabled={mutation.isPending}
          className="mt-6 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-600 text-white px-6 py-2 rounded-md font-medium transition-colors flex items-center"
        >
          <Save className="h-4 w-4 mr-2" />
          {mutation.isPending ? 'Saving...' : 'Save Settings'}
        </button>

        {mutation.isSuccess && (
          <p className="mt-2 text-success text-sm">Settings saved successfully!</p>
        )}

        {mutation.isError && (
          <p className="mt-2 text-danger text-sm">Failed to save settings</p>
        )}
      </div>

      {/* API Configuration */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">API Configuration</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">API URL</label>
            <input
              type="text"
              defaultValue={import.meta.env.VITE_API_URL || 'http://localhost:8000'}
              className="w-full bg-gray-700 border border-gray-600 rounded-md px-4 py-2 focus:outline-none focus:border-primary-500"
              readOnly
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">API Key</label>
            <input
              type="password"
              defaultValue={import.meta.env.VITE_API_KEY ? '••••••••' : ''}
              className="w-full bg-gray-700 border border-gray-600 rounded-md px-4 py-2 focus:outline-none focus:border-primary-500"
              readOnly
            />
            <p className="text-xs text-gray-400 mt-1">
              Set VITE_API_KEY in your .env file
            </p>
          </div>
        </div>
      </div>

      {/* About Settings */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Application Info</h2>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Version</span>
            <span>0.2.0</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Backend</span>
            <span>FastAPI (Python 3.11)</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Frontend</span>
            <span>React + Vite + TypeScript</span>
          </div>
        </div>
      </div>
    </div>
  )
}
