import React from 'react'

interface MicSparklesIconProps extends React.SVGProps<SVGSVGElement> {
  className?: string
  size?: number
}

export const MicSparklesIcon: React.FC<MicSparklesIconProps> = ({ 
  className = '', 
  size = 24,
  ...props 
}) => {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 100 100"
      width={size}
      height={size}
      className={className}
      {...props}
    >
      <defs>
        <linearGradient id={`micGradient-${size}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{stopColor: 'currentColor', stopOpacity: 1}} />
          <stop offset="100%" style={{stopColor: 'currentColor', stopOpacity: 0.8}} />
        </linearGradient>
      </defs>
      
      {/* Microphone body */}
      <rect x="40" y="20" width="20" height="35" rx="10" fill={`url(#micGradient-${size})`}/>
      
      {/* Microphone stand */}
      <path d="M 35 60 Q 35 70 50 70 Q 65 70 65 60" stroke="currentColor" strokeWidth="3" fill="none"/>
      <line x1="50" y1="70" x2="50" y2="80" stroke="currentColor" strokeWidth="3"/>
      <line x1="40" y1="80" x2="60" y2="80" stroke="currentColor" strokeWidth="4" strokeLinecap="round"/>
      
      {/* Microphone arc */}
      <path d="M 30 45 Q 30 60 50 60 Q 70 60 70 45" stroke="currentColor" strokeWidth="2.5" fill="none"/>
      
      {/* Sparkles */}
      <g fill="currentColor" opacity="0.9">
        {/* Top right sparkle */}
        <circle cx="72" cy="25" r="2"/>
        <line x1="72" y1="20" x2="72" y2="30" stroke="currentColor" strokeWidth="1.5"/>
        <line x1="67" y1="25" x2="77" y2="25" stroke="currentColor" strokeWidth="1.5"/>
        
        {/* Top left sparkle */}
        <circle cx="25" cy="30" r="1.5"/>
        <line x1="25" y1="26" x2="25" y2="34" stroke="currentColor" strokeWidth="1"/>
        <line x1="21" y1="30" x2="29" y2="30" stroke="currentColor" strokeWidth="1"/>
        
        {/* Bottom right sparkle */}
        <circle cx="75" cy="55" r="1.5"/>
        <line x1="75" y1="51" x2="75" y2="59" stroke="currentColor" strokeWidth="1"/>
        <line x1="71" y1="55" x2="79" y2="55" stroke="currentColor" strokeWidth="1"/>
      </g>
    </svg>
  )
}

