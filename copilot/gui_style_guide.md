# GUI Style Guide — Studio Library Aesthetic

This project's GUI follows a **professional Studio Library style**, inspired by Maya's Studio Library with **enhanced thumbnail system** and modular architecture. All components should follow these visual and UX principles.

---

## 🎨 Color Palette

| Element                      | Hex Code  | Purpose                             |
|------------------------------|-----------|-------------------------------------|
| Background (default)         | #2e2e2e   | Base background color               |
| Background (darker panels)   | #393939   | Secondary background (sidebars)     |
| Background (cards)           | #2e2e2e   | Animation card backgrounds          |
| Selected item background     | #3d5afe   | Folder/card selection (dark blue)   |
| Primary accent color         | #4a90e2   | Primary buttons, active states      |
| Folder icons / accent color  | #fbc02d   | Folder icons, highlights (yellow)   |
| Text (primary)               | #eeeeee   | Main text color                     |
| Text (secondary)             | #cccccc   | Secondary labels, metadata          |
| Text (tertiary)              | #888888   | Disabled text, placeholders         |
| Divider lines                | #555555   | Subtle dividers, borders            |
| Success indicators           | #51cf66   | Connected status, successful ops    |
| Warning indicators           | #ffd43b   | Warnings, compatibility issues      |
| Error indicators             | #ff6b6b   | Errors, failed operations           |

---

## 🖼️ Thumbnail System Guidelines

### **Animation Cards (140x140)**
- **Thumbnail size:** Fixed 140x140px with centered content (optimized for card space)
- **Background:** Dark grey (#2e2e2e) for empty/placeholder areas
- **Aspect ratio:** Preserve original aspect ratio, center in frame
- **Loading states:** Show subtle loading indicator during refresh
- **Error states:** Simple icon placeholder for missing/failed thumbnails
- **Hover effects:** Subtle brightness increase, action buttons appear

### **Metadata Panel (300x300)**
- **Large preview:** 300x300px for detailed viewing
- **Update button:** Prominently placed "Update Thumbnail" button
- **Cache clearing:** Aggressive refresh without flicker
- **Fallback display:** Larger placeholder with animation icon
- **Quality:** High-resolution capture (512x512) scaled appropriately

### **Thumbnail Refresh Behavior**
- **Immediate updates:** No delay between capture and display
- **Cross-component sync:** All thumbnail displays update simultaneously  
- **Cache management:** Automatic cache clearing for instant refresh
- **Visual feedback:** Brief status indication during update process
- **Error recovery:** Graceful fallback to placeholder on capture failure

---

## 🗂️ Folder Tree Guidelines

### **Visual Design**
- **Background:** Solid dark grey (`#2e2e2e`), no alternating row colors
- **Selection highlight:** Dark blue tint (`#3d5afe`), no bright white highlights
- **Icons:** Flat yellow folder icons (`#fbc02d`), no gradients or 3D effects
- **Text:** Light grey (`#eeeeee`) with consistent typography
- **Padding:** Consistent padding (10-12px), comfortable click targets
- **Hover states:** Subtle background lightening to `#3a3a3a`

### **Interaction Design**
- **Drag & Drop:** 
  - Allow dragging animations into folders for organization
  - Allow dragging folders into each other for nesting
  - Show subtle highlight around target folder when dragging
  - Prevent dragging the **"🎬 All Animations"** root category
  - Smooth animation feedback for successful drops

- **Context Menus:**
  - Right-click options: Rename, Delete, Create New Folder
  - Disable Rename/Delete for "🎬 All Animations"
  - Consistent menu styling with dark theme

### **Hierarchy Rules**
- **Root Category:** "🎬 All Animations" always appears at the top
- **Custom Folders:** All user-created folders appear below root
- **Folder Counts:** Show animation count in parentheses: "Walk Cycles (15)"
- **Expand/Collapse:** Smooth animations, remember state between sessions

---

## 🎛️ Animation Grid Guidelines

### **Card Layout**
- **Card size:** Fixed 160x220px for consistent grid alignment
- **Thumbnail area:** 140x140px at top of card (optimized for maximum visual impact)
- **Metadata area:** Remaining space below thumbnail for title and info
- **Spacing:** 1px margins between cards for ultra-tight Studio Library grid (almost touching)
- **Shadow effects:** Subtle drop shadow on hover for depth

### **Card Content**
- **Title:** Bold, 11px font, center-aligned, max 2 lines with ellipsis
- **Frame count:** Small text below title, light grey color
- **Rig type:** Color-coded indicators (🟢 Rigify, 🔵 Auto-Rig Pro, 🟡 Mixamo)
- **Performance indicators:** ⚡ for instant .blend files, ⏳ for legacy JSON
- **Action buttons:** Appear on hover: Apply, Delete, Rename

### **Interactive States**
- **Default:** Clean, minimal appearance with subtle shadows
- **Hover:** Slight brightness increase, action buttons slide in
- **Selected:** Blue border (#3d5afe), maintains thumbnail visibility
- **Loading:** Subtle spinner overlay during thumbnail refresh
- **Error:** Grayed out appearance with error icon

---

## 🔍 Toolbar & Search Guidelines

### **Layout**
- **Height:** Fixed 60px for consistent header appearance
- **Background:** Darker panel color (#393939) with bottom border
- **Button spacing:** 12px between elements for clean organization
- **Search prominence:** 300px width search box with clear placeholder

### **Controls**
- **Primary actions:** "Connect to Blender", "Extract Animation" 
- **Search box:** Real-time filtering with instant results
- **Filter dropdowns:** Tag and rig type filters with clear labels
- **Status indicators:** Connection status with color-coded dots

### **Visual Feedback**
- **Connection status:** Red (●) disconnected, Green (●) connected
- **Button states:** Clear hover/pressed/disabled states
- **Loading states:** Progress indicators for long operations
- **Statistics:** Show filtered/total counts in subtle text

---

## 📋 Metadata Panel Guidelines

### **Layout Structure**
- **Header:** "Animation Details" with bold typography
- **Sections:** Grouped information with subtle separators
- **Scroll support:** Vertical scrolling for long metadata
- **Action placement:** Prominent "Update Thumbnail" button

### **Information Hierarchy**
- **Primary:** Animation name, large thumbnail preview
- **Secondary:** Technical details (frames, bones, keyframes)
- **Tertiary:** Creation info, usage statistics, tags
- **Performance:** Storage method indicators with visual emphasis

### **Thumbnail Integration**
- **Large preview:** 300x300px centered at top
- **Update button:** Blue primary button below preview
- **Refresh feedback:** Brief loading state during update
- **Quality display:** Sharp, high-resolution thumbnail rendering

---

## 🎨 Typography Standards

### **Font Hierarchy**
- **Primary font:** "Segoe UI", Arial, sans-serif for Windows compatibility
- **Headers:** 12-14px, bold weight, slightly increased line height
- **Body text:** 11px, normal weight, good readability
- **Small text:** 9-10px for metadata, captions, secondary info
- **Monospace:** For technical data like bone names, frame numbers

### **Text Colors**
- **Primary text:** #eeeeee for main content
- **Secondary text:** #cccccc for labels and descriptions  
- **Tertiary text:** #888888 for subtle information
- **Interactive text:** #4a90e2 for links and active elements
- **Status text:** Color-coded based on state (success/warning/error)

---

## 🔠 Component-Specific Guidelines

### **Animation Cards**
```css
/* Card structure */
card_size: 160x220px
thumbnail_area: 140x140px (top, optimized for visual prominence)
metadata_area: auto (bottom, compact layout)
border_radius: 8px
margin: 1px (ultra-tight Studio Library grid - almost touching)

/* Interactive states */
hover: background lighten 5%, show action buttons
selected: #3d5afe border, maintain readability
loading: subtle spinner overlay
```

### **Folder Tree**
```css
/* Tree items */
item_height: 36px
padding: 10px 12px
border_radius: 6px
font_size: 12px

/* Selection states */
selected: #3d5afe background
hover: #3a3a3a background (not selected)
root_item: bold font, larger size (13px)
```

### **Toolbar**
```css
/* Toolbar layout */
height: 60px
padding: 8px 12px
background: #393939
border_bottom: 1px solid #555

/* Button styling */
primary_button: #4a90e2 background, white text
secondary_button: #666 background, border on hover
search_box: 300px width, #4a4a4a background
```

---

## 🧑‍💻 UX Interaction Principles

### **Response Times**
- **Thumbnail updates:** Immediate visual feedback (< 0.1s)
- **Search filtering:** Real-time results as user types
- **Folder navigation:** Instant switching between folders
- **Animation application:** Clear progress indication for 0.5s operations

### **Visual Feedback**
- **Hover states:** Subtle, not overwhelming
- **Loading states:** Clear but non-intrusive indicators
- **Success feedback:** Brief, positive confirmation
- **Error handling:** Clear, actionable error messages

### **Accessibility**
- **Color contrast:** Minimum 4.5:1 ratio for all text
- **Focus indicators:** Clear keyboard navigation support
- **Screen reader:** Proper ARIA labels and semantic markup
- **Keyboard shortcuts:** Standard shortcuts (Ctrl+F for search, etc.)

---

## 🛑 Protected Elements

### **Non-Deletable/Non-Modifiable**
- **"🎬 All Animations"** root category:
  - Must always remain at the top of folder tree
  - Cannot be deleted, renamed, or moved
  - Should show total animation count
  - Serves as "show all" filter

### **Consistent Branding**
- **Color scheme:** Maintain dark theme throughout
- **Icon style:** Flat, monochrome icons with consistent sizing  
- **Animation style:** Smooth transitions, no jarring movements
- **Typography:** Consistent font sizing and hierarchy

---

## 🔜 Future Enhancements

### **Planned Visual Improvements**
- **Video previews:** Hover-to-play animation loops in cards
- **Advanced thumbnails:** Multiple viewpoints, bone visualization
- **Theme customization:** User-selectable color schemes
- **Accessibility mode:** High contrast, larger text options

### **Interaction Enhancements**
- **Keyboard navigation:** Full keyboard control of interface
- **Gesture support:** Touch/trackpad gestures for navigation
- **Contextual menus:** Smart right-click options based on selection
- **Quick actions:** Hotkeys for common operations

---

## ✅ Style Implementation Checklist

When implementing new components:

- [ ] Use established color palette consistently
- [ ] Follow 140x140 thumbnail sizing for cards (optimized layout)
- [ ] Implement proper hover/selected states
- [ ] Include loading states for async operations
- [ ] Support dark theme throughout
- [ ] Add proper keyboard navigation
- [ ] Test with large datasets (1000+ items)
- [ ] Verify thumbnail refresh works correctly
- [ ] Ensure component isolation (no direct dependencies)
- [ ] Follow typography hierarchy
- [ ] Include proper error states
- [ ] Test cross-component thumbnail updates

This style guide ensures consistent, professional appearance across all components while supporting the real-time thumbnail system and modular architecture.