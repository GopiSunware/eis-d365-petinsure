# Frontend Design Skill

<frontend_aesthetics>
You tend to converge toward generic, "on distribution" outputs. In frontend design, this creates what users call the "AI slop" aesthetic. Avoid this: make creative, distinctive frontends that surprise and delight.
</frontend_aesthetics>

## Typography

Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial, Helvetica, and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics.

**Recommended Font Families:**
- Display: Playfair Display, Bricolage Grotesque, Space Grotesk, Outfit
- Monospace: JetBrains Mono, Fira Code, IBM Plex Mono
- Sans-serif: IBM Plex Sans, Sora, Manrope, Plus Jakarta Sans
- Serif: Merriweather, Lora, Source Serif Pro

**Typography Principles:**
- High contrast = interesting. Pair display + monospace, serif + geometric sans
- Use variable fonts across weights for visual hierarchy
- Don't be afraid of large type sizes for headings (48px+)
- Line height: 1.5-1.7 for body text, tighter (1.1-1.3) for headings

```css
/* Example: Distinctive typography setup */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --font-display: 'Space Grotesk', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

h1, h2, h3 { font-family: var(--font-display); font-weight: 700; }
code, pre { font-family: var(--font-mono); }
```

## Color & Theme

Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.

**Color Principles:**
- Choose ONE dominant color and commit to it boldly
- Use sharp accent colors sparingly for high-impact moments
- Dark themes should use subtle off-blacks (#0a0a0a, #111111) not pure black
- Light themes benefit from warm whites (#fafaf9, #f8fafc)

**Avoid:**
- Generic blue (#007bff) and purple (#6366f1) gradients
- Timid, washed-out pastels
- Too many competing accent colors

```css
/* Example: Bold, cohesive color system */
:root {
  /* Dark theme with amber accent */
  --bg-primary: #0a0a0a;
  --bg-secondary: #171717;
  --bg-tertiary: #262626;
  --text-primary: #fafafa;
  --text-secondary: #a3a3a3;
  --accent: #f59e0b;
  --accent-hover: #d97706;

  /* Gradient for hero sections */
  --gradient-hero: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
}
```

## Motion & Animation

Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library (Framer Motion) for React when available.

**Motion Principles:**
- Focus on high-impact moments: one well-orchestrated page load with staggered reveals creates more delight than scattered micro-interactions
- Use `animation-delay` for staggered reveals
- Keep durations short: 150-300ms for micro-interactions, 400-600ms for page transitions
- Prefer `transform` and `opacity` for performance

```css
/* Example: Staggered fade-in on page load */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-in {
  animation: fadeInUp 0.5s ease-out forwards;
  opacity: 0;
}

.animate-in:nth-child(1) { animation-delay: 0.1s; }
.animate-in:nth-child(2) { animation-delay: 0.2s; }
.animate-in:nth-child(3) { animation-delay: 0.3s; }

/* Micro-interaction: button hover */
.btn {
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
```

**React/Framer Motion Example:**
```tsx
import { motion } from 'framer-motion';

const staggerContainer = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

<motion.div variants={staggerContainer} initial="hidden" animate="show">
  {items.map(item => (
    <motion.div key={item.id} variants={fadeInUp}>
      {item.content}
    </motion.div>
  ))}
</motion.div>
```

## Backgrounds & Depth

Create atmosphere and depth rather than defaulting to solid colors. Layer CSS gradients, use geometric patterns, or add contextual effects that match the overall aesthetic.

**Background Techniques:**
- Layered gradients with subtle noise texture
- Geometric patterns (dots, grids, diagonal lines)
- Glassmorphism with backdrop-blur
- Subtle animated gradients for hero sections

```css
/* Example: Layered background with depth */
.hero {
  background:
    /* Noise texture overlay */
    url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E"),
    /* Radial glow */
    radial-gradient(ellipse at 50% 0%, rgba(245, 158, 11, 0.15) 0%, transparent 50%),
    /* Base gradient */
    linear-gradient(180deg, #0a0a0a 0%, #171717 100%);
}

/* Dot pattern background */
.pattern-dots {
  background-image: radial-gradient(circle, #333 1px, transparent 1px);
  background-size: 20px 20px;
}

/* Grid pattern */
.pattern-grid {
  background-image:
    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}

/* Glassmorphism card */
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}
```

## Component Patterns

### Cards
```css
.card {
  background: var(--bg-secondary);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 1.5rem;
  transition: border-color 0.2s ease, transform 0.2s ease;
}
.card:hover {
  border-color: rgba(255, 255, 255, 0.12);
  transform: translateY(-2px);
}
```

### Buttons
```css
.btn-primary {
  background: var(--accent);
  color: #000;
  font-weight: 600;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-primary:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.25);
}
```

### Input Fields
```css
.input {
  background: var(--bg-tertiary);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: var(--text-primary);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
}
```

## Dashboard-Specific Guidelines

For the EIS Dynamics and PetInsure360 dashboards:

### Data Visualization
- Use consistent color coding across all charts
- Status colors: Success (#22c55e), Warning (#f59e0b), Error (#ef4444), Info (#3b82f6)
- Charts should have subtle grid lines, not overwhelming borders

### Tables
```css
.table {
  border-collapse: separate;
  border-spacing: 0;
}
.table th {
  background: var(--bg-tertiary);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
}
.table tr:hover td {
  background: rgba(255, 255, 255, 0.02);
}
```

### Stats Cards
```css
.stat-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.stat-value {
  font-size: 2rem;
  font-weight: 700;
  font-family: var(--font-display);
  line-height: 1;
}
.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.stat-change {
  font-size: 0.875rem;
  font-weight: 500;
}
.stat-change.positive { color: #22c55e; }
.stat-change.negative { color: #ef4444; }
```

## Anti-Patterns to Avoid

1. **Generic Bootstrap/Tailwind defaults** - Customize aggressively
2. **Pure white (#fff) or pure black (#000)** - Use off-shades for depth
3. **Comic Sans, Papyrus, or system defaults** - Always specify fonts
4. **Rainbow gradient buttons** - Commit to ONE accent color
5. **Bouncy, exaggerated animations** - Subtle is sophisticated
6. **Flat, solid backgrounds everywhere** - Add texture and depth
7. **Center-aligning everything** - Use visual hierarchy with alignment
8. **Low contrast text** - Ensure WCAG AA compliance (4.5:1 ratio)

## Dark Mode Support

Both themes should be first-class. Use CSS custom properties with a data attribute toggle.

```css
/* Light theme (default) */
:root {
  --bg-primary: #fafafa;
  --bg-secondary: #ffffff;
  --bg-tertiary: #f4f4f5;
  --text-primary: #18181b;
  --text-secondary: #71717a;
  --border-color: rgba(0, 0, 0, 0.08);
  --accent: #f97316; /* pet-orange for PetInsure360 */
  --accent-hover: #ea580c;
}

/* Dark theme */
[data-theme="dark"] {
  --bg-primary: #0a0a0a;
  --bg-secondary: #171717;
  --bg-tertiary: #262626;
  --text-primary: #fafafa;
  --text-secondary: #a3a3a3;
  --border-color: rgba(255, 255, 255, 0.08);
}

/* Smooth transition */
* {
  transition: background-color 0.2s ease, border-color 0.2s ease;
}
```

**React Toggle:**
```tsx
const [theme, setTheme] = useState('light');
useEffect(() => {
  document.documentElement.setAttribute('data-theme', theme);
}, [theme]);
```

## Recharts & Data Visualization

For BI dashboards using Recharts:

```tsx
// Custom theme for Recharts
const chartTheme = {
  colors: ['#f97316', '#3b82f6', '#22c55e', '#a855f7'], // Brand colors
  grid: { stroke: 'var(--border-color)', strokeDasharray: '3 3' },
  axis: { stroke: 'var(--text-secondary)', fontSize: 12 },
  tooltip: {
    contentStyle: {
      background: 'var(--bg-secondary)',
      border: '1px solid var(--border-color)',
      borderRadius: '8px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
    }
  }
};

// Apply in charts
<LineChart>
  <CartesianGrid {...chartTheme.grid} />
  <XAxis tick={{ fill: 'var(--text-secondary)' }} />
  <Tooltip {...chartTheme.tooltip} />
  <Line stroke={chartTheme.colors[0]} strokeWidth={2} dot={{ r: 4 }} />
</LineChart>
```

**Chart Card Styling:**
```css
.chart-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 1.5rem;
}
.chart-card h3 {
  font-family: var(--font-display);
  font-weight: 600;
  margin-bottom: 1rem;
}
```

## Loading & Skeleton States

Replace spinners with skeleton screens for better perceived performance:

```css
/* Skeleton shimmer effect */
.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-tertiary) 25%,
    var(--bg-secondary) 50%,
    var(--bg-tertiary) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 8px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Skeleton variants */
.skeleton-text { height: 1rem; width: 60%; }
.skeleton-title { height: 1.5rem; width: 40%; }
.skeleton-card { height: 120px; width: 100%; }
.skeleton-avatar { height: 48px; width: 48px; border-radius: 50%; }
```

**React Skeleton Component:**
```tsx
const Skeleton = ({ className }: { className?: string }) => (
  <div className={`skeleton ${className}`} />
);

// Usage in loading state
{loading ? (
  <div className="space-y-4">
    <Skeleton className="skeleton-title" />
    <Skeleton className="skeleton-text" />
    <Skeleton className="skeleton-text" />
  </div>
) : (
  <Content />
)}
```

## Real-time Connection Indicators

For WebSocket/Socket.IO status (used in PetInsure360 BI Dashboard):

```css
/* Connection status pill */
.connection-status {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.connection-status.connected {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.connection-status.disconnected {
  background: rgba(161, 161, 170, 0.1);
  color: #a1a1aa;
}

/* Pulse indicator dot */
.connection-status::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.connection-status.connected::before {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

## React Flow Pipeline Visualization

For EIS-Dynamics agent pipeline canvas:

```css
/* Pipeline node base */
.react-flow__node {
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  border-radius: 12px;
  padding: 1rem;
  min-width: 180px;
  transition: all 0.2s ease;
}

/* Node states */
.react-flow__node.processing {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px rgba(249, 115, 22, 0.2);
  animation: node-pulse 2s ease-in-out infinite;
}

.react-flow__node.completed {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.05);
}

.react-flow__node.error {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

/* Agent type indicators */
.node-badge {
  position: absolute;
  top: -8px;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.125rem 0.5rem;
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-radius: 4px;
}

.node-badge.bronze { background: #cd7f32; color: white; }
.node-badge.silver { background: #c0c0c0; color: #333; }
.node-badge.gold { background: #ffd700; color: #333; }

/* Edge animations */
.react-flow__edge-path {
  stroke: var(--border-color);
  stroke-width: 2;
}

.react-flow__edge.animated .react-flow__edge-path {
  stroke-dasharray: 5;
  animation: flow 1s linear infinite;
}

@keyframes flow {
  from { stroke-dashoffset: 10; }
  to { stroke-dashoffset: 0; }
}
```

## Form Wizard / Multi-step Forms

For PetInsure360 registration and claim flows:

```css
/* Progress indicator */
.wizard-progress {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.wizard-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  position: relative;
}

.wizard-step::after {
  content: '';
  position: absolute;
  top: 16px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: var(--border-color);
}

.wizard-step:last-child::after { display: none; }

.wizard-step.completed::after {
  background: var(--accent);
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  background: var(--bg-tertiary);
  border: 2px solid var(--border-color);
  z-index: 1;
}

.wizard-step.active .step-number {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.wizard-step.completed .step-number {
  background: #22c55e;
  border-color: #22c55e;
  color: white;
}

.step-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-align: center;
}
```

## Tailwind Integration

Apply these principles using Tailwind's configuration:

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        // Pet Insurance brand colors
        pet: {
          orange: '#f97316',
          'orange-dark': '#ea580c',
        },
        // Semantic status colors
        success: { 50: '#f0fdf4', 500: '#22c55e', 600: '#16a34a' },
        warning: { 50: '#fffbeb', 500: '#f59e0b', 600: '#d97706' },
        danger: { 50: '#fef2f2', 500: '#ef4444', 600: '#dc2626' },
      },
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.5s ease-out forwards',
        'shimmer': 'shimmer 1.5s infinite',
        'pulse-slow': 'pulse 2s ease-in-out infinite',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: 0, transform: 'translateY(20px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
      },
    },
  },
  plugins: [],
}
```

**Tailwind Component Classes (index.css):**
```css
@layer components {
  .card {
    @apply bg-white dark:bg-neutral-900
           border border-gray-100 dark:border-neutral-800
           rounded-xl p-6
           transition-all duration-200
           hover:border-gray-200 dark:hover:border-neutral-700
           hover:-translate-y-0.5;
  }

  .btn-primary {
    @apply bg-pet-orange hover:bg-pet-orange-dark
           text-white font-semibold
           px-4 py-2 rounded-lg
           transition-all duration-150
           hover:-translate-y-0.5
           hover:shadow-lg hover:shadow-pet-orange/25;
  }

  .stat-card {
    @apply card flex flex-col gap-2;
  }

  .stat-value {
    @apply text-3xl font-bold font-display leading-none;
  }

  .stat-label {
    @apply text-sm text-gray-500 uppercase tracking-wide;
  }
}
```

## Toast Notifications

For real-time feedback (claim submitted, data refreshed):

```css
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 50;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.toast {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  animation: slideIn 0.3s ease-out;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.toast.success { background: #22c55e; color: white; }
.toast.warning { background: #f59e0b; color: white; }
.toast.error { background: #ef4444; color: white; }
.toast.info { background: #3b82f6; color: white; }

@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
```

## Quick Checklist

Before finalizing any frontend:
- [ ] Custom fonts loaded (not just system fonts like Inter)
- [ ] CSS variables defined for consistent theming
- [ ] Dark mode support implemented
- [ ] Page load animations with stagger effect
- [ ] Hover states on all interactive elements (translateY, shadow)
- [ ] Background has depth (gradient, pattern, or texture)
- [ ] One clear accent color throughout (pet-orange for PetInsure)
- [ ] Proper spacing rhythm (4px, 8px, 16px, 24px, 32px, 48px, 64px)
- [ ] Responsive breakpoints tested
- [ ] Loading states use skeletons (not just spinners)
- [ ] Real-time indicators styled consistently
- [ ] Charts use brand colors consistently
- [ ] WCAG AA contrast compliance (4.5:1 ratio)

---

## UI Audit: Current State

### PetInsure360 Frontend
| Criterion | Status | Issue |
|-----------|--------|-------|
| Typography | ⚠️ | Uses Inter (generic) |
| Color System | ⚠️ | Default Tailwind blue |
| Animations | ✅ | Has fade-in |
| Background | ❌ | Solid bg-gray-50 |
| Dark Mode | ❌ | Not implemented |
| Hover States | ⚠️ | Basic, no transforms |

### EIS-Dynamics Portal
| Criterion | Status | Issue |
|-----------|--------|-------|
| Typography | ⚠️ | System defaults |
| Color System | ✅ | Has semantic colors |
| Animations | ✅ | Multiple animations |
| Background | ⚠️ | Light gray only |
| React Flow | ⚠️ | Basic node styling |
| Dark Mode | ❌ | Not implemented |

### PetInsure360 BI Dashboard
| Criterion | Status | Issue |
|-----------|--------|-------|
| Typography | ⚠️ | Uses Inter |
| Charts | ⚠️ | Default Recharts colors |
| Real-time | ✅ | Has WebSocket indicator |
| Loading | ⚠️ | Spinner only |
| Tables | ✅ | Good structure |
