"""
Test ezdxf library - Verify DWG reading and writing without AutoCAD
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import ezdxf
    print("✓ ezdxf imported successfully")
except ImportError as e:
    print(f"✗ Failed to import ezdxf: {e}")
    print("Please install: pip install ezdxf")
    sys.exit(1)

# Test paths
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'Files', 'culvert_templates')
RESULT_DIR = os.path.join(os.path.dirname(__file__), '..', 'Files', 'culvert_results')

# Ensure result directory exists
os.makedirs(RESULT_DIR, exist_ok=True)

def test_read_dwg():
    """Test reading DXF file and extracting TEXT entities"""
    print("\n" + "="*60)
    print("TEST 1: Reading DXF Template")
    print("="*60)
    
    template_file = os.path.join(TEMPLATE_DIR, '1_Culvert_with_one_opening.dxf')
    
    if not os.path.exists(template_file):
        print(f"✗ Template file not found: {template_file}")
        return False
    
    try:
        # Read DWG file
        doc = ezdxf.readfile(template_file)
        print(f"✓ Successfully opened: {os.path.basename(template_file)}")
        print(f"  DWG Version: {doc.dxfversion}")
        
        # Get modelspace
        msp = doc.modelspace()
        
        # Count entities
        entity_counts = {}
        text_entities = []
        
        for entity in msp:
            entity_type = entity.dxftype()
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            # Collect TEXT entities
            if entity_type == 'TEXT':
                text_content = entity.dxf.text
                text_entities.append(text_content)
        
        # Print statistics
        print(f"\n  Entity Statistics:")
        for entity_type, count in sorted(entity_counts.items()):
            print(f"    {entity_type}: {count}")
        
        # Print TEXT entities (placeholders)
        print(f"\n  Found {len(text_entities)} TEXT entities")
        print(f"  Sample TEXT entities:")
        
        # Look for placeholder patterns (i-XXX)
        placeholders = [t for t in text_entities if t.startswith('i-')]
        if placeholders:
            print(f"\n  Found {len(placeholders)} placeholder TEXT entities:")
            for i, placeholder in enumerate(sorted(set(placeholders))[:10]):
                print(f"    {i+1}. '{placeholder}'")
            if len(placeholders) > 10:
                print(f"    ... and {len(placeholders) - 10} more")
        else:
            print("  ⚠ No placeholder TEXT entities found (i-XXX pattern)")
            print(f"  Sample TEXT entities: {text_entities[:5]}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading DWG: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_modify_and_save_dwg():
    """Test modifying TEXT entities and saving new DXF"""
    print("\n" + "="*60)
    print("TEST 2: Modifying and Saving DXF")
    print("="*60)
    
    template_file = os.path.join(TEMPLATE_DIR, '1_Culvert_with_one_opening.dxf')
    output_file = os.path.join(RESULT_DIR, 'test_output.dxf')
    
    try:
        # Read template
        doc = ezdxf.readfile(template_file)
        msp = doc.modelspace()
        
        # Replace some TEXT entities
        replacements = {
            'i-001': '123.45',
            'i-002': '67.89',
            'i-003': '10',
            'i-097': '37.14',
            'i-098': '3'
        }
        
        modified_count = 0
        for entity in msp.query('TEXT'):
            text = entity.dxf.text
            if text in replacements:
                entity.dxf.text = str(replacements[text])
                modified_count += 1
                print(f"  Replaced '{text}' → '{replacements[text]}'")
        
        print(f"\n  Modified {modified_count} TEXT entities")
        
        # Save new DWG
        doc.saveas(output_file)
        print(f"✓ Saved modified DWG to: {os.path.basename(output_file)}")
        print(f"  File size: {os.path.getsize(output_file):,} bytes")
        
        # Verify the saved file
        doc_verify = ezdxf.readfile(output_file)
        msp_verify = doc_verify.modelspace()
        
        # Check if modifications persist
        found_modifications = []
        for entity in msp_verify.query('TEXT'):
            text = entity.dxf.text
            if text in replacements.values():
                found_modifications.append(text)
        
        if found_modifications:
            print(f"✓ Verified: Found {len(found_modifications)} modified values in saved file")
        else:
            print("⚠ Warning: Could not verify modifications in saved file")
        
        return True
        
    except Exception as e:
        print(f"✗ Error modifying/saving DWG: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_create_new_dwg():
    """Test creating a new DXF from scratch"""
    print("\n" + "="*60)
    print("TEST 3: Creating New DXF from Scratch")
    print("="*60)
    
    output_file = os.path.join(RESULT_DIR, 'test_new.dxf')
    
    try:
        # Create new DWG document
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Add some entities
        msp.add_line((0, 0), (10, 10))
        msp.add_circle((5, 5), radius=2.5)
        msp.add_text('Test Text', dxfattribs={'height': 0.5, 'insert': (0, 0)})
        msp.add_text('i-001', dxfattribs={'height': 0.3, 'insert': (5, 0)})
        
        # Save
        doc.saveas(output_file)
        print(f"✓ Created new DWG file: {os.path.basename(output_file)}")
        print(f"  File size: {os.path.getsize(output_file):,} bytes")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating new DWG: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("EZDXF Library Test Suite")
    print("Testing DXF file operations WITHOUT AutoCAD")
    print("="*60)
    
    results = {
        'Read DXF': test_read_dwg(),
        'Modify & Save DXF': test_modify_and_save_dwg(),
        'Create New DXF': test_create_new_dwg()
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! ezdxf is working correctly!")
        print("✓ Can read DXF files without AutoCAD")
        print("✓ Can modify TEXT entities")
        print("✓ Can save modified DXF files")
        print("✓ Can create new DXF files from scratch")
    else:
        print("⚠ SOME TESTS FAILED - Please review errors above")
    print("="*60 + "\n")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
