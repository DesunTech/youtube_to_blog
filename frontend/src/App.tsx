import YouTubeBlogForm from './components/YouTubeBlogForm'

function App() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">YouTube to Blog Generator</h1>
          <p className="mt-2 text-gray-600">Transform any YouTube video into a well-structured blog post</p>
        </div>
        <YouTubeBlogForm />
      </div>
    </div>
  )
}

export default App
