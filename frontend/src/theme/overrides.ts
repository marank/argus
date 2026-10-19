import type { GlobalThemeOverrides } from 'naive-ui'

import { darkPalette, lightPalette, type Palette } from './palette'

const fontFamily = "'IBM Plex Sans Variable', 'IBM Plex Sans', system-ui, sans-serif"
const fontFamilyMono = "'JetBrains Mono Variable', 'JetBrains Mono', ui-monospace, monospace"

function build(p: Palette): GlobalThemeOverrides {
  return {
    common: {
      fontFamily,
      fontFamilyMono,
      fontSize: '13px',
      fontSizeMedium: '13px',
      fontSizeSmall: '12px',
      fontSizeLarge: '14px',
      borderRadius: '3px',
      borderRadiusSmall: '2px',
      heightSmall: '26px',
      heightMedium: '32px',
      heightLarge: '38px',
      primaryColor: p.primary,
      primaryColorHover: p.primaryHover,
      primaryColorPressed: p.primaryPressed,
      primaryColorSuppl: p.primaryHover,
      infoColor: p.info,
      successColor: p.success,
      warningColor: p.warning,
      errorColor: p.error,
      bodyColor: p.bg,
      cardColor: p.surface,
      modalColor: p.surfaceRaised,
      popoverColor: p.surfaceRaised,
      tableColor: p.surface,
      tableHeaderColor: p.surfaceSunken,
      inputColor: p.surface,
      borderColor: p.border,
      dividerColor: p.border,
      textColorBase: p.text,
      textColor1: p.text,
      textColor2: p.text,
      textColor3: p.textMuted,
    },
    Button: {
      textColorPrimary: p.onPrimary,
      textColorHoverPrimary: p.onPrimary,
      textColorPressedPrimary: p.onPrimary,
      textColorFocusPrimary: p.onPrimary,
      fontWeight: '500',
    },
    Card: {
      borderColor: p.border,
      titleFontSizeMedium: '13px',
      titleFontWeight: '600',
      paddingMedium: '16px 18px',
    },
    DataTable: {
      thFontWeight: '600',
      thTextColor: p.textMuted,
      tdColorHover: p.primarySoft,
      borderColor: p.border,
      thPaddingSmall: '6px 10px',
      tdPaddingSmall: '6px 10px',
    },
    Tag: { borderRadius: '2px', fontWeightStrong: '600' },
    Menu: {
      itemHeight: '34px',
      itemColorActive: p.primarySoft,
      itemColorActiveHover: p.primarySoft,
      itemTextColorActive: p.primary,
      itemIconColorActive: p.primary,
      itemTextColorActiveHover: p.primary,
      itemIconColorActiveHover: p.primary,
      borderRadius: '3px',
    },
    Input: { border: `1px solid ${p.borderStrong}` },
    InternalSelection: { border: `1px solid ${p.borderStrong}` },
    // Bordered surface tooltips instead of the default solid dark bubble.
    Tooltip: {
      color: p.surfaceRaised,
      textColor: p.text,
      boxShadow: `0 0 0 1px ${p.borderStrong}, 0 6px 18px rgba(0, 0, 0, 0.18)`,
    },
    DatePicker: { arrowColor: p.textMuted },
    Drawer: { color: p.surfaceRaised },
    Layout: { color: p.bg, siderColor: p.surface, headerColor: p.surface },
  }
}

export const lightOverrides = build(lightPalette)
export const darkOverrides = build(darkPalette)
