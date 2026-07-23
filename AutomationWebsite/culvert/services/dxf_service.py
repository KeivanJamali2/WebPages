"""
DXF Service for loading templates and generating final DXF files.
Wraps ezdxf library to handle TEXT entity replacement.
"""

import os
from typing import Dict, Any
import ezdxf
from ezdxf.document import Drawing


class DXFService:
    """
    Service for DXF file operations.
    Handles loading templates, replacing placeholders, and saving results.
    """
    
    def __init__(self, template_dir: str, output_dir: str):
        """
        Initialize DXF service.
        
        Args:
            template_dir: Directory containing DXF templates
            output_dir: Directory for output DXF files
        """
        self.template_dir = template_dir
        self.output_dir = output_dir
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def load_template(self, template_filename: str) -> Drawing:
        """
        Load a DXF template file.
        
        Args:
            template_filename: Name of template file (e.g., '1_Culvert_with_one_opening.dxf')
            
        Returns:
            ezdxf Drawing object
            
        Raises:
            FileNotFoundError: If template doesn't exist
            ezdxf.DXFError: If file is invalid
        """
        template_path = os.path.join(self.template_dir, template_filename)
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        print(f"[INFO] Loading template: {template_filename}")
        doc = ezdxf.readfile(template_path)
        print(f"[INFO] Template loaded successfully (DWG version: {doc.dxfversion})")
        
        return doc
    
    def replace_placeholders(self, doc: Drawing, data: Dict[str, Any]) -> int:
        """
        Replace placeholder TEXT entities with calculated values.
        
        Searches for TEXT entities matching placeholder pattern (i-XXX)
        and replaces them with values from data dictionary.
        Handles special formats like:
        - "A=i-A" → "A=8.0"
        - "i-096 %" → "0 %"
        
        Args:
            doc: ezdxf Drawing object
            data: Dictionary with placeholder keys and values
            
        Returns:
            Number of placeholders replaced
        """
        msp = doc.modelspace()
        replaced_count = 0
        
        # Iterate through all TEXT entities
        for entity in msp.query('TEXT'):
            text_content = entity.dxf.text.strip()
            original_text = text_content
            replaced = False
            
            # Direct match (most common case)
            if text_content in data:
                entity.dxf.text = str(data[text_content])
                replaced = True
            
            # Handle patterns like "A=i-A", "B=i-B", "L=i-L", "Hs=i-Hs"
            elif '=' in text_content and 'i-' in text_content:
                parts = text_content.split('=')
                if len(parts) == 2:
                    prefix = parts[0]
                    placeholder = parts[1].strip()
                    if placeholder in data:
                        entity.dxf.text = f"{prefix}={data[placeholder]}"
                        replaced = True
            
            # Handle patterns like "i-096 %", "i-098 %", "i-099 %"
            elif text_content.endswith(' %') and 'i-' in text_content:
                placeholder = text_content[:-2].strip()  # Remove " %"
                if placeholder in data:
                    entity.dxf.text = f"{data[placeholder]} %"
                    replaced = True
            
            if replaced:
                replaced_count += 1
                if replaced_count <= 10:  # Show first 10 replacements
                    print(f"  Replaced '{original_text}' → '{entity.dxf.text}'")
        
        if replaced_count > 10:
            print(f"  ... and {replaced_count - 10} more replacements")
        
        print(f"[INFO] Replaced {replaced_count} placeholders")
        return replaced_count
    
    def save_result(self, doc: Drawing, output_filename: str) -> str:
        """
        Save the modified DXF file.
        
        Args:
            doc: ezdxf Drawing object
            output_filename: Name for output file
            
        Returns:
            Full path to saved file
        """
        output_path = os.path.join(self.output_dir, output_filename)
        
        print(f"[INFO] Saving DXF to: {output_filename}")
        doc.saveas(output_path)
        
        file_size = os.path.getsize(output_path)
        print(f"[INFO] File saved successfully ({file_size:,} bytes)")
        
        return output_path
    
    def generate_dxf(self, 
                     template_filename: str,
                     data: Dict[str, Any],
                     output_filename: str) -> str:
        """
        Complete workflow: load template, replace placeholders, save result.
        
        Args:
            template_filename: Name of DXF template
            data: Dictionary with placeholder values
            output_filename: Name for output file
            
        Returns:
            Full path to generated DXF file
            
        Raises:
            FileNotFoundError: If template doesn't exist
            ezdxf.DXFError: If DXF operation fails
        """
        print("\n" + "="*60)
        print("DXF GENERATION")
        print("="*60)
        
        # Load template
        doc = self.load_template(template_filename)
        
        # Replace placeholders
        print(f"\nReplacing placeholders...")
        replaced_count = self.replace_placeholders(doc, data)
        
        if replaced_count == 0:
            print("[WARNING] No placeholders were replaced!")
        
        # Save result
        print(f"\nSaving result...")
        output_path = self.save_result(doc, output_filename)
        
        print("="*60)
        print(f"✓ DXF generation complete: {output_filename}")
        print("="*60 + "\n")
        
        return output_path
