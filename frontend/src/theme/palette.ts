/** Color tokens shared by the Naive UI theme and the app's own CSS variables. */

export interface Palette {
  bg: string
  surface: string
  surfaceRaised: string
  surfaceSunken: string
  border: string
  borderStrong: string
  text: string
  textMuted: string
  textSubtle: string
  primary: string
  primaryHover: string
  primaryPressed: string
  primarySoft: string
  onPrimary: string
  success: string
  warning: string
  error: string
  info: string
  grid: string
}

export const lightPalette: Palette = {
  bg: '#f3f5f7',
  surface: '#ffffff',
  surfaceRaised: '#ffffff',
  surfaceSunken: '#eef1f4',
  border: '#dbe1e7',
  borderStrong: '#c3ccd5',
  text: '#0f1720',
  textMuted: '#5b6877',
  textSubtle: '#8794a3',
  primary: '#0e7490',
  primaryHover: '#0b8aa9',
  primaryPressed: '#0a5c72',
  primarySoft: 'rgba(14, 116, 144, 0.09)',
  onPrimary: '#ffffff',
  success: '#15803d',
  warning: '#b45309',
  error: '#c2410c',
  info: '#1d4ed8',
  grid: 'rgba(15, 23, 32, 0.035)',
}

export const darkPalette: Palette = {
  bg: '#0a0e13',
  surface: '#10151b',
  surfaceRaised: '#151b23',
  surfaceSunken: '#0c1116',
  border: '#212a35',
  borderStrong: '#2e3a48',
  text: '#dfe6ee',
  textMuted: '#8a97a8',
  textSubtle: '#5f6c7c',
  primary: '#22b8d6',
  primaryHover: '#46cbe5',
  primaryPressed: '#1a96af',
  primarySoft: 'rgba(34, 184, 214, 0.12)',
  onPrimary: '#03141a',
  success: '#34c370',
  warning: '#f0a63a',
  error: '#f26b4d',
  info: '#6aa1ff',
  grid: 'rgba(223, 230, 238, 0.03)',
}
