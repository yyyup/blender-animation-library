# GUI Style Guide — Studio Library Aesthetic

This project’s GUI follows a **professional Studio Library style**, inspired by Maya's Studio Library. All components should follow these visual and UX principles.

---

## 🎨 Color Palette

| Element                      | Hex Code  | Purpose                             |
|------------------------------|-----------|-------------------------------------|
| Background (default)         | #2e2e2e   | Base background color               |
| Background (darker panels)   | #252525   | Secondary background (e.g., sidebars) |
| Selected item background     | #3d5afe   | Folder selection (dark blue tint)   |
| Folder icons / accent color  | #fbc02d   | Folder icons, highlights (yellow)   |
| Text (primary)               | #eeeeee   | Main text color                     |
| Text (secondary)             | #bdbdbd   | Secondary labels                    |
| Divider lines (optional)     | #424242   | Subtle dividers (minimize usage)    |

---

## 🗂️ Folder Tree Guidelines
- **Background:** Solid dark grey (`#2e2e2e`), no alternating row colors.
- **Selection highlight:** Dark blue tint (`#3d5afe`), no bright white highlights.
- **Icons:** Flat yellow folder icons (`#fbc02d`), no gradients.
- **Text:** Light grey (`#eeeeee`).
- **Padding:** Consistent padding (8-12px), no tight layouts.
- **Drag & Drop:**
   - Allow dragging folders into each other to create nested folders.
   - Show subtle highlight around the target folder when dragging.
   - Prevent dragging the **"All Animations"** root.
   - Folder reordering should be animated (smooth drop effect).
- **Right-click Context Menu:** (Future)
   - Options: Rename, Delete, Create New Folder.
   - Disable Rename/Delete for "All Animations."

---

## 🎛️ Animation Grid (Existing, Keep Style)
- Thumbnails with a clean shadow.
- Consistent card margins and padding.
- Rig icons and frame counts visible but unobtrusive.
- Hover highlights only slightly brighten the card.

---

## 🔠 Typography
- Use **Sans-serif fonts** (Qt default or Roboto/Helvetica if applicable).
- Keep text sizes consistent across folders and grid.
- Avoid large or bold fonts unless necessary.

---

## 🧑‍💻 UX Guidelines
- Minimal visual noise.
- No unnecessary borders.
- Smooth hover effects, not harsh color changes.
- Keep interaction cues clear but subtle.

---

## 🛑 Non-Deletable Category
The **"All Animations"** category at the top of the folder tree:
- Must always remain present.
- Cannot be deleted or renamed.
- Should always appear **above all other folders**, even after drag/drop.

---

## 🔜 Future Improvements
- Add right-click context menus.
- Smooth expand/collapse animations.
- Customizable color themes.
