import React, { useState, useRef, useEffect } from 'react'
import '../assets/ExpandingTextArea.css'

export default function ExpandingTextarea({ onSubmit }) {
  const [text, setText] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => {
    adjustTextareaHeight()
  }, [text])

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${textarea.scrollHeight}px`
    }
  }

  const handleChange = (e) => {
    setText(e.target.value)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (text.trim()) {
        onSubmit(text)
        setText('')
      }
    }
  }

  return (
    <textarea
      ref={textareaRef}
      value={text}
      onChange={handleChange}
      onKeyDown={handleKeyDown}
      placeholder="Ask a question..."
      className="expanding-textarea"
      rows={1}
    />
  )
}

