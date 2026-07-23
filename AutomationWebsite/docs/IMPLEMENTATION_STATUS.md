# Culvert Design Module - Technical Implementation Notes

## ✅ **Completed So Far**

### 1. **Bilingual Infrastructure (Todos 1-2)** ✓
- Created `static/translations/i18n.json` with EN/FA translations
- Added `static/css/rtl.css` for RTL/LTR support
- Created `static/js/i18n.js` for language switching
- Updated `layout.html` with language toggle
- Added Vazir font for Persian text
- Language preference stored in localStorage

### 2. **Project Structure** ✓
- Created all necessary directories
- Copied CSV tables to `data/culvert_tables/`
- Copied DWG templates to `Files/culvert_templates/`
- Set up models hierarchy (core, validators, repositories, calculators, dwg, services, exceptions)

### 3. **Dependencies** ✓
- Updated `requirements.txt` with:
  - `ezdxf==1.1.4` (DXF file handling - NO AutoCAD!)
  - `jdatetime==5.0.0` (Persian dates)
- Both packages installed and tested

---

## 🔍 **Important Discovery: DWG vs DXF**

### **Issue Found:**
- DWG files are **binary format** (proprietary AutoCAD)
- `ezdxf` library **cannot read DWG** files directly
- `ezdxf` works with **DXF format** (text-based, open standard)

### **Solution:**
✅ **Use DXF format for templates and output**

**Why this works:**
1. DXF is fully compatible with AutoCAD
2. Users can open DXF files in AutoCAD normally
3. No AutoCAD dependency for server processing
4. Pure Python solution with ezdxf

### **Next Steps:**
1. Convert existing DWG templates to DXF format (one-time task)
2. Store DXF templates in `Files/culvert_templates/`
3. Process with ezdxf (reads/writes DXF)
4. Output DXF files for users to download
5. Users open DXF in AutoCAD (works perfectly!)

### **Conversion Options:**
- **Option 1**: Use AutoCAD (File -> Save As -> DXF)
- **Option 2**: Use ODA File Converter (free tool)
- **Option 3**: Online converters

---

## 📋 **Revised Implementation Plan**

### **Phase 1: Foundation** (In Progress)
- [x] Bilingual infrastructure
- [x] Directory structure
- [x] Dependencies installed
- [ ] **Convert DWG templates to DXF** ← **NEXT STEP**
- [ ] Test ezdxf with DXF files
- [ ] Add culvert translations to i18n.json

### **Phase 2: Core Models & Services**
- [ ] Domain models (CulvertDesignInput, CalculationResult)
- [ ] Table repository with caching
- [ ] Calculation engine (Single, Angular, Multiple)
- [ ] DXF reader/writer with ezdxf
- [ ] Persian logger with jdatetime

### **Phase 3: Web Integration**
- [ ] Bilingual HTML template
- [ ] Flask route for culvert processing
- [ ] AJAX progress tracking
- [ ] Results page with download

### **Phase 4: Advanced Features**
- [ ] CSV input upload
- [ ] Design history
- [ ] Batch processing
- [ ] Admin panel

---

## 🎯 **Technical Architecture**

### **Data Flow:**
```
User Input (Form/CSV)
    ↓
Validation
    ↓
Load Tables (CSV)
    ↓
Calculation Engine (Strategy Pattern)
    ↓
Load DXF Template
    ↓
Replace Placeholders (i-001, i-002, etc.)
    ↓
Save Modified DXF
    ↓
User Downloads DXF → Opens in AutoCAD
```

### **Key Components:**

1. **CulvertProcessor** (Main Interface)
   - `process(input_data, template_choice) -> dxf_file`
   - Orchestrates entire workflow

2. **CalculationEngine** (Strategy Pattern)
   - `SingleOpeningCalculator` (n=1, alpha=0)
   - `AngularCalculator` (n=1, alpha!=0)
   - `MultipleOpeningCalculator` (n>1)

3. **DXFService** (Template Processing)
   - `read_template(template_path) -> doc`
   - `replace_placeholders(doc, values) -> doc`
   - `save_dxf(doc, output_path) -> file`

4. **TableRepository** (Data Access)
   - Load CSV tables at startup
   - Cache in memory
   - Provide lookup methods with interpolation

5. **Validator** (Input Validation)
   - Bilingual error messages
   - Range checks
   - Dependency validation

---

## 🌐 **Bilingual Support**

### **Translation Keys Added:**
```javascript
{
  "en": {
    "tool_culvert": "Culvert Design",
    "tool_culvert_desc": "Automated culvert design",
    // ... more keys
  },
  "fa": {
    "tool_culvert": "طراحی آبرو",
    "tool_culvert_desc": "طراحی خودکار آبرو",
    // ... more keys
  }
}
```

### **RTL/LTR Handling:**
- Automatic direction switching
- Persian font (Vazir)
- Form alignment
- Button placement

---

## 📊 **File Formats Summary**

| Format | Type | ezdxf Support | AutoCAD Compatible | Use Case |
|--------|------|---------------|-------------------|----------|
| DWG | Binary | ❌ No | ✅ Yes (native) | Source templates (convert to DXF) |
| DXF | Text | ✅ Yes | ✅ Yes (fully) | Working format & output |

---

## 🔄 **Current Status**

**Completed:**
- ✅ Bilingual website infrastructure
- ✅ Project directories created
- ✅ Tables and templates copied
- ✅ Dependencies installed and tested
- ✅ ezdxf verified (works with DXF)

**Immediate Next Steps:**
1. **Convert DWG templates to DXF** (manual task)
2. Update test to use DXF files
3. Verify ezdxf can read/modify DXF templates
4. Extract placeholder TEXT entities (i-001, i-002, etc.)
5. Add culvert-specific translations

**Blockers:**
- None (waiting for DXF template conversion)

---

## 📝 **Notes for Developer**

1. **No AutoCAD Dependency**: ezdxf is pure Python, works on any platform
2. **DXF = DWG for Users**: Users won't notice difference when opening in AutoCAD
3. **Template Placeholders**: Look for TEXT entities with pattern `i-XXX` (i-001, i-097, etc.)
4. **Persian Dates**: Use jdatetime for logging (format: 1404/08/02 | 14:30:15)
5. **Bilingual Errors**: All user-facing messages must support EN/FA
6. **Table Caching**: Load CSV tables once at app startup (performance)

---

**Last Updated**: 2025-10-24  
**Next Milestone**: Convert templates to DXF and test with ezdxf
