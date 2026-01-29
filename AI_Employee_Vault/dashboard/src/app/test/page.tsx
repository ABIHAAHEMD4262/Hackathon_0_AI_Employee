'use client';

import { useState } from 'react';

export default function TestPage() {
  const [text, setText] = useState('');
  const [clicks, setClicks] = useState(0);

  return (
    <div style={{ padding: '50px', background: '#1a1a2e', minHeight: '100vh', color: 'white' }}>
      <h1 style={{ marginBottom: '20px' }}>Test Page</h1>

      <div style={{ marginBottom: '20px' }}>
        <p>Clicks: {clicks}</p>
        <button
          onClick={() => setClicks(c => c + 1)}
          style={{
            padding: '10px 20px',
            background: '#00ff88',
            color: 'black',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer'
          }}
        >
          Click Me
        </button>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <p>You typed: {text}</p>
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type something here..."
          style={{
            padding: '10px',
            width: '300px',
            background: '#0a0a0f',
            border: '1px solid #00ff88',
            borderRadius: '8px',
            color: 'white'
          }}
        />
      </div>

      <p style={{ color: '#888' }}>
        If you can click the button and type in the input, React is working fine.
      </p>
    </div>
  );
}
