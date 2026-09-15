---
name: Modern Clinical
colors:
  surface: '#f9f9ff'
  surface-dim: '#cfdaf2'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eeff'
  surface-container-high: '#dee8ff'
  surface-container-highest: '#d8e3fb'
  on-surface: '#111c2d'
  on-surface-variant: '#3e4947'
  inverse-surface: '#263143'
  inverse-on-surface: '#ecf1ff'
  outline: '#6e7977'
  outline-variant: '#bdc9c6'
  surface-tint: '#006a63'
  primary: '#005c55'
  on-primary: '#ffffff'
  primary-container: '#0f766e'
  on-primary-container: '#a3faef'
  inverse-primary: '#80d5cb'
  secondary: '#216963'
  on-secondary: '#ffffff'
  secondary-container: '#a8ece5'
  on-secondary-container: '#266d68'
  tertiary: '#7d4200'
  on-tertiary: '#ffffff'
  tertiary-container: '#a15600'
  on-tertiary-container: '#ffe6d5'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#9cf2e8'
  primary-fixed-dim: '#80d5cb'
  on-primary-fixed: '#00201d'
  on-primary-fixed-variant: '#00504a'
  secondary-fixed: '#abefe8'
  secondary-fixed-dim: '#8fd3cc'
  on-secondary-fixed: '#00201e'
  on-secondary-fixed-variant: '#00504b'
  tertiary-fixed: '#ffdcc3'
  tertiary-fixed-dim: '#ffb77d'
  on-tertiary-fixed: '#2f1500'
  on-tertiary-fixed-variant: '#6e3900'
  background: '#f9f9ff'
  on-background: '#111c2d'
  surface-variant: '#d8e3fb'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  metric-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  container-padding: 24px
  gutter: 16px
  card-gap: 20px
---

## Brand & Style
The design system is centered on the "Modern Clinical" aesthetic—a synthesis of high-precision scientific tooling and contemporary software ergonomics. It prioritizes clarity, speed of cognition, and professional trust, essential for a Clinical Decision Support System. 

The visual language is rooted in **Corporate Modernism** with a focus on functional transparency. It utilizes high-density information layouts balanced by generous whitespace and a "Quiet UI" philosophy, ensuring that critical biomedical data remains the focal point without unnecessary visual noise.

## Colors
The palette is engineered for clinical precision. The primary Teal is used for actionable intelligence and primary navigation, while the Dark Teal provides a grounded, authoritative frame for the top bar.

- **Primary Action**: Teal (#0F766E) is the cognitive anchor for buttons and active states.
- **Surface & Background**: A "Cold-Grey" background (#F5F8FA) reduces eye strain during long shifts compared to pure white, while White (#FFFFFF) is reserved for data-containing cards.
- **Semantic Badging**: Strictly follows medical conventions:
  - **BENIGNO**: Success Green.
  - **MALIGNO**: Error Red.
  - **INDEFINIDO**: Slate Gray.
- **Ethical Layer**: Light Amber (#FEF3C7) backgrounds are used exclusively for cautionary AI-related disclaimers.

## Typography
This design system utilizes **Inter** for its exceptional legibility and comprehensive glyph support. 

- **Titles & Headings**: Set in Semibold (#1E293B) to provide clear hierarchical separation.
- **Body Text**: Set in Regular (#475569) to maintain a soft contrast that facilitates long-form reading of clinical notes.
- **Data & Metrics**: Specifically utilize `tabular-nums` (tnum) for all tables and numerical analysis. This ensures that decimal points align vertically, which is critical for comparing biomedical values.

## Layout & Spacing
The layout follows a **Fluid Grid** model optimized for high-resolution medical monitors.

- **Desktop**: 12-column grid with 24px margins and 16px gutters.
- **Card Containers**: Standardized 20px gap between data modules.
- **Top Bar**: Fixed 64px height for persistent access to the "🧬 BioStatusIA" identity and user controls.
- **Tables**: Horizontal scrolling is permitted on tablet/mobile, but the first column (Patient/ID) and the Header must remain sticky.

## Elevation & Depth
Depth is used sparingly to maintain a "flat" clinical feel. 

- **Surface Level (Level 0)**: Background color (#F5F8FA).
- **Card Level (Level 1)**: White surfaces with a subtle 1px border (#E2E8F0).
- **Interactive Depth**: Only use shadows on hover for cards or for floating elements like dropdowns. Use a "Soft Shadow" (0px 4px 6px -1px rgba(0, 0, 0, 0.05)) to suggest interactivity without creating visual clutter.

## Shapes
The shape language is "Approachable Geometric." 

- **Main Cards**: Fixed 16px radius to soften the high-density data environment.
- **Buttons & Inputs**: 8px (rounded-lg) for a modern, software-centric feel.
- **Clinical Badges**: Full pill shape (999px radius) to distinguish them from interactive buttons or square data cells.

## Components
- **Top Bar**: Dark Teal (#115E59) background. Typography for the logo is bold white. Navigation links use a lower opacity white (80%) and transition to 100% on hover.
- **Clinical Badges**: High-contrast pill shapes. Text inside badges must be Bold and centered.
- **Zebra-Striped Tables**: Headers are sticky with a subtle bottom border. Rows alternate between white and a very light tint of teal or gray every second row to assist horizontal tracking of data.
- **Charts**: Use Plotly-style aesthetic—minimalist axes, no background grids (or very faint gray), and a palette that aligns with the Primary Teal and Secondary status colors.
- **Ethical Banner**: A fixed-width or full-width component at the top of analysis pages. Light Amber background, 1px Amber border, featuring a warning icon. Text: "Esta é uma ferramenta de suporte à decisão baseada em IA e não substitui o diagnóstico clínico realizado por um médico."
- **Horizontal Tabs**: Simple underline style using the Primary Teal for the active state, located directly below card headers.