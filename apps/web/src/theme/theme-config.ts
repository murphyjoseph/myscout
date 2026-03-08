import { defineConfig } from "@chakra-ui/react";

/**
 * MyScout design tokens.
 *
 * All color values live here — views reference token names (e.g., color="fg.muted"),
 * presenters output token names for data-driven colors (e.g., scoreColor: "score.high").
 *
 * For non-Chakra elements (SVG, native <select>), use CSS variables:
 *   var(--chakra-colors-accent-solid)
 */
export const themeConfig = defineConfig({
  theme: {
    tokens: {
      fonts: {
        heading: { value: "var(--font-body), system-ui, sans-serif" },
        body: { value: "var(--font-body), system-ui, sans-serif" },
      },
    },
    semanticTokens: {
      colors: {
        /* ─── Surfaces ────────────────────────────────── */
        bg: {
          value: { _light: "#ffffff", _dark: "#0a0a0c" },
          subtle: { value: { _light: "#f5f5f5", _dark: "#0c0c10" } },
          muted: { value: { _light: "#e5e5e5", _dark: "#1c1c24" } },
        },

        /* ─── Foreground / text ───────────────────────── */
        fg: {
          value: { _light: "#09090b", _dark: "#ededef" },
          heading: { value: { _light: "#27272a", _dark: "#d4d4d8" } },
          muted: { value: { _light: "#525252", _dark: "#a1a1aa" } },
          subtle: { value: { _light: "#737373", _dark: "#71717a" } },
          dim: { value: { _light: "#a3a3a3", _dark: "#52525b" } },
          faint: { value: { _light: "#d4d4d4", _dark: "#3f3f46" } },
          error: { value: { _light: "#dc2626", _dark: "#ef4444" } },
          success: { value: { _light: "#16a34a", _dark: "#22c55e" } },
        },

        /* ─── Borders ─────────────────────────────────── */
        border: {
          value: { _light: "#e5e5e5", _dark: "#27272a" },
          subtle: { value: { _light: "#f5f5f5", _dark: "#1a1a1f" } },
          muted: { value: { _light: "#e5e5e5", _dark: "#1f1f24" } },
        },

        /* ─── Accent (gold) ───────────────────────────── */
        accent: {
          solid: { value: { _light: "#b07d2e", _dark: "#c8913a" } },
          emphasized: { value: { _light: "#c8913a", _dark: "#d9a04a" } },
          contrast: { value: { _light: "#ffffff", _dark: "#0a0a0c" } },
          subtle: {
            value: {
              _light: "rgba(200, 145, 58, 0.08)",
              _dark: "rgba(200, 145, 58, 0.1)",
            },
          },
          muted: {
            value: {
              _light: "rgba(200, 145, 58, 0.2)",
              _dark: "rgba(200, 145, 58, 0.25)",
            },
          },
          fg: { value: { _light: "#8b6914", _dark: "#c8913a" } },
        },

        /* ─── Score tiers ─────────────────────────────── */
        score: {
          high: { value: { _light: "#b07d2e", _dark: "#c8913a" } },
          good: { value: { _light: "#7d7d2e", _dark: "#a3a353" } },
          mid: { value: { _light: "#737373", _dark: "#71717a" } },
          low: { value: { _light: "#a3a3a3", _dark: "#52525b" } },
          negative: { value: { _light: "#dc2626", _dark: "#b45454" } },
        },

        /* ─── Status ──────────────────────────────────── */
        status: {
          new: { value: { _light: "#2563eb", _dark: "#3b82f6" } },
          saved: { value: { _light: "#9333ea", _dark: "#a855f7" } },
          applied: { value: { _light: "#16a34a", _dark: "#22c55e" } },
          skipped: { value: { _light: "#a3a3a3", _dark: "#52525b" } },
          interviewing: { value: { _light: "#d97706", _dark: "#f59e0b" } },
        },

        /* ─── Tech tag categories ─────────────────────── */
        tag: {
          strongPlus: {
            fg: { value: { _light: "#4d7353", _dark: "#6b8f71" } },
            bg: {
              value: {
                _light: "rgba(107, 143, 113, 0.06)",
                _dark: "rgba(107, 143, 113, 0.08)",
              },
            },
            border: {
              value: {
                _light: "rgba(107, 143, 113, 0.15)",
                _dark: "rgba(107, 143, 113, 0.2)",
              },
            },
          },
          avoid: {
            fg: { value: { _light: "#7a3b3b", _dark: "#8b5454" } },
            bg: {
              value: {
                _light: "rgba(139, 84, 84, 0.06)",
                _dark: "rgba(139, 84, 84, 0.08)",
              },
            },
            border: {
              value: {
                _light: "rgba(139, 84, 84, 0.15)",
                _dark: "rgba(139, 84, 84, 0.2)",
              },
            },
          },
        },

        /* ─── Salary ──────────────────────────────────── */
        salary: {
          fg: { value: { _light: "#5c6e3f", _dark: "#8b9a6b" } },
        },
      },
    },
  },
  globalCss: {
    body: {
      bg: "bg",
      color: "fg",
    },
  },
});
