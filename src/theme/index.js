/**
 * Naive UI 主题定制
 *
 * 说明：
 * - 变量名与 Naive UI 官方 ThemeOverrides 保持一致，可参阅
 *   https://www.naiveui.com/zh-CN/os-theme/docs/customize-theme
 * - `common` 下为全局变量，其余以「组件名」为 key 做局部覆盖
 * - 深色主题（darkTheme）由 naive-ui 提供，这里只覆盖品牌色与圆角
 */

/** 品牌色板：改这里即可全局换肤 */
export const brand = {
  primary: '#2f6fed',
  primaryHover: '#558cff',
  primaryPressed: '#1f57c9',
}

/** 浅色主题覆盖 */
export const lightThemeOverrides = {
  common: {
    primaryColor: brand.primary,
    primaryColorHover: brand.primaryHover,
    primaryColorPressed: brand.primaryPressed,
    primaryColorSuppl: brand.primary,
    borderRadius: '8px',
    borderRadiusSmall: '6px',
    fontWeightStrong: '600',
    fontSize: '14px',
  },
  Card: {
    borderRadius: '12px',
  },
  Button: {
    borderRadiusMedium: '8px',
    borderRadiusSmall: '6px',
  },
  Layout: {
    color: '#f5f7fb',
    siderColor: '#ffffff',
    headerColor: '#ffffff',
  },
  Menu: {
    borderRadius: '8px',
    itemTextColorActive: brand.primary,
    itemTextColorActiveHover: brand.primary,
    itemIconColorActive: brand.primary,
    itemIconColorActiveHover: brand.primary,
  },
}

/** 深色主题覆盖 */
export const darkThemeOverrides = {
  common: {
    primaryColor: brand.primaryHover,
    primaryColorHover: '#84aaff',
    primaryColorPressed: brand.primary,
    primaryColorSuppl: brand.primaryHover,
    borderRadius: '8px',
    borderRadiusSmall: '6px',
    fontWeightStrong: '600',
    fontSize: '14px',
  },
  Card: {
    borderRadius: '12px',
  },
  Button: {
    borderRadiusMedium: '8px',
    borderRadiusSmall: '6px',
  },
  Layout: {
    color: '#101014',
    siderColor: '#18181c',
    headerColor: '#18181c',
  },
  Menu: {
    borderRadius: '8px',
    itemTextColorActive: brand.primaryHover,
    itemTextColorActiveHover: '#a5c0ff',
    itemIconColorActive: brand.primaryHover,
    itemIconColorActiveHover: '#a5c0ff',
  },
}

export default { brand, lightThemeOverrides, darkThemeOverrides }
