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
  violet: string
  pink: string
  grid: string
}

// Solarized Light: base3/base2 surfaces, base02/base01/base1 text and the Solarized accents.
// The primary is Solarized cyan one step darker, so button labels stay legible.
export const lightPalette: Palette = {
  bg: '#eee8d5',
  surface: '#fdf6e3',
  surfaceRaised: '#fdf6e3',
  surfaceSunken: '#f5efdc',
  border: '#e2dbc5',
  borderStrong: '#d3cbb3',
  text: '#073642',
  textMuted: '#586e75',
  textSubtle: '#93a1a1',
  primary: '#1f8a82',
  primaryHover: '#2aa198',
  primaryPressed: '#19716b',
  primarySoft: 'rgba(42, 161, 152, 0.11)',
  onPrimary: '#fdf6e3',
  success: '#859900',
  warning: '#b58900',
  error: '#dc322f',
  info: '#268bd2',
  violet: '#6c71c4',
  pink: '#d33682',
  grid: 'rgba(7, 54, 66, 0.04)',
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
  violet: '#a78bfa',
  pink: '#f472b6',
  grid: 'rgba(223, 230, 238, 0.03)',
}
