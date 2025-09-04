/**
 * SprintConnect Design Tokens
 * Based on ColorHunt palette: #C96868, #7EACB5, #FADFA1, #FFF4EA
 */

export const colors = {
  // Primary palette from ColorHunt
  primary: {
    50: '#FFF4EA',   // Lightest - backgrounds, subtle highlights
    100: '#FADFA1',  // Light - secondary backgrounds, disabled states
    200: '#7EACB5',  // Medium - primary actions, links
    300: '#C96868',  // Dark - primary brand, important actions
    400: '#B85A5A',  // Darker - hover states
    500: '#A74C4C',  // Darkest - active states, text
  },
  
  // Semantic colors derived from primary palette
  semantic: {
    success: '#4CAF50',
    warning: '#FF9800', 
    error: '#F44336',
    info: '#2196F3',
  },
  
  // Neutral grays for text and backgrounds
  neutral: {
    50: '#FAFAFA',
    100: '#F5F5F5',
    200: '#EEEEEE',
    300: '#E0E0E0',
    400: '#BDBDBD',
    500: '#9E9E9E',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
  },
  
  // Background colors
  background: {
    primary: '#FFFFFF',
    secondary: '#FFF4EA',
    tertiary: '#FADFA1',
    dark: '#212121',
    overlay: 'rgba(0, 0, 0, 0.5)',
  },
  
  // Text colors
  text: {
    primary: '#212121',
    secondary: '#616161',
    tertiary: '#9E9E9E',
    inverse: '#FFFFFF',
    link: '#7EACB5',
    linkHover: '#C96868',
  },
  
  // Border colors
  border: {
    light: '#E0E0E0',
    medium: '#BDBDBD',
    dark: '#757575',
    focus: '#7EACB5',
    error: '#F44336',
  },
} as const

export const typography = {
  fontFamily: {
    primary: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: '"JetBrains Mono", "Fira Code", Consolas, monospace',
  },
  
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
    '5xl': '3rem',    // 48px
  },
  
  fontWeight: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
} as const

export const spacing = {
  0: '0',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  5: '1.25rem',   // 20px
  6: '1.5rem',    // 24px
  8: '2rem',      // 32px
  10: '2.5rem',   // 40px
  12: '3rem',     // 48px
  16: '4rem',     // 64px
  20: '5rem',     // 80px
  24: '6rem',     // 96px
  32: '8rem',     // 128px
} as const

export const borderRadius = {
  none: '0',
  sm: '0.125rem',   // 2px
  base: '0.25rem',  // 4px
  md: '0.375rem',   // 6px
  lg: '0.5rem',     // 8px
  xl: '0.75rem',    // 12px
  '2xl': '1rem',    // 16px
  full: '9999px',
} as const

export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
} as const

export const breakpoints = {
  xs: '0px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const

export const zIndex = {
  hide: -1,
  auto: 'auto',
  base: 0,
  docked: 10,
  dropdown: 1000,
  sticky: 1100,
  banner: 1200,
  overlay: 1300,
  modal: 1400,
  popover: 1500,
  skipLink: 1600,
  toast: 1700,
  tooltip: 1800,
} as const

export const transitions = {
  fast: '150ms ease-in-out',
  normal: '250ms ease-in-out',
  slow: '350ms ease-in-out',
} as const

// Component-specific tokens
export const components = {
  button: {
    height: {
      sm: '2rem',      // 32px
      md: '2.5rem',    // 40px
      lg: '3rem',      // 48px
    },
    padding: {
      sm: '0.5rem 1rem',
      md: '0.75rem 1.5rem',
      lg: '1rem 2rem',
    },
  },
  
  input: {
    height: {
      sm: '2rem',
      md: '2.5rem',
      lg: '3rem',
    },
    padding: {
      sm: '0.5rem 0.75rem',
      md: '0.75rem 1rem',
      lg: '1rem 1.25rem',
    },
  },
  
  card: {
    padding: {
      sm: '1rem',
      md: '1.5rem',
      lg: '2rem',
    },
  },
} as const

// Dark mode color overrides
export const darkModeColors = {
  background: {
    primary: '#121212',
    secondary: '#1E1E1E',
    tertiary: '#2D2D2D',
    overlay: 'rgba(255, 255, 255, 0.1)',
  },
  
  text: {
    primary: '#FFFFFF',
    secondary: '#B3B3B3',
    tertiary: '#808080',
    inverse: '#121212',
    link: '#7EACB5',
    linkHover: '#C96868',
  },
  
  border: {
    light: '#404040',
    medium: '#525252',
    dark: '#666666',
    focus: '#7EACB5',
    error: '#F44336',
  },
} as const

export type ColorToken = keyof typeof colors
export type TypographyToken = keyof typeof typography
export type SpacingToken = keyof typeof spacing
export type BorderRadiusToken = keyof typeof borderRadius
export type ShadowToken = keyof typeof shadows
export type BreakpointToken = keyof typeof breakpoints
export type ZIndexToken = keyof typeof zIndex
export type TransitionToken = keyof typeof transitions
