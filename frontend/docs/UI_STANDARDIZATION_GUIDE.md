# UI Standardization Guide

## Design System Principles

### 1. **Visual Hierarchy** (Left → Right / Top → Bottom Priority)

**Toolbar & Headers:**
```
[Primary Input] | [Filters] | [View Options] ··· [Primary Actions] | [Secondary Actions] | [Utilities]
```

- **Left Section**: Input fields, filters (most used)
- **Middle Section**: View/display options
- **Right Section**: Actions and utilities (less frequently used)

### 2. **Grouping & Visual Separation**

- Use **vertical dividers** (`<div className="h-8 w-px bg-gray-300"></div>`) between logical groups
- Use **consistent spacing**: 8px grid (gap-2, gap-3, gap-4)
- Group related controls together

### 3. **Button Placement Standards**

**Modal Footers:**
```
[Cancel/Secondary] ··················· [Primary Action]
```
- Destructive/Cancel actions: LEFT
- Confirmatory/Primary actions: RIGHT
- Close buttons (×): Always top-right corner

**Toolbars:**
```
[Primary CTA] [Secondary Actions] ··· [Icon Buttons]
```
- Call-to-action buttons: LEFT of action group
- Icon-only utilities: RIGHT

### 4. **Size Consistency**

**Buttons:**
- Primary actions: `size="md"` (h-10, 40px)
- Secondary actions: `size="sm"` (h-8, 32px)
- Icon buttons: `variant="icon"` (h-8, w-8)

**Form Inputs:**
- Standard inputs: `h-10` (40px)
- Compact inputs: `h-8` (32px)
- Search bars: `h-10` with consistent padding

###5. **Color & Variant Standards**

**Button Variants:**
- `primary`: Main actions (blue background)
- `secondary`: Alternative actions (white background, gray border)
- `ghost`: Minimal styling, icon buttons
- `danger`: Destructive actions (red)
- `icon`: Square icon-only buttons

**State Indicators:**
- Active/Selected: `variant="primary"` or custom blue background
- Disabled: `disabled={true}` with opacity-50
- Locked/Special: Yellow (`bg-yellow-500`)

### 6. **Typography & Labels**

- **Button labels**: Short, action-oriented (Trace, Search, Apply)
- **Section headers**: Uppercase, tracked labels (`uppercase tracking-wide text-xs font-semibold`)
- **Helper text**: Gray-500, text-xs
- **Font sizes**: text-sm for most UI, text-xs for secondary info and checkboxes
- **Checkbox labels**: text-xs for consistency across all dropdowns

### 7. **Modal & Panel Standards**

**Full-Screen Modals:**
```tsx
<div className="fixed inset-0 bg-black/50 z-[9998]" onClick={handleClose} />
<div className="fixed inset-0 bg-white z-[9999] flex flex-col">
  <header>...</header>
  <main className="flex-1 overflow-auto">...</main>
  <footer>...</footer>
</div>
```

**Standard Modals (with Gradient Accent):**
```tsx
<div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
  <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col">
    <header>
      <div className="flex items-center justify-between px-4 py-2.5">
        <img src="/logo.png" alt="Logo" className="h-10" />
        <button onClick={onClose} className="w-9 h-9 flex items-center justify-center hover:bg-gray-100 text-gray-600 rounded transition-colors">×</button>
      </div>
      {/* Colorful gradient accent bar */}
      <div className="h-1 bg-gradient-to-r from-blue-500 via-teal-400 to-orange-400"></div>
    </header>
    <main className="flex-1 px-6 py-5 overflow-y-auto">...</main>
    <footer className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end gap-2">
      <Button variant="secondary">Cancel</Button>
      <Button variant="primary">Confirm</Button>
    </footer>
  </div>
</div>
```

**Side Panels (with Icon & Gradient Accent):**
```tsx
<div className={`absolute top-0 right-0 h-full w-80 bg-white shadow-2xl z-20 transform transition-transform ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
  <div className="flex flex-col h-full">
    <header className="flex-shrink-0">
      <div className="flex items-center justify-between px-4 py-2.5">
        <div className="flex items-center gap-2">
          {/* Gradient icon */}
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center">
            <svg>...</svg>
          </div>
          <h2 className="text-lg font-bold text-gray-800">Panel Title</h2>
        </div>
        <button onClick={onClose} className="w-9 h-9 flex items-center justify-center hover:bg-gray-100 text-gray-600 rounded transition-colors">×</button>
      </div>
      {/* Colorful gradient bar */}
      <div className="h-1 bg-gradient-to-r from-green-500 via-teal-400 to-blue-500"></div>
    </header>
    <main className="flex-grow overflow-y-auto px-4 py-4 space-y-5">...</main>
    <footer className="flex-shrink-0 px-4 py-3 border-t border-gray-200 bg-gray-50 flex justify-end gap-2">
      <Button variant="secondary">Reset</Button>
      <Button variant="primary">Apply</Button>
    </footer>
  </div>
</div>
```

### 8. **Form Layout Standards**

**Vertical Form (Side panels, modals):**
```tsx
<div className="space-y-6"> {/* 24px between sections */}
  <div>
    <label className="font-semibold block mb-1">1. Field Name</label>
    <input />
    <p className="text-xs text-gray-500 mt-1">Helper text</p>
  </div>
</div>
```

**Horizontal Form (Toolbars):**
```tsx
<div className="flex items-center gap-3">
  <label className="text-sm font-medium">Label:</label>
  <input className="w-48" />
</div>
```

### 9. **Icon Guidelines**

- Use Heroicons (consistent with existing codebase)
- Standard size: `w-5 h-5` (20px)
- Color: Inherit from button/parent
- Always wrap in proper button/clickable element

### 10. **Accessibility Standards**

- All buttons must have `title` attribute
- Form inputs need associated labels (`htmlFor` / `id`)
- Disabled states must be visually obvious
- Focus states: `focus:ring-2 focus:ring-primary-600`

---

## Component-Specific Patterns

### Toolbar
- **Structure**: `justify-between` with left and right sections
- **Left**: Search + Filters + View Options
- **Right**: Primary Actions + Icon Utilities
- **Dividers**: Between logical groups

### Import Modal
- **Tabs**: Horizontal tabs at top
- **Content**: Conditional rendering based on active tab
- **Footer**: Only visible for JSON tab (Cancel | Apply)

### Interactive Trace Panel
- **Type**: Side panel (slide from right)
- **Header**: Green gradient icon + colorful accent bar
- **Form**: Uppercase tracked labels, contextual help text
- **Footer**: Reset (left) | Apply Trace (right)

### Detail Search Modal
- **Type**: Full-screen overlay
- **Header**: Sticky with search bar
- **Content**: Resizable split (results top, DDL bottom)
- **No footer**: Close button in header only

### Info Modal
- **Type**: Standard centered modal with logo + gradient accent
- **Icons**: Simple gray circles (bg-gray-100) with gray icons - not colorful gradients
- **Content**: Feature cards with icons and descriptions
- **Footer**: LinkedIn credit (left) | "Got it!" button (right)

---

## Implementation Checklist

When creating/updating a component:

- [ ] Follows left-right visual hierarchy
- [ ] Uses consistent spacing (8px grid)
- [ ] Buttons follow placement standards
- [ ] Sizes are consistent (h-10 for main, h-8 for compact)
- [ ] Variants match purpose (primary/secondary/ghost/danger)
- [ ] Has proper grouping with dividers
- [ ] All buttons have titles
- [ ] Focus states are defined
- [ ] Disabled states are clear
- [ ] Responsive (wraps properly on small screens)

---

## Color Palette Reference

**Primary Actions:** `bg-primary-600 hover:bg-primary-700 text-white`
**Secondary Actions:** `bg-white border border-gray-300 hover:bg-gray-50 text-gray-800`
**Ghost Actions:** `bg-transparent hover:bg-gray-100 text-gray-600`
**Danger Actions:** `bg-red-600 hover:bg-red-700 text-white`
**Disabled:** `opacity-50 cursor-not-allowed`

**Borders:** `border-gray-200` (light), `border-gray-300` (standard)
**Text:** `text-gray-800` (primary), `text-gray-600` (secondary), `text-gray-500` (tertiary)
**Backgrounds:** `bg-white`, `bg-gray-50`, `bg-gray-100`

---

**Version:** 1.0
**Last Updated:** 2025-10-31
