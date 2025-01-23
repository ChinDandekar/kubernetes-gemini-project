import React, { useState } from "react"
import "../assets/TokenProgressBar.css"

const TokenProgressBar = ({ tokensUsed, contextWindow }) => {
  const [showTooltip, setShowTooltip] = useState(false)
  const percentage = (tokensUsed / contextWindow) * 100

  return (
    <div
      className="token-progress-container"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div className="token-progress-bar" style={{ width: `${percentage}%` }}></div>
      {showTooltip && (
        <div className="token-progress-tooltip">
          {tokensUsed.toLocaleString()} / {contextWindow.toLocaleString()} tokens used
        </div>
      )}
    </div>
  )
}

export default TokenProgressBar
