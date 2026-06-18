// React entry point.
//
// The root render is intentionally thin; application state and routing-like tab
// behavior live in `App.js` so the prototype can stay dependency-light.

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App.js';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
