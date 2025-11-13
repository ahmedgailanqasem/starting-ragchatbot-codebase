# Development Documentation

This document covers both code quality improvements and frontend enhancements for the RAG chatbot codebase.

---

# Part 1: Code Quality Tools Implementation

## Overview
This section describes the code quality tools and development workflow improvements added to the RAG chatbot codebase.

## Changes Made

### 1. Code Quality Tools Added

Added the following development dependencies to `pyproject.toml`:
- **Black** (>=24.0.0) - Automatic code formatter for Python
- **isort** (>=5.13.0) - Import statement organizer
- **Flake8** (>=7.0.0) - Code linting and style checking
- **mypy** (>=1.8.0) - Static type checking
- **pytest** (>=8.0.0) - Testing framework
- **pytest-cov** (>=4.1.0) - Code coverage reporting

### 2. Configuration Files

#### pyproject.toml
Added comprehensive configuration sections:

**Black Configuration:**
- Line length: 88 characters
- Target Python version: 3.13
- Excludes: .venv, build, dist, chroma_db

**isort Configuration:**
- Profile: black (compatible with Black formatter)
- Line length: 88
- Multi-line output mode: 3 (vertical hanging indent)

**mypy Configuration:**
- Python version: 3.13
- Enabled warnings for return types, unused configs, redundant casts
- Strict equality checking
- Non-blocking for untyped definitions (gradual typing approach)

**pytest Configuration:**
- Test path: backend/tests/
- Coverage reports: terminal + HTML
- Verbose output enabled

#### .flake8
Created `.flake8` configuration file:
- Max line length: 88 (Black compatible)
- Ignores: E203, W503, E501 (Black-compatible settings)
- Excludes: .venv, build, dist, chroma_db, cache directories

### 3. Development Scripts

Created `scripts/` directory with executable shell scripts:

#### format.sh
Automatically formats all Python code:
- Runs `isort` to organize imports
- Runs `black` to format code
- Non-destructive - makes changes to files

**Usage:** `./scripts/format.sh`

#### lint.sh
Runs linting checks:
- Flake8 for style violations
- mypy for type checking
- Shows issues without failing

**Usage:** `./scripts/lint.sh`

#### check.sh
Validates code quality without making changes:
- Checks import sorting (isort --check-only)
- Checks code formatting (black --check)
- Runs Flake8 linting
- Runs mypy type checking
- Exits with error if checks fail (CI/CD friendly)

**Usage:** `./scripts/check.sh`

#### test.sh
Runs test suite with coverage:
- Executes pytest on backend/tests/
- Generates coverage reports (terminal + HTML)
- HTML report saved to htmlcov/index.html

**Usage:** `./scripts/test.sh`

#### quality.sh
Full quality pipeline:
- Step 1: Format code
- Step 2: Run linting
- Step 3: Run tests
- Comprehensive quality check

**Usage:** `./scripts/quality.sh`

### 4. Code Formatting Applied

All Python files in the codebase have been formatted:
- **14 files reformatted** with Black
- **14 files fixed** with isort
- Consistent code style throughout the project
- Properly organized imports

Files formatted:
- backend/config.py
- backend/models.py
- backend/session_manager.py
- backend/app.py
- backend/rag_system.py
- backend/ai_generator.py
- backend/search_tools.py
- backend/document_processor.py
- backend/vector_store.py
- backend/tests/conftest.py
- backend/tests/test_ai_generator.py
- backend/tests/test_rag_integration.py
- backend/tests/test_live_system.py
- backend/tests/test_search_tools.py
- main.py

### 5. Installation

To install the development dependencies:
```bash
uv sync --extra dev
```

## Benefits

1. **Consistent Code Style**: Black ensures all code follows the same formatting rules
2. **Organized Imports**: isort keeps imports clean and consistently organized
3. **Early Bug Detection**: Flake8 and mypy catch potential issues before runtime
4. **Test Coverage**: pytest-cov helps identify untested code paths
5. **Developer Productivity**: Automated formatting saves time on code reviews
6. **CI/CD Ready**: check.sh script can be integrated into continuous integration pipelines

## Workflow Integration

### Before Committing Code:
```bash
# Format your code
./scripts/format.sh

# Check for issues
./scripts/check.sh

# Run tests
./scripts/test.sh
```

### Quick Quality Check:
```bash
# Run everything at once
./scripts/quality.sh
```

### CI/CD Integration:
Add to your CI pipeline:
```bash
uv sync --extra dev
./scripts/check.sh
./scripts/test.sh
```

## Notes

- All scripts use `uv run` to execute tools in the project's virtual environment
- Scripts are made executable with proper permissions
- Configuration is compatible across all tools (Black + isort + Flake8)
- Type checking with mypy is non-blocking to allow gradual adoption
- Coverage reports are generated in `htmlcov/` directory (gitignored)

## Future Enhancements

Potential additions for further quality improvements:
- Pre-commit hooks for automatic formatting
- pylint for additional code analysis
- bandit for security vulnerability scanning
- pre-push hooks for running tests
- GitHub Actions workflow for automated checks

---

# Part 2: Frontend Changes - Dark/Light Theme Toggle

## Overview
Added a theme toggle button that allows users to switch between dark and light themes with smooth transitions and persistent theme preferences.

## Files Modified

### 1. `frontend/index.html`
- **Location:** Lines 13-21 (after `<body>` tag)
- **Changes:**
  - Added theme toggle button with sun and moon SVG icons
  - Button positioned as fixed element in top-right corner
  - Includes proper ARIA labels for accessibility
  - Added `id="themeToggle"` for JavaScript control

### 2. `frontend/style.css`
- **Location:** Lines 8-44 (CSS Variables section)
- **Changes:**
  - Enhanced dark theme variables with clearer comments
  - Added complete light theme color palette using `[data-theme="light"]` selector
  - Light theme features:
    - Light background: `#f8fafc`
    - White surfaces: `#ffffff`
    - Dark text: `#0f172a` for primary text
    - Proper contrast ratios for accessibility
    - Adjusted shadows for light background

- **Location:** Line 56 (body styles)
- **Changes:**
  - Added smooth transition for background-color and color properties

- **Location:** Lines 724-787 (Theme Toggle Button styles)
- **Changes:**
  - Fixed positioning in top-right corner (1.5rem from edges)
  - Circular button design (48px diameter)
  - Smooth hover effects with scale transformation
  - Focus ring for keyboard accessibility
  - Icon switching logic using display property
  - Sun icon (yellow) visible in dark mode
  - Moon icon (blue) visible in light mode
  - Universal transitions for all theme-dependent properties

### 3. `frontend/script.js`
- **Location:** Lines 8, 19, 22 (Initialization)
- **Changes:**
  - Added `themeToggle` to DOM elements
  - Added `initializeTheme()` call on page load

- **Location:** Lines 38-47 (Event Listeners)
- **Changes:**
  - Added click event listener for theme toggle
  - Added keyboard accessibility (Enter and Space keys)

- **Location:** Lines 234-263 (Theme Functions)
- **Changes:**
  - `initializeTheme()`: Checks localStorage for saved preference, defaults to dark
  - `toggleTheme()`: Switches between light and dark themes
  - `setTheme(theme)`: Applies theme by setting/removing `data-theme` attribute
  - LocalStorage integration for persistent theme preferences
  - Dynamic ARIA label updates for accessibility

## Features Implemented

### 1. Visual Design
- **Button Design:**
  - Clean, circular button with 48px diameter
  - Fixed position in top-right corner
  - Semi-transparent background matching current theme
  - Border with theme-appropriate color
  - Smooth hover animation with scale effect

- **Icons:**
  - Sun icon: Displayed in dark mode (yellow color `#fbbf24`)
  - Moon icon: Displayed in light mode (blue color `#60a5fa`)
  - Icons are 24x24px SVG graphics
  - Smooth fade transition when switching

### 2. Theme Switching
- **Dark Theme (Default):**
  - Deep blue background (`#0f172a`)
  - Slate surfaces (`#1e293b`)
  - Light text (`#f1f5f9`)
  - Designed for reduced eye strain in low-light conditions

- **Light Theme:**
  - Clean white/light gray palette
  - White surfaces on light gray background
  - Dark text for optimal readability
  - Professional, modern appearance

### 3. Transitions
- **Smooth Animations:**
  - 0.3s ease transitions for all color changes
  - Button hover/active states with transform effects
  - Theme changes affect all elements simultaneously
  - No jarring visual changes

### 4. Accessibility
- **Keyboard Navigation:**
  - Button is keyboard focusable
  - Enter and Space keys trigger theme toggle
  - Visible focus ring (blue glow)

- **Screen Readers:**
  - Proper ARIA labels
  - Label updates dynamically: "Toggle theme" / "Switch to dark theme" / "Switch to light theme"
  - Semantic button element

### 5. Persistence
- **LocalStorage:**
  - Theme preference saved automatically
  - Preference persists across page reloads
  - Preference persists across browser sessions
  - Defaults to dark theme if no preference saved

## Technical Implementation

### CSS Variables Approach
Both themes use the same variable names, allowing seamless switching without JavaScript manipulation of individual elements. Variables include:
- `--primary-color`, `--primary-hover`
- `--background`, `--surface`, `--surface-hover`
- `--text-primary`, `--text-secondary`
- `--border-color`
- `--user-message`, `--assistant-message`
- `--shadow`, `--focus-ring`

### Data Attribute Strategy
- Theme controlled via `data-theme="light"` attribute on `<html>` element
- Dark theme: No attribute (default)
- Light theme: `data-theme="light"`
- CSS selectors target `[data-theme="light"]` for overrides

### Icon Visibility Toggle
CSS controls which icon is visible:
```css
/* Dark mode: Show sun */
.theme-toggle .sun-icon { display: block; }
.theme-toggle .moon-icon { display: none; }

/* Light mode: Show moon */
[data-theme="light"] .theme-toggle .sun-icon { display: none; }
[data-theme="light"] .theme-toggle .moon-icon { display: block; }
```

## User Experience

### How It Works
1. User clicks the theme toggle button (or uses keyboard)
2. Theme switches instantly with smooth transitions
3. New preference saves to localStorage
4. All UI elements update their colors automatically
5. Icon in button changes to reflect current mode
6. Preference remembered for future visits

### Visual Feedback
- Hover: Button scales up slightly (1.1x) with blue border highlight
- Active: Button scales down (0.95x) for click feedback
- Smooth color transitions throughout interface
- Icon changes immediately upon click

## Browser Compatibility
- Works in all modern browsers (Chrome, Firefox, Safari, Edge)
- Uses standard CSS custom properties
- LocalStorage API (widely supported)
- SVG icons (universal support)
- Gracefully degrades to dark theme in older browsers

## Maintenance Notes
- To modify colors: Edit CSS variables in `:root` and `[data-theme="light"]`
- To change button position: Modify `.theme-toggle` top/right properties
- To adjust transition speed: Modify transition duration values
- Default theme: Change in `initializeTheme()` function

## Testing Recommendations
1. Toggle theme multiple times - verify smooth transitions
2. Reload page - verify theme persists
3. Test keyboard navigation (Tab to button, Enter/Space to toggle)
4. Test on mobile devices - verify button doesn't overlap content
5. Verify contrast ratios meet WCAG AA standards
6. Test with screen readers - verify ARIA labels work

## Future Enhancement Opportunities
- Auto-detect system theme preference using `prefers-color-scheme`
- Add more theme options (e.g., sepia, high contrast)
- Animate icon transition with rotation or fade
- Add theme preview/tooltip on hover
- Sync theme across multiple tabs using localStorage events
