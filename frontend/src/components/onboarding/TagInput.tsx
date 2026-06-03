'use client'

import { useState, type KeyboardEvent } from 'react'
import { X } from 'lucide-react'
import { cn } from '@/lib/cn'

interface TagInputProps {
  value: string[]
  onChange: (v: string[]) => void
  placeholder?: string
  addLabel?: string
  className?: string
}

export default function TagInput({ value, onChange, placeholder, addLabel = 'Add', className }: TagInputProps) {
  const [input, setInput] = useState('')

  function add() {
    const trimmed = input.trim()
    if (trimmed && !value.includes(trimmed)) {
      onChange([...value, trimmed])
    }
    setInput('')
  }

  function remove(item: string) {
    onChange(value.filter((v) => v !== item))
  }

  function onKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault()
      add()
    }
  }

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          placeholder={placeholder}
          className="flex-1 px-3 py-2.5 rounded-xl border border-line bg-elevated text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
        />
        <button
          type="button"
          onClick={add}
          disabled={!input.trim()}
          className="px-4 py-2.5 rounded-xl bg-brand-muted text-brand text-sm font-medium disabled:opacity-40 transition-opacity shrink-0"
        >
          {addLabel}
        </button>
      </div>

      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map((item) => (
            <span
              key={item}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-muted text-brand text-sm"
            >
              {item}
              <button
                type="button"
                onClick={() => remove(item)}
                className="w-4 h-4 flex items-center justify-center rounded-full hover:bg-brand hover:text-white transition-colors"
                aria-label="Remove"
              >
                <X size={10} />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
