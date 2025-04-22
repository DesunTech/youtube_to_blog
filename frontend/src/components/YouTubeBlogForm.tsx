import { useState } from 'react';
import axios from 'axios';
import PostCard from './PostCard';

interface BlogOptions {
  audience: 'beginners' | 'intermediate' | 'experts' | 'general';
  tone: 'formal' | 'conversational' | 'professional' | 'enthusiastic' | 'technical';
  output_format: 'markdown' | 'html';
}

export default function YouTubeBlogForm() {
  const [url, setUrl] = useState('');
  const [options, setOptions] = useState<BlogOptions>({
    audience: 'general',
    tone: 'professional',
    output_format: 'markdown'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [blogPost, setBlogPost] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setBlogPost('');

    try {
      // Extract video ID from URL
      const videoId = url.split('v=')[1]?.split('&')[0];
      if (!videoId) {
        throw new Error('Invalid YouTube URL');
      }

      const response = await axios.post(`http://localhost:8000/process-video/?video_id=${videoId}&output_format=${options.output_format}&tone=${options.tone}&audience=${options.audience}`);
      setBlogPost(response.data.blog_post);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error details:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(blogPost);
  };

  const handleDownload = () => {
    const blob = new Blob([blogPost], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'blog-post.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* YouTube URL Input */}
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-gray-700">
            YouTube URL
          </label>
          <input
            type="url"
            id="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            required
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>

        {/* Target Audience Selection */}
        <div>
          <label htmlFor="audience" className="block text-sm font-medium text-gray-700">
            Target Audience
          </label>
          <select
            id="audience"
            value={options.audience}
            onChange={(e) => setOptions({ ...options, audience: e.target.value as BlogOptions['audience'] })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          >
            <option value="beginners">Beginners</option>
            <option value="intermediate">Intermediate</option>
            <option value="experts">Experts</option>
            <option value="general">General Audience</option>
          </select>
        </div>

        {/* Tone Selection */}
        <div>
          <label htmlFor="tone" className="block text-sm font-medium text-gray-700">
            Writing Tone
          </label>
          <select
            id="tone"
            value={options.tone}
            onChange={(e) => setOptions({ ...options, tone: e.target.value as BlogOptions['tone'] })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          >
            <option value="formal">Formal</option>
            <option value="conversational">Conversational</option>
            <option value="professional">Professional</option>
            <option value="enthusiastic">Enthusiastic</option>
            <option value="technical">Technical</option>
          </select>
        </div>

        {/* Output Format Selection */}
        <div>
          <label htmlFor="output_format" className="block text-sm font-medium text-gray-700">
            Output Format
          </label>
          <select
            id="output_format"
            value={options.output_format}
            onChange={(e) => setOptions({ ...options, output_format: e.target.value as BlogOptions['output_format'] })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          >
            <option value="markdown">Markdown</option>
            <option value="html">HTML</option>
          </select>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
        >
          {loading ? 'Processing...' : 'Generate Blog Post'}
        </button>
      </form>

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Blog Post Display */}
      {blogPost && (
        <div className="mt-8">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Generated Blog Post</h2>
          <PostCard
            content={blogPost}
            onCopy={handleCopy}
            onDownload={handleDownload}
          />
        </div>
      )}
    </div>
  );
}