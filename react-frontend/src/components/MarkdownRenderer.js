import React from "react"
import ReactMarkdown from "react-markdown"
import { CodeBlock } from "./CodeBlock"
import { MathJax, MathJaxContext } from "better-react-mathjax";


export function MarkdownRenderer({ children }) {
  return (
    <MathJax>
      <ReactMarkdown
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "")
            return !inline && match ? (
              <CodeBlock language={match[1]} value={String(children).replace(/\n$/, "")} {...props} />
            ) : (
              <code className={className} {...props}>
                {children}
              </code>
            )
          },
        }}
      >
        {children}
      </ReactMarkdown>
    </MathJax>
  )
}

