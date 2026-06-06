'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'

interface Props {
  content: string
  className?: string
}

const components: Components = {
  p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  ul: ({ children }) => <ul className="list-disc ps-4 mb-1 space-y-0.5">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal ps-4 mb-1 space-y-0.5">{children}</ol>,
  li: ({ children }) => <li className="leading-snug">{children}</li>,
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="underline underline-offset-2 opacity-80 hover:opacity-100"
    >
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="bg-black/8 rounded px-1 py-0.5 text-xs font-mono">{children}</code>
  ),
  pre: ({ children }) => (
    <pre className="bg-black/8 rounded-lg p-2 text-xs font-mono overflow-x-auto mb-1">
      {children}
    </pre>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-s-2 border-current opacity-70 ps-3 mb-1">
      {children}
    </blockquote>
  ),
  hr: () => <hr className="border-current opacity-20 my-1" />,
}

export default function MarkdownMessage({ content, className }: Props) {
  return (
    <div className={className}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components} skipHtml>
        {content}
      </ReactMarkdown>
    </div>
  )
}
