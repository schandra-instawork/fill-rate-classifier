# File Structure Cleanup - TODO

## **🏗️ Proposed File Structure Cleanup for LLM Navigation**

### **Current Issues with LLM Navigation:**
- Mixed file types in root directory
- Inconsistent naming patterns
- Configuration files scattered
- Test files mixed with source code
- Documentation files cluttering root

### **Proposed Structure (LLM-Optimized):**

```
fill-rate-classifier/
├── 📁 src/                          # Main source code (LLMs focus here)
│   ├── 📁 api/                      # API layer
│   ├── 📁 classification/           # Core classification engine
│   ├── 📁 models/                   # Data models (LLMs reference these)
│   ├── 📁 evaluation/               # RAGAS evaluation framework
│   ├── 📁 utils/                    # Shared utilities
│   └── __init__.py
├── 📁 tests/                        # All test files (LLMs can ignore)
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_env_loading.py
│   └── 📁 unit/
│       └── test_*.py
├── 📁 config/                       # Configuration files (LLMs reference)
│   ├── classification_rules.yaml
│   ├── app_config.yaml
│   └── email_templates.yaml
├── 📁 data/                         # Data files (LLMs can ignore)
│   ├── raw/
│   │   └── company_ids_and_other.csv
│   └── output/
├── 📁 scripts/                      # Utility scripts (LLMs can ignore)
├── 📁 docs/                         # Documentation (LLMs reference)
│   ├── README.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── DEVELOPMENT.md
├── 📁 .cursor/                      # Cursor rules (LLMs ignore)
├── 📁 .gitignore
├── 📄 requirements.txt
├── 📄 setup.py
├── 📄 pytest.ini
└── 📄 .env
```

### **Implementation Plan:**

#### **Phase 1: Move Files to Proper Locations**
```bash
# Create new directories
mkdir -p docs
mkdir -p tests/unit

# Move documentation files
mv README.md docs/
mv *.md docs/  # Move all markdown files except README

# Move test files
mv test_*.py tests/
mv cursor_*.py tests/

# Move configuration files
mv *.yaml config/ 2>/dev/null || true

# Move scripts
mv scripts/*.py scripts/ 2>/dev/null || true
```

#### **Phase 2: Update Import Paths**
- Update all import statements to reflect new structure
- Update `setup.py` to point to `src/` directory
- Update `pytest.ini` to use new test structure

#### **Phase 3: Update Documentation**
- Update all file path references in documentation
- Update dependency documentation to reflect new structure
- Create navigation guides for LLMs

### **Benefits for LLMs:**
1. **Faster Navigation** - LLMs can focus on `src/` for code understanding
2. **Better Context Understanding** - Related files are grouped together
3. **Efficient File Discovery** - Clear file purposes from location

### **Files to Move:**
- `README.md` → `docs/README.md`
- `test_*.py` → `tests/`
- `cursor_*.py` → `tests/`
- `*.md` → `docs/` (except README)
- `*.yaml` → `config/`

### **Files to Keep in Root:**
- `requirements.txt`
- `setup.py`
- `pytest.ini`
- `.env`
- `.gitignore`

**Status:** TODO - Implement when time permits
**Priority:** Medium
**Estimated Time:** 2-3 hours 