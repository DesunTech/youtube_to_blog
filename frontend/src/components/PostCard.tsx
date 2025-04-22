import ReactMarkdown from 'react-markdown';

interface PostCardProps {
  content: string;
  onCopy: () => void;
  onDownload: () => void;
}

export default function PostCard({ content, onCopy, onDownload }: PostCardProps) {
  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="p-6">
        <div className="prose max-w-none">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
        <div className="flex justify-end space-x-4">
          <button
            onClick={onCopy}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Copy to Clipboard
          </button>
          <button
            onClick={onDownload}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Download as Markdown
          </button>
        </div>
      </div>
    </div>
  );
}