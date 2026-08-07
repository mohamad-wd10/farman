"""
Data Cleaning Engine
Automatically cleans, normalizes, and standardizes Excel data
"""

import re
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import jdatetime


class DataCleaningEngine:
    """
    Intelligent data cleaning engine for Excel files.
    Handles Persian and English data with various formats.
    """
    
    def __init__(self):
        self.cleaning_log = []
    
    def clean_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Main cleaning pipeline for a DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (cleaned DataFrame, list of cleaning actions performed)
        """
        self.cleaning_log = []
        
        # Step 1: Remove completely empty rows/columns
        df = self._remove_empty_rows_columns(df)
        
        # Step 2: Clean column names
        df = self._clean_column_names(df)
        
        # Step 3: Remove duplicates
        df = self._remove_duplicates(df)
        
        # Step 4: Standardize dates (Persian/English)
        df = self._standardize_dates(df)
        
        # Step 5: Standardize numbers (Persian/English digits, commas)
        df = self._standardize_numbers(df)
        
        # Step 6: Fix common typos in Persian text
        df = self._fix_persian_typos(df)
        
        # Step 7: Detect and handle outliers
        df = self._detect_outliers(df)
        
        # Step 8: Fill missing values intelligently
        df = self._handle_missing_values(df)
        
        return df, self.cleaning_log
    
    def _remove_empty_rows_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows and columns that are completely empty"""
        initial_shape = df.shape
        
        # Remove empty columns
        df = df.dropna(axis=1, how='all')
        
        # Remove empty rows
        df = df.dropna(axis=0, how='all')
        
        if df.shape != initial_shape:
            self.cleaning_log.append({
                'action': 'remove_empty',
                'details': f'Removed {initial_shape[0] - df.shape[0]} empty rows and {initial_shape[1] - df.shape[1]} empty columns'
            })
        
        return df
    
    def _clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names"""
        new_columns = {}
        
        for col in df.columns:
            if pd.isna(col) or str(col).strip() == '':
                continue
            
            # Convert to string and strip whitespace
            clean_col = str(col).strip()
            
            # Remove special characters but keep Persian/English letters and numbers
            clean_col = re.sub(r'[^\w\s\u0600-\u06FF]', '', clean_col)
            
            # Replace multiple spaces with single space
            clean_col = re.sub(r'\s+', ' ', clean_col)
            
            # Convert to lowercase for English
            if clean_col.isascii():
                clean_col = clean_col.lower()
            
            new_columns[col] = clean_col
        
        df = df.rename(columns=new_columns)
        
        # Remove columns with empty names after cleaning
        df = df.loc[:, df.columns != '']
        
        self.cleaning_log.append({
            'action': 'clean_columns',
            'details': f'Cleaned {len(new_columns)} column names'
        })
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows"""
        initial_count = len(df)
        df = df.drop_duplicates()
        removed_count = initial_count - len(df)
        
        if removed_count > 0:
            self.cleaning_log.append({
                'action': 'remove_duplicates',
                'details': f'Removed {removed_count} duplicate rows'
            })
        
        return df
    
    def _standardize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert Persian and English dates to standard format"""
        date_patterns = [
            r'\d{4}/\d{1,2}/\d{1,2}',  # 1402/01/15 or 2023/01/15
            r'\d{4}-\d{1,2}-\d{1,2}',  # 1402-01-15 or 2023-01-15
            r'\d{2}/\d{2}/\d{4}',      # 01/15/1402 or 01/15/2023
        ]
        
        persian_months = {
            'فروردین': 1, 'اردیبهشت': 2, 'خرداد': 3, 'تیر': 4,
            'مرداد': 5, 'شهریور': 6, 'مهر': 7, 'آبان': 8,
            'آذر': 9, 'دی': 10, 'بهمن': 11, 'اسفند': 12
        }
        
        for col in df.columns:
            if not isinstance(col, str):
                continue
                
            # Check if column name suggests it's a date column
            date_keywords = ['تاریخ', 'date', 'زمان', 'time', 'روز', 'day']
            is_date_column = any(keyword in col.lower() for keyword in date_keywords)
            
            if not is_date_column:
                # Try to detect date pattern in values
                sample_value = str(df[col].iloc[0]) if len(df) > 0 else ''
                is_date_column = any(re.search(pattern, sample_value) for pattern in date_patterns)
            
            if is_date_column:
                def convert_date(val):
                    if pd.isna(val):
                        return val
                    
                    val_str = str(val).strip()
                    
                    # Handle Persian text months (e.g., "15 فروردین 1402")
                    for month_name, month_num in persian_months.items():
                        if month_name in val_str:
                            # Extract year and day
                            year_match = re.search(r'(\d{4})', val_str)
                            day_match = re.search(r'(\d{1,2})', val_str)
                            if year_match and day_match:
                                year = year_match.group(1)
                                day = day_match.group(1)
                                return f"{year}/{month_num:02d}/{int(day):02d}"
                    
                    # Handle numeric dates
                    for pattern in date_patterns:
                        match = re.search(pattern, val_str)
                        if match:
                            date_str = match.group(0)
                            # Normalize separators
                            date_str = re.sub(r'[-/]', '/', date_str)
                            parts = date_str.split('/')
                            
                            if len(parts) == 3:
                                # Try to determine format
                                if int(parts[0]) > 1300:  # Likely Persian YYYY/MM/DD
                                    return f"{parts[0]}/{int(parts[1]):02d}/{int(parts[2]):02d}"
                                elif int(parts[2]) > 1300:  # Likely DD/MM/YYYY Persian
                                    return f"{parts[2]}/{int(parts[1]):02d}/{int(parts[0]):02d}"
                                elif int(parts[0]) > 2000:  # Likely English YYYY/MM/DD
                                    return f"{parts[0]}/{int(parts[1]):02d}/{int(parts[2]):02d}"
                            
                            return date_str
                    
                    return val_str
                
                df[col] = df[col].apply(convert_date)
        
        self.cleaning_log.append({
            'action': 'standardize_dates',
            'details': 'Converted dates to standard YYYY/MM/DD format'
        })
        
        return df
    
    def _standardize_numbers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert Persian digits and formatted numbers to standard numeric format"""
        persian_digits = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
        
        for col in df.columns:
            if not isinstance(col, str):
                continue
            
            # Check if column might contain numbers
            number_keywords = ['تعداد', 'مبلغ', 'قیمت', 'عدد', 'count', 'amount', 'price', 'quantity']
            is_number_column = any(keyword in col.lower() for keyword in number_keywords)
            
            if not is_number_column:
                # Sample values to check
                sample_value = str(df[col].iloc[0]) if len(df) > 0 else ''
                is_number_column = bool(re.search(r'[\d۰-۹]', sample_value))
            
            if is_number_column:
                def convert_number(val):
                    if pd.isna(val):
                        return val
                    
                    val_str = str(val).strip()
                    
                    # Convert Persian digits to English
                    val_str = val_str.translate(persian_digits)
                    
                    # Remove thousand separators (commas, spaces)
                    val_str = re.sub(r'[,\s]', '', val_str)
                    
                    # Remove currency symbols
                    val_str = re.sub(r'[ریال تومان $ €]', '', val_str)
                    
                    # Try to convert to numeric
                    try:
                        if '.' in val_str:
                            return float(val_str)
                        else:
                            return int(val_str)
                    except (ValueError, TypeError):
                        return val_str
                
                df[col] = df[col].apply(convert_number)
        
        self.cleaning_log.append({
            'action': 'standardize_numbers',
            'details': 'Converted Persian digits and formatted numbers to standard format'
        })
        
        return df
    
    def _fix_persian_typos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fix common Persian typos"""
        typo_fixes = {
            'ك': 'ک',  # Arabic Kaf to Persian Kaf
            'ي': 'ی',  # Arabic Ye to Persian Ye
            'ۀ': 'ه',  # He with goal to standard He
            'ة': 'ه',  # Ta marbuta to He
            '‌‌': '‌',  # Double ZWNJ to single
        }
        
        for col in df.select_dtypes(include=['object']).columns:
            def fix_text(val):
                if not isinstance(val, str):
                    return val
                
                for wrong, correct in typo_fixes.items():
                    val = val.replace(wrong, correct)
                
                return val.strip()
            
            df[col] = df[col].apply(fix_text)
        
        self.cleaning_log.append({
            'action': 'fix_typos',
            'details': 'Fixed common Persian character typos'
        })
        
        return df
    
    def _detect_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect statistical outliers in numeric columns"""
        outlier_columns = []
        
        for col in df.select_dtypes(include=['number']).columns:
            if df[col].nunique() < 5:  # Skip columns with very few unique values
                continue
            
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
            
            outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            
            if outliers > 0:
                outlier_columns.append((col, outliers))
        
        if outlier_columns:
            self.cleaning_log.append({
                'action': 'detect_outliers',
                'details': f'Found {sum(count for _, count in outlier_columns)} potential outliers in {len(outlier_columns)} columns'
            })
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Intelligently handle missing values"""
        for col in df.columns:
            missing_count = df[col].isna().sum()
            
            if missing_count == 0:
                continue
            
            # For numeric columns, fill with median
            if df[col].dtype in ['int64', 'float64']:
                df[col] = df[col].fillna(df[col].median())
            
            # For text columns, fill with 'نامشخص' (Unknown in Persian)
            elif df[col].dtype == 'object':
                df[col] = df[col].fillna('نامشخص')
        
        self.cleaning_log.append({
            'action': 'handle_missing',
            'details': 'Filled missing values with appropriate defaults'
        })
        
        return df


def get_cleaning_summary(log: List[Dict]) -> str:
    """Generate human-readable summary of cleaning actions"""
    if not log:
        return "هیچ عملیات پاکسازی نیاز نبود."
    
    summary_lines = ["گزارش پاکسازی داده:"]
    for i, action in enumerate(log, 1):
        summary_lines.append(f"{i}. {action['details']}")
    
    return "\n".join(summary_lines)
