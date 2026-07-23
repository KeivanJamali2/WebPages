"""
Culvert Processor - Handles web-based culvert design calculations
"""
import os
from typing import Dict, Any
from culvert.calculators.base import CulvertInput
from culvert.calculators.factory import CulvertCalculatorFactory
from culvert.services.dxf_service import DXFService
from culvert.repositories.table_repository import TableRepository


class CulvertProcessor:
    """Process culvert design requests from web interface"""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize the processor
        
        Args:
            base_dir: Base directory of the application (defaults to parent of this file)
        """
        if base_dir is None:
            # Get base directory (Project-07-AutomationWebsite)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(os.path.dirname(current_dir))
        
        # All culvert-specific paths are now in the culvert folder
        culvert_dir = os.path.join(base_dir, 'culvert')
        template_dir = os.path.join(culvert_dir, 'templates_dxf')
        output_dir = os.path.join(culvert_dir, 'results')
        table_dir = os.path.join(culvert_dir, 'data')
        
        self.dxf_service = DXFService(template_dir, output_dir)
        self.table_repository = TableRepository(table_dir)
    
    def process(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process culvert design request
        
        Args:
            form_data: Dictionary with form input parameters
            
        Returns:
            Dictionary with processing results including:
            - status: 'success', 'warning', or 'error'
            - message: Status message
            - calculated_height: The calculated H value
            - filename: Generated DXF filename
            - filepath: Full path to generated file
            - warnings: List of warning messages (when present)
            - error_details: Additional error information (when status is 'error')
            
        Note:
            DXF files are always generated for debugging purposes.
            Missing/failed values will be empty or marked as ERR in the output.
        """
        try:
            # Extract and validate form data
            culvert_input = self._create_input_from_form(form_data)
            
            # Get appropriate calculator
            calculator = CulvertCalculatorFactory.create_calculator(
                input_params=culvert_input,
                table_repository=self.table_repository
            )
            
            # Run calculation (now continues even with errors)
            results = calculator.calculate()
            
            # Get any warning/error messages from calculator
            messages = calculator.get_messages()
            
            # Check if there were errors during calculation
            has_errors = results.get('_has_errors') == 'true'
            
            # Get template filename
            template_filename = calculator.get_template_filename()
            
            # Derive culvert type from n and alpha for output filename
            n = culvert_input.n
            alpha = culvert_input.alpha
            if n == 1:
                if alpha == 0:
                    culvert_type = 'single_perpendicular'
                elif alpha < 0:
                    culvert_type = 'single_angular_less'
                else:
                    culvert_type = 'single_angular_more'
            elif n == 2:
                if alpha == 0:
                    culvert_type = "double_perpendicular"
                elif alpha < 0:
                    culvert_type = "double_angular_less"
                else:                    
                    culvert_type = "double_angular_more"
            elif n == 3:
                if alpha == 0:
                    culvert_type = "triple_perpendicular"
                elif alpha < 0:
                    culvert_type = "triple_angular_less"
                else:                    
                    culvert_type = "triple_angular_more"
            elif n == 4:
                if alpha == 0:
                    culvert_type = "four_perpendicular"
                elif alpha < 0:
                    culvert_type = "four_angular_less"
                else:                    
                    culvert_type = "four_angular_more"
            elif n == 5:
                if alpha == 0:
                    culvert_type = "five_perpendicular"
                elif alpha < 0:
                    culvert_type = "five_angular_less"
                else:                    
                    culvert_type = "five_angular_more"
            elif n == 6:
                if alpha == 0:
                    culvert_type = "six_perpendicular"
                elif alpha < 0:
                    culvert_type = "six_angular_less"
                else:                    
                    culvert_type = "six_angular_more"
            
            error_suffix = "_DEBUG" if has_errors else ""
            output_filename = f"culvert_{culvert_type}_n{culvert_input.n}_D{culvert_input.D}{error_suffix}.dxf"
            
            # Always generate DXF file (even with errors for debugging)
            output_path = self.dxf_service.generate_dxf(
                template_filename=template_filename,
                data=results,
                output_filename=output_filename
            )
            
            # Determine response status
            if has_errors:
                response = {
                    'status': 'warning',
                    'message': 'DXF generated with errors - some values may be missing or incorrect',
                    'calculated_height': results.get('HA', results.get('c04', 'N/A')),
                    'filename': output_filename,
                    'filepath': output_path,
                    'warnings': messages if messages else ['Some calculations failed - check DXF for details'],
                    'has_calculation_errors': True
                }
            else:
                response = {
                    'status': 'success',
                    'message': 'Culvert design generated successfully',
                    'calculated_height': results.get('HA', results.get('c04', 'N/A')),
                    'filename': output_filename,
                    'filepath': output_path
                }
                
                # Add warnings if any (non-critical)
                if messages:
                    response['warnings'] = messages
            
            return response
            
        except ValueError as e:
            error_msg = str(e)
            error_details = self._parse_error_details(error_msg, form_data)
            return {
                'status': 'error',
                'message': f'Input validation error: {error_msg}',
                'error_type': 'validation',
                'error_details': error_details
            }
        except Exception as e:
            error_msg = str(e)
            error_details = self._parse_error_details(error_msg, form_data)
            return {
                'status': 'error',
                'message': f'Processing error: {error_msg}',
                'error_type': 'processing',
                'error_details': error_details
            }
    
    def _parse_error_details(self, error_msg: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse error message and provide helpful details.
        
        Args:
            error_msg: The error message string
            form_data: Original form data for context
            
        Returns:
            Dictionary with error details and suggestions
        """
        details = {
            'suggestions': [],
            'affected_fields': [],
            'formulas': []
        }
        
        # Parse H out of range errors
        if 'H=' in error_msg and 'out of range' in error_msg:
            details['affected_fields'] = ['H_min', 'CL', 'ax_natural', 'Hs', 'ret']
            details['suggestions'] = [
                'The calculated wall height (H) must be between 1m and 7m',
                'Try adjusting: CL (center line), ax_natural, Hs (static head), or ret (retention)',
                'Increase H: Raise CL, Lower ax_natural, Reduce Hs, Increase ret',
                'Decrease H: Lower CL, Raise ax_natural, Increase Hs, Reduce ret'
            ]
            details['formulas'] = [
                'H_max_left = c04 + 0.3 + t - c06',
                'H_max_right = c14 + 0.3 + t - c04',
                'c04 = CL + (dever_left/100) × A - Hs - t - 0.3',
                'c06 = ax_natural ± z_natural × A - ret'
            ]
        
        # Parse table lookup errors
        elif 'No data found' in error_msg or 'No suitable' in error_msg:
            if 'table1' in error_msg:
                details['affected_fields'] = ['n', 'D', 'Hs']
                details['suggestions'] = [
                    'The combination of n, D, and Hs is not in the design tables',
                    'Valid D values: 0.6, 0.8, 1.0, 1.2, 1.5, 2.0 meters',
                    'Check if your Hs value falls within the available ranges'
                ]
            elif 'table2' in error_msg:
                details['affected_fields'] = ['D', 'Hs']
                details['suggestions'] = [
                    'Rebar specifications not found for this configuration',
                    'Try a different diameter or static head value'
                ]
            elif 'table3' in error_msg:
                details['affected_fields'] = ['H_min', 'CL', 'ax_natural']
                details['suggestions'] = [
                    'Wall height parameters are outside valid range (1m to 7m)',
                    'Adjust elevation parameters to bring H values into range'
                ]
        
        return details
    
    def _create_input_from_form(self, form_data: Dict[str, Any]) -> CulvertInput:
        """
        Convert form data to CulvertInput object
        
        Args:
            form_data: Dictionary with form fields
            
        Returns:
            CulvertInput object
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            # Parse direction flag
            direction_flag_str = form_data.get('direction_flag', 'true')
            direction_flag = direction_flag_str.lower() == 'true'
            
            # Handle L_left and L_right - calculate total L
            L_left = float(form_data.get('L_left', 5.0))
            L_right = float(form_data.get('L_right', 5.0))
            L = float(form_data.get('L', L_left + L_right))
            
            # A and B are now derived from L_left and L_right
            A = L_left
            B = L_right
            
            # Create input object
            return CulvertInput(
                n=int(form_data['n']),
                D=float(form_data['D']),
                L=L,
                Hs=float(form_data['Hs']),
                H_min=float(form_data['H_min']),
                CL=float(form_data['CL']),
                ax_natural=float(form_data['ax_natural']),
                dever_right=float(form_data['dever_right']),
                dever_left=float(form_data['dever_left']),
                z_natural=float(form_data['z_natural']) / 100,  # Convert from % to ratio
                z_toli=float(form_data['z_toli']) / 100,  # Convert from % to ratio
                z_shirvani=float(form_data['z_shirvani']),
                u_shirvani=float(form_data['u_shirvani']),
                ret=float(form_data['ret']),
                ball_degree=float(form_data['ball_degree']),
                A=A,
                B=B,
                direction_flag=direction_flag,
                alpha=float(form_data.get('alpha', 0.0)),
                employer=form_data.get('employer', ''),
                project_title=form_data.get('project_title', ''),
                project_type=form_data.get('project_type', ''),
                date=form_data.get('project_date', ''),
                map_code=form_data.get('map_code', ''),
                page_number=form_data.get('page_number', ''),
                location=form_data.get('location', ''),
                city_top=form_data.get('city_top', ''),
                city_bottom=form_data.get('city_bottom', ''),
                h_min_dastak_l=float(form_data['h_min_dastak_r']),
                h_min_dastak_r=float(form_data['h_min_dastak_l']),
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid field value: {e}")
