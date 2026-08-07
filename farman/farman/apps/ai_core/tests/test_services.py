"""
Unit tests for AI Core services
"""

import pytest
import pandas as pd
from farman.apps.ai_core.services import (
    DomainClassifier,
    DataCleaningEngine,
    SemanticLayer,
)


class TestDomainClassifier:
    """Tests for domain classification service"""
    
    def test_sales_detection(self):
        classifier = DomainClassifier()
        columns = ['نام مشتری', 'شماره فاکتور', 'مبلغ کل', 'تاریخ فروش']
        
        result = classifier.classify(columns)
        
        assert result.domain == 'sales'
        assert result.confidence > 0.5
        assert len(result.matched_columns) > 0
    
    def test_inventory_detection(self):
        classifier = DomainClassifier()
        columns = ['کالا', 'موجودی', 'انبار', 'تعداد']
        
        result = classifier.classify(columns)
        
        assert result.domain == 'inventory'
        assert result.confidence > 0.5
    
    def test_hr_detection(self):
        classifier = DomainClassifier()
        columns = ['کارمند', 'حقوق', 'حضور و غیاب', 'مرخصی']
        
        result = classifier.classify(columns)
        
        assert result.domain == 'hr'
        assert result.confidence > 0.5
    
    def test_unknown_domain(self):
        classifier = DomainClassifier()
        columns = ['col1', 'col2', 'random_data']
        
        result = classifier.classify(columns)
        
        assert result.domain == 'unknown' or result.confidence < 0.3


class TestDataCleaningEngine:
    """Tests for data cleaning engine"""
    
    def test_remove_empty_rows(self):
        engine = DataCleaningEngine()
        df = pd.DataFrame({
            'A': [1, 2, None, 4],
            'B': [5, None, None, 8]
        })
        
        cleaned_df, log = engine.clean_dataframe(df)
        
        # Should remove the completely empty row
        assert len(cleaned_df) < len(df)
        assert any(item['action'] == 'remove_empty' for item in log)
    
    def test_clean_column_names(self):
        engine = DataCleaningEngine()
        df = pd.DataFrame({
            '  نام مشتری  ': [1, 2, 3],
            'شماره فاکتور#': [4, 5, 6]
        })
        
        cleaned_df, log = engine.clean_dataframe(df)
        
        assert 'نام مشتری' in cleaned_df.columns
        assert 'شماره فاکتور' in cleaned_df.columns
    
    def test_persian_digit_conversion(self):
        engine = DataCleaningEngine()
        df = pd.DataFrame({
            'تعداد': ['۱۲۳', '۴۵۶', '۷۸۹']
        })
        
        cleaned_df, log = engine.clean_dataframe(df)
        
        assert cleaned_df['تعداد'].iloc[0] == 123
        assert cleaned_df['تعداد'].iloc[1] == 456
    
    def test_duplicate_removal(self):
        engine = DataCleaningEngine()
        df = pd.DataFrame({
            'A': [1, 1, 2, 3],
            'B': [4, 4, 5, 6]
        })
        
        cleaned_df, log = engine.clean_dataframe(df)
        
        assert len(cleaned_df) == 3
        assert any(item['action'] == 'remove_duplicates' for item in log)
    
    def test_persian_typo_fix(self):
        engine = DataCleaningEngine()
        df = pd.DataFrame({
            'name': ['علي', 'رضا', 'حسين']
        })
        
        cleaned_df, log = engine.clean_dataframe(df)
        
        assert cleaned_df['name'].iloc[0] == 'علی'
        assert cleaned_df['name'].iloc[2] == 'حسین'


class TestSemanticLayer:
    """Tests for semantic mapping layer"""
    
    def test_exact_match(self):
        layer = SemanticLayer()
        
        mapping = layer.map_column('customer')
        
        assert mapping is not None
        assert mapping.canonical_name == 'customer_name'
    
    def test_persian_match(self):
        layer = SemanticLayer()
        
        mapping = layer.map_column('مشتری')
        
        assert mapping is not None
        assert mapping.canonical_name == 'customer_name'
        assert mapping.persian_label == 'نام مشتری'
    
    def test_quantity_aliases(self):
        layer = SemanticLayer()
        
        for alias in ['تعداد', 'qty', 'quantity', 'عدد']:
            mapping = layer.map_column(alias)
            assert mapping is not None
            assert mapping.canonical_name == 'quantity'
    
    def test_normalize_dataframe(self):
        layer = SemanticLayer()
        df = pd.DataFrame({
            'customer': ['Ali', 'Reza'],
            'qty': [10, 20],
            'انبار': ['Tehran', 'Isfahan']
        })
        
        normalized_df = layer.normalize_dataframe_columns(df, domain_hint='sales')
        
        assert 'customer_name' in normalized_df.columns
        assert 'quantity' in normalized_df.columns
    
    def test_get_persian_label(self):
        layer = SemanticLayer()
        
        label = layer.get_persian_label('invoice_number')
        assert label == 'شماره فاکتور'
    
    def test_suggest_mappings(self):
        layer = SemanticLayer()
        
        suggestions = layer.suggest_mappings(['cust', 'inv'])
        
        assert 'cust' in suggestions
        assert len(suggestions['cust']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
