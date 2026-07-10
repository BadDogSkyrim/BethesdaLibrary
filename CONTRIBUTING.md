# Contributing to Bethesda Modding Library

Thank you for your interest in contributing! This library consolidates community knowledge about Bethesda modding, and contributions are welcome.

## How to Contribute

### 1. Fork & Clone
```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/yourusername/bethesda-library.git
cd bethesda-library
```

### 2. Set Up Development Environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate it
.venv\Scripts\Activate.ps1

# Install MkDocs
pip install mkdocs-material

# Run local server
mkdocs serve
```

Visit http://localhost:8000 to preview your changes.

### 3. Make Changes

All documentation files are in the `docs/` directory:
- Add new files or edit existing markdown files
- Follow existing structure and formatting
- Include code examples where relevant
- Cross-reference related sections

### 4. Test Locally

```powershell
# Check that site builds without errors
mkdocs build

# Preview changes
mkdocs serve
```

### 5. Submit Pull Request

```bash
# Commit your changes
git add .
git commit -m "Add documentation for [topic]"

# Push to your fork
git push origin main

# Open a Pull Request on GitHub
```

## What to Contribute

### High Priority
- **Missing Files** - We have 60+ files planned but not yet created (see [LIBRARY_STRUCTURE_PLAN.md](LIBRARY_STRUCTURE_PLAN.md))
- **Code Examples** - Complete, working PyNifly/esplib examples
- **Game-Specific Details** - Skyrim LE/SE/FO4 differences
- **Debugging Solutions** - Real-world problems you've solved

### Also Welcome
- **Corrections** - Fix errors, outdated information
- **Clarifications** - Improve explanations, add missing context
- **New Sections** - Propose additional topics (open an issue first)
- **Images/Diagrams** - Visual aids (NIF structure diagrams, workflow charts)

## Style Guidelines

### Markdown
- Use headers hierarchy: `#` for page title, `##` for sections, `###` for subsections
- Use code fences with language specifiers: ` ```python `
- Link to other pages: `[text](../category/file.md)`
- Link to sections: `[text](file.md#section-heading)`

### Code Examples
- Must be complete and runnable (no `...` placeholders)
- Include imports and setup
- Add comments explaining non-obvious steps
- Show actual paths (use `C:\Modding\` as example)

### Game-Specific Information
- Always specify which game(s) a detail applies to
- Call out differences explicitly
- Use admonitions for important notes:
  ```markdown
  !!! warning "Skyrim LE Only"
      This feature is not available in SE.
  ```

### Technical Accuracy
- Verify information from official sources or working code
- Cite sources for binary format specifications
- Mark uncertain information clearly: "Unconfirmed:" or "Needs verification:"

## File Organization

```
docs/
├── index.md                    # Home page
├── file-formats/               # Format specifications
├── game-specific/              # Game differences
│   └── fallout4/              # FO4 gets subdirectory
├── tools/                      # Tool documentation
│   ├── pynifly/
│   └── esplib/
├── workflows/                  # How-to guides
├── debugging/                  # Troubleshooting
├── reference/                  # Lookup tables
└── ai-reference/              # Structured data
```

Add new files to appropriate directories. Update `mkdocs.yml` navigation if adding new pages.

## Scope

**In Scope:**
- Skyrim LE, Skyrim SE, Fallout 4
- PyNifly, esplib, NifSkope (brief)
- File formats: ESP/ESM, NIF, HKX, TRI, DDS, BGSM, HDT XML, BSA, PEX
- Python workflows (not Pascal/xEdit scripting)

**Out of Scope:**
- Other Bethesda games (FO76, FO3, FONV, Starfield)
- Creation Kit detailed workflows
- Pascal/xEdit scripting
- Game modding unrelated to file formats/Python tools

## Questions?

- **Bug Reports/Feature Requests** - Open a GitHub issue
- **Discussions** - Use GitHub Discussions
- **Unclear Contribution Path** - Open an issue asking for guidance

## Code of Conduct

- Be respectful and constructive
- Focus on technical accuracy
- Help newcomers learn
- Give credit where due (cite sources, acknowledge contributors)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (to be determined - add LICENSE file).

---

Thank you for helping make Bethesda modding more accessible! 🎮
