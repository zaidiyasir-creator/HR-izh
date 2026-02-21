import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext(null);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

// Convert hex to HSL for CSS variables
const hexToHSL = (hex) => {
  // Remove # if present
  hex = hex.replace('#', '');
  
  // Parse hex values
  const r = parseInt(hex.substring(0, 2), 16) / 255;
  const g = parseInt(hex.substring(2, 4), 16) / 255;
  const b = parseInt(hex.substring(4, 6), 16) / 255;
  
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;
  
  if (max === min) {
    h = s = 0;
  } else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
      default: h = 0;
    }
  }
  
  return {
    h: Math.round(h * 360),
    s: Math.round(s * 100),
    l: Math.round(l * 100)
  };
};

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('vantage_theme');
    if (saved) return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  const [primaryColor, setPrimaryColorState] = useState(() => {
    return localStorage.getItem('vantage_primary_color') || '#0F172A';
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('vantage_theme', theme);
  }, [theme]);

  // Apply primary color as CSS variables
  const setPrimaryColor = (color) => {
    setPrimaryColorState(color);
    localStorage.setItem('vantage_primary_color', color);
    applyColorToCSS(color);
  };

  const applyColorToCSS = (color) => {
    const hsl = hexToHSL(color);
    const root = document.documentElement;
    
    // Set primary color HSL values
    root.style.setProperty('--primary', `${hsl.h} ${hsl.s}% ${hsl.l}%`);
    root.style.setProperty('--primary-foreground', hsl.l > 50 ? '0 0% 0%' : '0 0% 100%');
    
    // Set ring color to match primary
    root.style.setProperty('--ring', `${hsl.h} ${hsl.s}% ${hsl.l}%`);
    
    // Set sidebar accent
    root.style.setProperty('--sidebar-primary', `${hsl.h} ${hsl.s}% ${hsl.l}%`);
    root.style.setProperty('--sidebar-primary-foreground', hsl.l > 50 ? '0 0% 0%' : '0 0% 100%');
    root.style.setProperty('--sidebar-accent', `${hsl.h} ${Math.max(hsl.s - 20, 10)}% ${theme === 'dark' ? Math.min(hsl.l + 10, 30) : Math.max(hsl.l - 5, 90)}%`);
    root.style.setProperty('--sidebar-accent-foreground', `${hsl.h} ${hsl.s}% ${theme === 'dark' ? '90' : '20'}%`);
  };

  // Apply color on mount and when theme changes
  useEffect(() => {
    applyColorToCSS(primaryColor);
  }, [primaryColor, theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const value = {
    theme,
    setTheme,
    toggleTheme,
    primaryColor,
    setPrimaryColor,
    isDark: theme === 'dark'
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export default ThemeContext;
