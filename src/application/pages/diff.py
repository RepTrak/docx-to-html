"""
Diff page for comparing CSV/Excel files.
"""

import streamlit as st
import pandas as pd
import io
import re
import datetime
import os
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from .base import BasePage


class DiffPage(BasePage):
    """Diff page for comparing CSV/Excel files."""
    
    def __init__(self):
        self.title = "📊 File Diff Comparison"
    
    def render(self):
        """Render the diff comparison page."""
        st.title(self.title)
        
        st.markdown("""
        Upload two CSV or Excel files to compare their differences.
        The tool will identify common columns and highlight changes between the files.
        """)
        
        # File upload section
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📁 Source/Original File")
            source_file = st.file_uploader(
                "Upload source file",
                type=['csv', 'xlsx', 'xls'],
                key="source_file"
            )
            
            # Sheet selector for source file
            source_sheet = None
            if source_file is not None and source_file.name.endswith(('.xlsx', '.xls')):
                try:
                    sheets = self._get_sheet_names(source_file)
                    if len(sheets) > 1:
                        source_sheet = st.selectbox(
                            "Select sheet from source file:",
                            options=sheets,
                            key="source_sheet"
                        )
                    else:
                        source_sheet = sheets[0] if sheets else None
                except Exception as e:
                    st.error(f"Error reading sheets from source file: {str(e)}")
        
        with col2:
            st.subheader("📁 File to Compare")
            compare_file = st.file_uploader(
                "Upload file to compare",
                type=['csv', 'xlsx', 'xls'],
                key="compare_file"
            )
            
            # Sheet selector for compare file
            compare_sheet = None
            if compare_file is not None and compare_file.name.endswith(('.xlsx', '.xls')):
                try:
                    sheets = self._get_sheet_names(compare_file)
                    if len(sheets) > 1:
                        compare_sheet = st.selectbox(
                            "Select sheet from compare file:",
                            options=sheets,
                            key="compare_sheet"
                        )
                    else:
                        compare_sheet = sheets[0] if sheets else None
                except Exception as e:
                    st.error(f"Error reading sheets from compare file: {str(e)}")
        
        if source_file is not None and compare_file is not None:
            try:
                # Parse uploaded files with sheet selection
                df1 = self._parse_file(source_file, source_sheet)
                df2 = self._parse_file(compare_file, compare_sheet)
                
                # Find common columns
                common_columns = list(set(df1.columns) & set(df2.columns))
                
                if common_columns:
                    st.subheader("🔗 Column Selection")
                    st.markdown(f"**Common columns found:** {len(common_columns)}")
                    
                    selected_columns = st.multiselect(
                        "Select columns to use as comparison keys:",
                        options=common_columns,
                        default=common_columns[:min(2, len(common_columns))],
                        help="These columns will be used to match rows between files"
                    )
                    
                    if selected_columns:
                        if st.button("🔍 Compare Files", type="primary"):
                            self._perform_comparison(df1, df2, selected_columns, common_columns)
                    else:
                        st.warning("Please select at least one column for comparison.")
                else:
                    st.error("No common columns found between the two files.")
                    
                    # Show column information
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Source file columns:**")
                        st.write(list(df1.columns))
                    with col2:
                        st.write("**Compare file columns:**")
                        st.write(list(df2.columns))
                        
            except Exception as e:
                st.error(f"Error processing files: {str(e)}")
    
    def _get_sheet_names(self, uploaded_file):
        """Get sheet names from Excel file."""
        file_bytes = uploaded_file.read()
        uploaded_file.seek(0)  # Reset file pointer
        
        excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
        return excel_file.sheet_names
    
    def _parse_file(self, uploaded_file, sheet_name=None):
        """Parse uploaded file to DataFrame."""
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            if sheet_name:
                df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
            else:
                df = pd.read_excel(uploaded_file)
        
        # Normalize column names
        df.columns = [self._normalize_string(col.strip()).lower() for col in df.columns]
        return df
    
    def _normalize_string(self, s):
        """Convert a string to normalized format with only lowercase letters, numbers, and underscores."""
        s = re.sub(r'[^a-zA-Z0-9]', '_', s)
        s = s.lower()
        return s
    
    def _perform_comparison(self, df1, df2, selected_columns, common_columns):
        """Perform the comparison between two DataFrames."""
        try:
            # Create copies for processing
            source_df = df1.copy()
            compare_df = df2.copy()
            
            # Set index for comparison
            source_df_commons = source_df[common_columns].copy()
            source_df_commons.set_index(selected_columns, inplace=True, drop=False)
            
            compare_df_commons = compare_df[common_columns].copy()
            compare_df_commons.set_index(selected_columns, inplace=True, drop=False)
            
            # Perform comparison
            diff_df = self._compare_dataframes(source_df_commons, compare_df_commons, common_columns)
            
            # Display results
            st.subheader("📋 Comparison Results")
            
            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            
            added_count = len(diff_df[diff_df['diff'] == 'ADDED'])
            removed_count = len(diff_df[diff_df['diff'] == 'REMOVED'])
            modified_count = len(diff_df[~diff_df['diff'].isin(['ADDED', 'REMOVED', None])])
            total_rows = len(diff_df)
            
            col1.metric("Total Rows", total_rows)
            col2.metric("Added", added_count)
            col3.metric("Removed", removed_count)
            col4.metric("Modified", modified_count)
            
            # Display diff table
            if not diff_df.empty:
                st.subheader("📊 Detailed Differences")
                
                # Filter options
                filter_option = st.selectbox(
                    "Filter results:",
                    ["All Changes", "Added Only", "Removed Only", "Modified Only"]
                )
                
                filtered_df = diff_df.copy()
                if filter_option == "Added Only":
                    filtered_df = diff_df[diff_df['diff'] == 'ADDED']
                elif filter_option == "Removed Only":
                    filtered_df = diff_df[diff_df['diff'] == 'REMOVED']
                elif filter_option == "Modified Only":
                    filtered_df = diff_df[~diff_df['diff'].isin(['ADDED', 'REMOVED', None])]
                
                # Apply styling and display the filtered dataframe
                styled_df = self._style_diff_dataframe(filtered_df)
                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    height=400
                )
                
                # Download section - generate Excel data once and provide direct download
                st.subheader("💾 Download Results")
                
                # Generate Excel file data
                try:
                    excel_data = self._create_styled_excel(diff_df)
                    if excel_data:
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
                        filename = f"diff_results_{timestamp}.xlsx"
                        
                        st.download_button(
                            label="📥 Download Styled Excel File",
                            data=excel_data,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_excel"
                        )
                        
                        st.info("💡 Click the button above to download the comparison results as a styled Excel file.")
                    else:
                        st.error("Failed to generate Excel file. Please try again.")
                        
                except Exception as e:
                    st.error(f"Error preparing Excel download: {str(e)}")
                    
                    # Fallback: Offer CSV download
                    csv_data = diff_df.to_csv(index=True)
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
                    csv_filename = f"diff_results_{timestamp}.csv"
                    
                    st.download_button(
                        label="📄 Download as CSV (Fallback)",
                        data=csv_data,
                        file_name=csv_filename,
                        mime="text/csv",
                        key="download_csv"
                    )
            else:
                st.info("No differences found between the files.")
                
        except Exception as e:
            st.error(f"Error during comparison: {str(e)}")
    
    def _create_styled_excel(self, df):
        """Create a styled Excel file with conditional formatting."""
        try:
            # Create workbook and worksheet
            wb = Workbook()
            ws = wb.active
            ws.title = "Diff Results"
            
            # Prepare DataFrame for Excel export by handling MultiIndex
            export_df = df.copy()
            
            # Convert MultiIndex tuples to strings if present
            if hasattr(export_df.index, 'nlevels') and export_df.index.nlevels > 1:
                # Convert MultiIndex tuples to readable strings
                export_df.index = export_df.index.map(lambda x: ' | '.join(str(val) for val in x) if isinstance(x, tuple) else str(x))
            else:
                # Convert single index values that might be tuples
                export_df.index = export_df.index.map(lambda x: ' | '.join(str(val) for val in x) if isinstance(x, tuple) else str(x))
            
            # Ensure all column values are Excel-compatible
            for col in export_df.columns:
                export_df[col] = export_df[col].apply(lambda x: self._convert_to_excel_compatible(x))
            
            # Add data to worksheet
            for r in dataframe_to_rows(export_df, index=True, header=True):
                # Convert any remaining tuples in the row data
                converted_row = []
                for cell_value in r:
                    converted_row.append(self._convert_to_excel_compatible(cell_value))
                ws.append(converted_row)
            
            # Define styles
            header_fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
            header_font = Font(bold=True, color="495057")
            
            added_fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
            added_font = Font(bold=True, color="155724")
            
            removed_fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
            removed_font = Font(bold=True, color="721C24")
            
            modified_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
            modified_font = Font(bold=True, color="856404")
            
            diff_added_fill = PatternFill(start_color="28A745", end_color="28A745", fill_type="solid")
            diff_added_font = Font(bold=True, color="FFFFFF")
            
            diff_removed_fill = PatternFill(start_color="DC3545", end_color="DC3545", fill_type="solid")
            diff_removed_font = Font(bold=True, color="FFFFFF")
            
            diff_modified_fill = PatternFill(start_color="FFC107", end_color="FFC107", fill_type="solid")
            diff_modified_font = Font(bold=True, color="212529")
            
            # Border style
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            # Style header row
            for cell in ws[2]:  # Row 2 contains the headers (row 1 is index header)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.border = thin_border
            
            # Find diff column index
            diff_col_idx = None
            for idx, cell in enumerate(ws[2], 1):
                if cell.value == 'diff':
                    diff_col_idx = idx
                    break
            
            # Style data rows
            for row_idx, row in enumerate(ws.iter_rows(min_row=3), 3):  # Start from row 3 (data rows)
                if diff_col_idx and len(row) >= diff_col_idx:
                    diff_cell = row[diff_col_idx - 1]  # Adjust for 0-based indexing
                    diff_value = str(diff_cell.value) if diff_cell.value is not None else ''
                    
                    # Apply row styling based on diff value
                    for cell in row:
                        cell.border = thin_border
                        cell.alignment = Alignment(vertical='top', wrap_text=True)
                        
                        if diff_value == 'ADDED':
                            cell.fill = added_fill
                            cell.font = added_font
                        elif diff_value == 'REMOVED':
                            cell.fill = removed_fill
                            cell.font = removed_font
                        elif diff_value and diff_value not in ['ADDED', 'REMOVED', 'None', '']:
                            cell.fill = modified_fill
                            cell.font = modified_font
                    
                    # Special styling for diff column
                    if diff_value == 'ADDED':
                        diff_cell.fill = diff_added_fill
                        diff_cell.font = diff_added_font
                        diff_cell.value = '✅ ADDED'
                        diff_cell.alignment = Alignment(horizontal='center', vertical='center')
                    elif diff_value == 'REMOVED':
                        diff_cell.fill = diff_removed_fill
                        diff_cell.font = diff_removed_font
                        diff_cell.value = '❌ REMOVED'
                        diff_cell.alignment = Alignment(horizontal='center', vertical='center')
                    elif diff_value and diff_value not in ['ADDED', 'REMOVED', 'None', '']:
                        diff_cell.fill = diff_modified_fill
                        diff_cell.font = diff_modified_font
                        # Format changes for Excel
                        formatted_diff = self._format_diff_for_excel(diff_value)
                        diff_cell.value = formatted_diff
                        diff_cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        cell_value = str(cell.value) if cell.value is not None else ''
                        if len(cell_value) > max_length:
                            max_length = len(cell_value)
                    except:
                        pass
                
                # Set column width (with some padding)
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Set row heights for better readability
            for row in ws.iter_rows(min_row=3):
                ws.row_dimensions[row[0].row].height = 30
            
            # Save to BytesIO buffer
            excel_buffer = io.BytesIO()
            wb.save(excel_buffer)
            excel_buffer.seek(0)
            
            return excel_buffer.getvalue()
            
        except Exception as e:
            st.error(f"Error creating Excel file: {str(e)}")
            return None
    
    def _convert_to_excel_compatible(self, value):
        """Convert any value to Excel-compatible format."""
        if value is None:
            return ''
        elif isinstance(value, tuple):
            # Convert tuple to string with separator
            return ' | '.join(str(v) for v in value)
        elif isinstance(value, (list, set)):
            # Convert list/set to string
            return ', '.join(str(v) for v in value)
        elif hasattr(value, 'strftime'):
            # Handle datetime objects
            return value.strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Convert everything else to string
            return str(value)
    
    def _format_diff_for_excel(self, diff_value):
        """Format diff content specifically for Excel cells."""
        if not diff_value or diff_value in ['ADDED', 'REMOVED', None]:
            return diff_value
        
        # Format multi-line changes for Excel
        changes = diff_value.split('\n')
        formatted_changes = []
        
        for change in changes:
            if '=>' in change:
                parts = change.split('=>')
                if len(parts) == 2:
                    col_name = parts[0].split(':')[0].strip()
                    old_val = parts[0].split(':')[1].strip() if ':' in parts[0] else ''
                    new_val = parts[1].strip()
                    formatted_changes.append(f"🔄 {col_name}:\n  {old_val} → {new_val}")
                else:
                    formatted_changes.append(f"🔄 {change}")
            else:
                formatted_changes.append(f"🔄 {change}")
        
        return '\n'.join(formatted_changes)
    
    def _style_diff_dataframe(self, df):
        """Apply conditional styling to the diff dataframe based on diff state."""
        def style_row(row):
            """Style entire row based on diff status."""
            diff_value = row['diff']
            
            if diff_value == 'ADDED':
                return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row)
            elif diff_value == 'REMOVED':
                return ['background-color: #f8d7da; color: #721c24; font-weight: bold'] * len(row)
            elif diff_value and diff_value not in ['ADDED', 'REMOVED', None]:
                return ['background-color: #fff3cd; color: #856404; font-weight: bold'] * len(row)
            else:
                return [''] * len(row)
        
        def style_diff_column(series):
            """Style the diff column specifically."""
            styles = []
            for val in series:
                if val == 'ADDED':
                    styles.append('background-color: #28a745; color: white; font-weight: bold; text-align: center')
                elif val == 'REMOVED':
                    styles.append('background-color: #dc3545; color: white; font-weight: bold; text-align: center')
                elif val and val not in ['ADDED', 'REMOVED', None]:
                    styles.append('background-color: #ffc107; color: #212529; font-weight: bold; text-align: left; white-space: pre-wrap')
                else:
                    styles.append('text-align: center')
            return styles
        
        # Apply styling
        styled = df.style.apply(style_row, axis=1)
        styled = styled.apply(style_diff_column, subset=['diff'])
        
        # Set table-wide styles
        styled = styled.set_table_styles([
            {'selector': 'th', 'props': [
                ('background-color', '#f8f9fa'),
                ('color', '#495057'),
                ('font-weight', 'bold'),
                ('text-align', 'center'),
                ('border', '1px solid #dee2e6')
            ]},
            {'selector': 'td', 'props': [
                ('border', '1px solid #dee2e6'),
                ('padding', '8px'),
                ('vertical-align', 'top')
            ]},
            {'selector': 'table', 'props': [
                ('border-collapse', 'collapse'),
                ('width', '100%')
            ]}
        ])
        
        # Format the diff column to be more readable
        styled = styled.format({'diff': lambda x: self._format_diff_cell(x)})
        
        return styled
    
    def _format_diff_cell(self, diff_value):
        """Format the diff cell content for better readability."""
        if diff_value == 'ADDED':
            return '✅ ADDED'
        elif diff_value == 'REMOVED':
            return '❌ REMOVED'
        elif diff_value and diff_value not in ['ADDED', 'REMOVED', None]:
            # Format multi-line changes
            changes = diff_value.split('\n')
            formatted_changes = []
            for change in changes:
                if '=>' in change:
                    parts = change.split('=>')
                    if len(parts) == 2:
                        col_name = parts[0].split(':')[0].strip()
                        old_val = parts[0].split(':')[1].strip() if ':' in parts[0] else ''
                        new_val = parts[1].strip()
                        formatted_changes.append(f"🔄 {col_name}:\n  {old_val} → {new_val}")
                    else:
                        formatted_changes.append(f"🔄 {change}")
                else:
                    formatted_changes.append(f"🔄 {change}")
            return '\n'.join(formatted_changes)
        else:
            return ''
    
    def _compare_dataframes(self, df1: pd.DataFrame, df2: pd.DataFrame, common_columns) -> pd.DataFrame:
        """Compare two DataFrames and return differences."""
        # Merge both dataframes on their indexes, filling missing values with empty strings
        merged = pd.merge(
            df1, df2, 
            how='outer', 
            left_index=True, 
            right_index=True, 
            suffixes=('_source', '_compare')
        ).fillna('')
        
        # Initialize comparison dataframe with proper structure
        comparison_columns = ['diff'] + list(merged.columns)
        comparison_df = pd.DataFrame(columns=comparison_columns)
        
        for i, row in merged.iterrows():
            # Initialize the diff column
            if i not in df1.index:
                row_diff = 'ADDED'
            elif i not in df2.index:
                row_diff = 'REMOVED'
            else:
                row_diff = None
            
            # Compare values in common columns
            cell_diffs = []
            for column in common_columns:
                val1 = row.get(f'{column}_source', '')
                val2 = row.get(f'{column}_compare', '')
                if val1 != val2:
                    cell_diffs.append(f'{column}: {val1} => {val2}')
            
            if row_diff is None and len(cell_diffs) > 0:
                row_diff = '\n'.join(cell_diffs)
            
            # Create a new row with diff column + all merged columns
            new_row = pd.Series([row_diff] + list(row.values), index=comparison_columns, name=i)
            comparison_df = pd.concat([comparison_df, new_row.to_frame().T], ignore_index=False)
        
        return comparison_df
