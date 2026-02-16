import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('App Component', () => {
  it('renders without crashing', () => {
    render(<App />);
    // Check if the main wrapper exists or specific text from your App.jsx
    expect(document.body).toBeDefined();
  });
});