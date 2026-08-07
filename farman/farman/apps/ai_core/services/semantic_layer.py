"""
Semantic Layer Service
Maps different column names to unified business concepts
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class SemanticMapping:
    """Represents a mapping from various column names to a canonical concept"""
    canonical_name: str  # Standard name in the system
    persian_label: str   # Persian display name
    data_type: str       # expected data type
    aliases: Set[str] = field(default_factory=set)  # Alternative names
    domain: str = 'general'  # Which business domain this belongs to


class SemanticLayer:
    """
    Semantic mapping layer that understands different ways users name their data.
    Maps "Qty", "Quantity", "تعداد", "عدد" all to the same concept: "quantity"
    """
    
    def __init__(self):
        self.mappings: Dict[str, SemanticMapping] = {}
        self._initialize_standard_mappings()
    
    def _initialize_standard_mappings(self):
        """Initialize with standard business concepts"""
        
        # Sales Domain
        self.add_mapping(SemanticMapping(
            canonical_name='customer_name',
            persian_label='نام مشتری',
            data_type='string',
            domain='sales',
            aliases={'customer', 'client', 'buyer', 'مشتری', 'نام مشتری', 'خریدار'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='invoice_number',
            persian_label='شماره فاکتور',
            data_type='string',
            domain='sales',
            aliases={'invoice', 'factor', 'فاکتور', 'شماره فاکتور', 'invoice_no', 'inv_num'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='sale_date',
            persian_label='تاریخ فروش',
            data_type='date',
            domain='sales',
            aliases={'sale_date', 'فروش', 'تاریخ فروش', 'date_sold', 'transaction_date'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='total_amount',
            persian_label='مبلغ کل',
            data_type='number',
            domain='sales',
            aliases={'total', 'amount', 'مبلغ', 'مبلغ کل', 'قیمت نهایی', 'grand_total', 'sum'}
        ))
        
        # Inventory Domain
        self.add_mapping(SemanticMapping(
            canonical_name='product_name',
            persian_label='نام محصول',
            data_type='string',
            domain='inventory',
            aliases={'product', 'item', 'کالا', 'محصول', 'نام کالا', 'نام محصول', 'goods'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='quantity',
            persian_label='تعداد',
            data_type='number',
            domain='inventory',
            aliases={'qty', 'count', 'تعداد', 'عدد', 'quantity', 'تعداد موجودی', 'units'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='warehouse_name',
            persian_label='نام انبار',
            data_type='string',
            domain='inventory',
            aliases={'warehouse', 'انبار', 'نام انبار', 'storage', 'depot'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='stock_level',
            persian_label='موجودی فعلی',
            data_type='number',
            domain='inventory',
            aliases={'stock', 'موجودی', 'existing_stock', 'current_stock', 'موجودی فعلی'}
        ))
        
        # HR Domain
        self.add_mapping(SemanticMapping(
            canonical_name='employee_name',
            persian_label='نام کارمند',
            data_type='string',
            domain='hr',
            aliases={'employee', 'worker', 'کارمند', 'پرسنل', 'نام کارمند', 'staff', 'personnel'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='attendance_date',
            persian_label='تاریخ حضور',
            data_type='date',
            domain='hr',
            aliases={'date', 'تاریخ', 'روز', 'attendance_date', 'تاریخ حضور', 'work_date'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='attendance_status',
            persian_label='وضعیت حضور',
            data_type='string',
            domain='hr',
            aliases={'status', 'وضعیت', 'حضور', 'غیبت', 'attendance_status', 'state'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='salary',
            persian_label='حقوق',
            data_type='number',
            domain='hr',
            aliases={'salary', 'pay', 'حقوق', 'دستمزد', 'wage', 'monthly_salary'}
        ))
        
        # Accounting Domain
        self.add_mapping(SemanticMapping(
            canonical_name='account_name',
            persian_label='نام حساب',
            data_type='string',
            domain='accounting',
            aliases={'account', 'حساب', 'نام حساب', 'ledger_account'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='debit_amount',
            persian_label='مبلغ بدهکار',
            data_type='number',
            domain='accounting',
            aliases={'debit', 'بدهکار', 'مبلغ بدهکار', 'dr_amount'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='credit_amount',
            persian_label='مبلغ بستانکار',
            data_type='number',
            domain='accounting',
            aliases={'credit', 'بستانکار', 'مبلغ بستانکار', 'cr_amount'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='check_number',
            persian_label='شماره چک',
            data_type='string',
            domain='accounting',
            aliases={'check', 'چک', 'شماره چک', 'cheque_no', 'check_id'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='check_date',
            persian_label='تاریخ چک',
            data_type='date',
            domain='accounting',
            aliases={'check_date', 'تاریخ چک', 'due_date', 'سررسید'}
        ))
        
        # Purchasing Domain
        self.add_mapping(SemanticMapping(
            canonical_name='supplier_name',
            persian_label='نام تأمین‌کننده',
            data_type='string',
            domain='purchasing',
            aliases={'supplier', 'vendor', 'تأمین‌کننده', 'فروشنده', 'supplier_name', 'پیمانکار'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='purchase_order_number',
            persian_label='شماره سفارش خرید',
            data_type='string',
            domain='purchasing',
            aliases={'po_number', 'سفارش خرید', 'purchase_order', 'order_id'}
        ))
        
        # Production Domain
        self.add_mapping(SemanticMapping(
            canonical_name='machine_name',
            persian_label='نام دستگاه',
            data_type='string',
            domain='production',
            aliases={'machine', 'device', 'دستگاه', 'equipment', 'line'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='production_quantity',
            persian_label='تعداد تولید',
            data_type='number',
            domain='production',
            aliases={'output', 'تولید', 'تعداد تولید', 'produced_qty', 'manufactured'}
        ))
        
        self.add_mapping(SemanticMapping(
            canonical_name='defect_rate',
            persian_label='نرخ ضایعات',
            data_type='number',
            domain='production',
            aliases={'defects', 'ضایعات', 'نرخ ضایعات', 'waste', 'scrap'}
        ))
    
    def add_mapping(self, mapping: SemanticMapping):
        """Add a new semantic mapping"""
        self.mappings[mapping.canonical_name] = mapping
    
    def map_column(self, column_name: str, domain_hint: Optional[str] = None) -> Optional[SemanticMapping]:
        """
        Find the best semantic mapping for a given column name.
        
        Args:
            column_name: The column name from the Excel file
            domain_hint: Optional hint about which domain to prioritize
            
        Returns:
            SemanticMapping if found, None otherwise
        """
        column_clean = str(column_name).strip().lower()
        
        # First pass: exact match
        for mapping in self.mappings.values():
            if domain_hint and mapping.domain != domain_hint:
                continue
            
            if column_clean in {a.lower() for a in mapping.aliases}:
                return mapping
        
        # Second pass: partial match
        for mapping in self.mappings.values():
            if domain_hint and mapping.domain != domain_hint:
                continue
            
            for alias in mapping.aliases:
                if column_clean in alias.lower() or alias.lower() in column_clean:
                    return mapping
        
        # Third pass: check canonical name
        if column_clean in self.mappings:
            return self.mappings[column_clean]
        
        return None
    
    def get_canonical_name(self, column_name: str, domain_hint: Optional[str] = None) -> str:
        """Get the canonical name for a column, or return original if no mapping found"""
        mapping = self.map_column(column_name, domain_hint)
        return mapping.canonical_name if mapping else column_name
    
    def get_persian_label(self, column_name: str, domain_hint: Optional[str] = None) -> str:
        """Get the Persian label for a column"""
        mapping = self.map_column(column_name, domain_hint)
        return mapping.persian_label if mapping else column_name
    
    def normalize_dataframe_columns(self, df, domain_hint: Optional[str] = None):
        """
        Rename DataFrame columns to their canonical names.
        
        Args:
            df: pandas DataFrame
            domain_hint: Optional domain hint
            
        Returns:
            DataFrame with renamed columns
        """
        import pandas as pd
        
        new_columns = {}
        for col in df.columns:
            canonical = self.get_canonical_name(col, domain_hint)
            new_columns[col] = canonical
        
        return df.rename(columns=new_columns)
    
    def get_all_concepts(self, domain: Optional[str] = None) -> List[Dict]:
        """Get all semantic concepts, optionally filtered by domain"""
        results = []
        
        for mapping in self.mappings.values():
            if domain and mapping.domain != domain:
                continue
            
            results.append({
                'canonical_name': mapping.canonical_name,
                'persian_label': mapping.persian_label,
                'data_type': mapping.data_type,
                'domain': mapping.domain,
                'aliases': list(mapping.aliases)
            })
        
        return results
    
    def suggest_mappings(self, unknown_columns: List[str], domain: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Suggest possible mappings for columns that weren't automatically mapped.
        Useful for interactive user confirmation.
        
        Returns:
            Dict mapping unknown column names to list of suggested mappings
        """
        suggestions = {}
        
        for col in unknown_columns:
            col_clean = str(col).strip().lower()
            potential_matches = []
            
            for mapping in self.mappings.values():
                if domain and mapping.domain != domain:
                    continue
                
                # Check if any alias partially matches
                for alias in mapping.aliases:
                    alias_clean = alias.lower()
                    if (col_clean in alias_clean or 
                        alias_clean in col_clean or
                        self._similarity(col_clean, alias_clean) > 0.6):
                        
                        potential_matches.append({
                            'canonical_name': mapping.canonical_name,
                            'persian_label': mapping.persian_label,
                            'confidence': self._similarity(col_clean, alias_clean)
                        })
            
            # Sort by confidence and take top 3
            potential_matches.sort(key=lambda x: x['confidence'], reverse=True)
            suggestions[col] = potential_matches[:3]
        
        return suggestions
    
    def _similarity(self, s1: str, s2: str) -> float:
        """Simple string similarity score"""
        if not s1 or not s2:
            return 0.0
        
        # Simple Jaccard similarity on character bigrams
        def get_bigrams(s):
            return set(s[i:i+2] for i in range(len(s)-1))
        
        b1 = get_bigrams(s1)
        b2 = get_bigrams(s2)
        
        if not b1 or not b2:
            return 0.0
        
        intersection = len(b1 & b2)
        union = len(b1 | b2)
        
        return intersection / union if union > 0 else 0.0
