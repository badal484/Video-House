/**
 * Design Tokens & Theme Manager for the Studio Application.
 */

export const THEME_DARK = "dark";
export const THEME_LIGHT = "light";

export const ACCENTS = {
  CYAN: "#00F0FF",
  INDIGO: "#6366F1",
  EMERALD: "#10B981",
  AMBER: "#F59E0B",
  ROSE: "#F43F5E"
};

export class ThemeManager {
  constructor() {
    this.currentTheme = localStorage.getItem("studio_theme") || THEME_DARK;
    this.currentAccent = localStorage.getItem("studio_accent") || ACCENTS.CYAN;
    this.applyTheme(this.currentTheme);
    this.applyAccent(this.currentAccent);
  }

  applyTheme(theme) {
    this.currentTheme = theme;
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("studio_theme", theme);
  }

  applyAccent(colorHex) {
    this.currentAccent = colorHex;
    document.documentElement.style.setProperty("--studio-accent-primary", colorHex);
    document.documentElement.style.setProperty("--studio-border-focus", colorHex);
    localStorage.setItem("studio_accent", colorHex);
  }

  toggleTheme() {
    const nextTheme = this.currentTheme === THEME_DARK ? THEME_LIGHT : THEME_DARK;
    this.applyTheme(nextTheme);
    return nextTheme;
  }
}

export const themeManager = new ThemeManager();
