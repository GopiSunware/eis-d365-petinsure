---
description: Improve UI design using frontend-design skill
---

# UI Design Command

Enhance UI components using the frontend-designer agent and frontend-design skill.

## Instructions

1. **Audit Current State**
   - Review the specified component/page
   - Check typography, colors, animations
   - Identify areas for improvement

2. **Apply Design Principles**
   - Bold, distinctive fonts (not generic)
   - Cohesive color palette with personality
   - Purposeful animations and micro-interactions
   - Proper loading states and feedback

3. **Implement Improvements**
   - Update CSS/Tailwind styles
   - Add hover states and transitions
   - Implement dark mode if missing
   - Ensure responsive design

## Arguments

`$ARGUMENTS` should be:
- File path: Improve specific component
- "audit": Just audit, don't change
- Component name: Find and improve that component
- Empty: Show design recommendations for the project

## Design Checklist

- [ ] Distinctive typography (Space Grotesk, Plus Jakarta Sans)
- [ ] Bold accent color (not generic blue/gray)
- [ ] Hover states on interactive elements
- [ ] Loading skeletons
- [ ] Smooth transitions (200-300ms)
- [ ] Dark mode support
- [ ] Accessible contrast ratios

## Examples

```
/ui                           # Project design audit
/ui src/components/Button.tsx # Improve button component
/ui audit                     # Audit without changes
/ui "login page"              # Improve login page
```

## Output

- Current state assessment
- Specific improvements made
- Before/after comparison (conceptual)
- Additional recommendations
