import type { GlobalThemeOverrides } from 'naive-ui'

import { darkPalette, lightPalette, retroPalette, solarizedPalette, type Palette } from './palette'

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
    // Segmented choices: the active option soft like the select chips, not a solid fill.
    Radio: {
      buttonColorActive: p.primarySoft,
      buttonTextColorActive: p.primary,
      buttonBorderColorActive: p.primary,
    },
    // Page numbers like the segmented choices; disabled arrows only outlined, not a light box.
    Pagination: {
      itemColorActive: p.primarySoft,
      itemColorActiveHover: p.primarySoft,
      itemColorDisabled: 'transparent',
    },
    // Quiet scrollbars: in the border colour, a little stronger on hover.
    Scrollbar: { color: p.borderStrong, colorHover: p.textSubtle },
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

/*
 * Naive's light theme paints a number of surfaces in fixed white or cool grey (`baseColor` for
 * segmented buttons, checkboxes and tabs; tags, rails, disabled inputs, switch knobs …), which
 * stand out on the tinted Solarized surfaces. Solarized builds on the light theme, so it
 * replaces them with its own tones.
 */
function tinted(p: Palette): GlobalThemeOverrides {
  return {
    common: {
      baseColor: p.surface,
      tagColor: p.surfaceSunken,
      codeColor: p.surfaceSunken,
      tabColor: p.surfaceSunken,
      actionColor: p.surfaceSunken,
      // Highlighted options in selects and dropdowns: a tint of the text colour, so it shows
      // on any surface (popovers are as light as the cards).
      hoverColor: 'rgba(7, 54, 66, 0.07)',
      pressedColor: 'rgba(7, 54, 66, 0.11)',
      inputColorDisabled: p.surfaceSunken,
      railColor: p.borderStrong,
      textColorDisabled: p.textSubtle,
      placeholderColor: p.textSubtle,
      placeholderColorDisabled: p.borderStrong,
      iconColor: p.textSubtle,
      iconColorHover: p.textMuted,
      iconColorPressed: p.text,
      iconColorDisabled: p.borderStrong,
      clearColor: p.textSubtle,
      clearColorHover: p.textMuted,
      clearColorPressed: p.text,
    },
    Switch: { buttonColor: p.surface },
    Slider: { handleColor: p.surface },
  }
}

const solarized = build(solarizedPalette)
const solarizedTint = tinted(solarizedPalette)

export const lightOverrides = build(lightPalette)
export const darkOverrides = build(darkPalette)
export const retroOverrides = build(retroPalette)
export const solarizedOverrides: GlobalThemeOverrides = {
  ...solarized,
  ...solarizedTint,
  common: { ...solarized.common, ...solarizedTint.common },
}
