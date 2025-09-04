import { createTheme, ThemeOptions } from '@mui/material/styles'
import { colors, typography, spacing, borderRadius, shadows, breakpoints, zIndex, transitions } from './design-tokens'

// Create custom theme options
const themeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: colors.primary[200], // #7EACB5
      light: colors.primary[100], // #FADFA1
      dark: colors.primary[300], // #C96868
      contrastText: colors.text.inverse,
    },
    secondary: {
      main: colors.primary[300], // #C96868
      light: colors.primary[200], // #7EACB5
      dark: colors.primary[400], // #B85A5A
      contrastText: colors.text.inverse,
    },
    error: {
      main: colors.semantic.error,
      light: '#FFCDD2',
      dark: '#D32F2F',
      contrastText: colors.text.inverse,
    },
    warning: {
      main: colors.semantic.warning,
      light: '#FFE0B2',
      dark: '#F57C00',
      contrastText: colors.text.primary,
    },
    info: {
      main: colors.semantic.info,
      light: '#BBDEFB',
      dark: '#1976D2',
      contrastText: colors.text.inverse,
    },
    success: {
      main: colors.semantic.success,
      light: '#C8E6C9',
      dark: '#388E3C',
      contrastText: colors.text.inverse,
    },
    background: {
      default: colors.background.primary,
      paper: colors.background.secondary,
    },
    text: {
      primary: colors.text.primary,
      secondary: colors.text.secondary,
    },
    divider: colors.border.light,
  },
  
  typography: {
    fontFamily: typography.fontFamily.primary,
    h1: {
      fontSize: typography.fontSize['4xl'],
      fontWeight: typography.fontWeight.bold,
      lineHeight: typography.lineHeight.tight,
      color: colors.text.primary,
    },
    h2: {
      fontSize: typography.fontSize['3xl'],
      fontWeight: typography.fontWeight.bold,
      lineHeight: typography.lineHeight.tight,
      color: colors.text.primary,
    },
    h3: {
      fontSize: typography.fontSize['2xl'],
      fontWeight: typography.fontWeight.semibold,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.primary,
    },
    h4: {
      fontSize: typography.fontSize.xl,
      fontWeight: typography.fontWeight.semibold,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.primary,
    },
    h5: {
      fontSize: typography.fontSize.lg,
      fontWeight: typography.fontWeight.medium,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.primary,
    },
    h6: {
      fontSize: typography.fontSize.base,
      fontWeight: typography.fontWeight.medium,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.primary,
    },
    body1: {
      fontSize: typography.fontSize.base,
      fontWeight: typography.fontWeight.normal,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.primary,
    },
    body2: {
      fontSize: typography.fontSize.sm,
      fontWeight: typography.fontWeight.normal,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.secondary,
    },
    button: {
      fontSize: typography.fontSize.sm,
      fontWeight: typography.fontWeight.medium,
      textTransform: 'none',
    },
    caption: {
      fontSize: typography.fontSize.xs,
      fontWeight: typography.fontWeight.normal,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.tertiary,
    },
  },
  
  spacing: 8, // 8px base unit
  
  shape: {
    borderRadius: parseInt(borderRadius.md),
  },
  
  shadows: [
    'none',
    shadows.sm,
    shadows.base,
    shadows.md,
    shadows.lg,
    shadows.xl,
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
    shadows['2xl'],
  ],
  
  breakpoints: {
    values: {
      xs: parseInt(breakpoints.xs),
      sm: parseInt(breakpoints.sm),
      md: parseInt(breakpoints.md),
      lg: parseInt(breakpoints.lg),
      xl: parseInt(breakpoints.xl),
    },
  },
  
  zIndex: {
    mobileStepper: zIndex.base,
    fab: zIndex.docked,
    speedDial: zIndex.docked,
    appBar: zIndex.sticky,
    drawer: zIndex.overlay,
    modal: zIndex.modal,
    snackbar: zIndex.toast,
    tooltip: zIndex.tooltip,
  },
  
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: borderRadius.md,
          textTransform: 'none',
          fontWeight: typography.fontWeight.medium,
          transition: transitions.normal,
          '&:hover': {
            transform: 'translateY(-1px)',
            boxShadow: shadows.md,
          },
        },
        contained: {
          boxShadow: shadows.sm,
          '&:hover': {
            boxShadow: shadows.md,
          },
        },
        outlined: {
          borderWidth: '2px',
          '&:hover': {
            borderWidth: '2px',
          },
        },
      },
    },
    
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: borderRadius.md,
            transition: transitions.normal,
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: colors.border.medium,
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: colors.border.focus,
              borderWidth: '2px',
            },
          },
        },
      },
    },
    
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: borderRadius.lg,
          boxShadow: shadows.sm,
          transition: transitions.normal,
          '&:hover': {
            boxShadow: shadows.md,
          },
        },
      },
    },
    
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: borderRadius.lg,
        },
        elevation1: {
          boxShadow: shadows.sm,
        },
        elevation2: {
          boxShadow: shadows.base,
        },
        elevation3: {
          boxShadow: shadows.md,
        },
      },
    },
    
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: colors.background.primary,
          color: colors.text.primary,
          boxShadow: shadows.sm,
        },
      },
    },
    
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: colors.background.secondary,
          borderRight: `1px solid ${colors.border.light}`,
        },
      },
    },
    
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: borderRadius.md,
          margin: `${spacing[1]} ${spacing[2]}`,
          transition: transitions.fast,
          '&:hover': {
            backgroundColor: colors.primary[50],
          },
          '&.Mui-selected': {
            backgroundColor: colors.primary[100],
            '&:hover': {
              backgroundColor: colors.primary[100],
            },
          },
        },
      },
    },
    
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: borderRadius.full,
          fontWeight: typography.fontWeight.medium,
        },
      },
    },
    
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: borderRadius.md,
        },
      },
    },
    
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: borderRadius.xl,
        },
      },
    },
    
    MuiSnackbar: {
      styleOverrides: {
        root: {
          '& .MuiSnackbarContent-root': {
            borderRadius: borderRadius.md,
          },
        },
      },
    },
  },
}

// Create the theme
export const lightTheme = createTheme(themeOptions)

// Dark theme variant
export const darkTheme = createTheme({
  ...themeOptions,
  palette: {
    ...themeOptions.palette,
    mode: 'dark',
    primary: {
      main: colors.primary[200], // #7EACB5
      light: colors.primary[100], // #FADFA1
      dark: colors.primary[300], // #C96868
      contrastText: colors.text.primary,
    },
    background: {
      default: '#121212',
      paper: '#1E1E1E',
    },
    text: {
      primary: '#FFFFFF',
      secondary: '#B3B3B3',
    },
    divider: '#404040',
  },
  components: {
    ...themeOptions.components,
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1E1E1E',
          color: '#FFFFFF',
          boxShadow: shadows.sm,
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#1E1E1E',
          borderRight: '1px solid #404040',
        },
      },
    },
  },
})

export default lightTheme
