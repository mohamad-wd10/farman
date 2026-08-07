"""
Domain Classifier Service
Detects business domain of uploaded Excel files using AI heuristics and patterns
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class DomainMatch:
    domain: str
    confidence: float
    matched_columns: List[str]
    matched_values: List[str]


class DomainClassifier:
    """
    Intelligent domain classifier for Excel files.
    Detects if file is related to: Sales, Inventory, HR, Accounting, etc.
    """
    
    DOMAIN_PATTERNS = {
        'sales': {
            'columns': [
                r'فروش', r'مشتری', r'فاکتور', r'سفارش', r'قیمت', r'تخفیف',
                r'customer', r'sales', r'invoice', r'order', r'price', r'discount',
                r'amount', r'total', r'payment', r'buyer', r'client'
            ],
            'keywords': [
                r'فروش', r'خرید', r'مشتری', r'سفارش', r'فاکتور'
            ]
        },
        'inventory': {
            'columns': [
                r'موجودی', r'انبار', r'کالا', r'محصول', r'تعداد', r'واحد',
                r'quantity', r'stock', r'warehouse', r'product', r'item',
                r'sku', r'barcode', r'inventory', r'unit'
            ],
            'keywords': [
                r'انبار', r'موجودی', r'کالا', r'محصول', r'قطعه'
            ]
        },
        'hr': {
            'columns': [
                r'کارمند', r'پرسنل', r'حضور', r'غیبت', r'مرخصی', r'حقوق',
                r'employee', r'attendance', r'leave', r'salary', r'payroll',
                r'personnel', r'staff', r'worker', r'department'
            ],
            'keywords': [
                r'کارمند', r'پرسنل', r'حقوق', r'مرخصی', r'غیبت'
            ]
        },
        'accounting': {
            'columns': [
                r'حساب', r'بدهکار', r'بستانکار', r'تراز', r'سند', r'چک',
                r'account', r'debit', r'credit', r'balance', r'voucher',
                r'check', r'bank', r'finance', r'ledger', r'journal'
            ],
            'keywords': [
                r'حساب', r'چک', r'بانک', r'تراز', r'سند حسابداری'
            ]
        },
        'purchasing': {
            'columns': [
                r'خرید', r'تأمین‌کننده', r'سفارش خرید', r'فاکتور خرید',
                r'purchase', r'supplier', r'vendor', r'po', r'procurement'
            ],
            'keywords': [
                r'خرید', r'تأمین', r'سفارش خرید', r'پیمانکار'
            ]
        },
        'production': {
            'columns': [
                r'تولید', r'خط تولید', r'دستگاه', r'ضایعات', r'بهره‌وری',
                r'production', r'manufacturing', r'machine', r'line', r'output'
            ],
            'keywords': [
                r'تولید', r'کارخانه', r'دستگاه', r'خط تولید'
            ]
        }
    }
    
    def __init__(self):
        self.compiled_patterns = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance"""
        for domain, config in self.DOMAIN_PATTERNS.items():
            self.compiled_patterns[domain] = {
                'columns': [re.compile(p, re.IGNORECASE) for p in config['columns']],
                'keywords': [re.compile(p, re.IGNORECASE) for p in config['keywords']]
            }
    
    def classify(self, columns: List[str], sample_values: List[str] = None) -> DomainMatch:
        """
        Classify the domain of a file based on column names and sample values.
        
        Args:
            columns: List of column names from the Excel file
            sample_values: Optional list of sample cell values
            
        Returns:
            DomainMatch with detected domain and confidence score
        """
        scores: Dict[str, Dict] = {}
        
        for domain, patterns in self.compiled_patterns.items():
            matched_cols = []
            matched_vals = []
            score = 0.0
            
            # Check column names
            for col in columns:
                for pattern in patterns['columns']:
                    if pattern.search(str(col)):
                        matched_cols.append(col)
                        score += 1.5
                        break
            
            # Check sample values if provided
            if sample_values:
                for val in sample_values[:20]:  # Limit to first 20 values
                    for pattern in patterns['keywords']:
                        if pattern.search(str(val)):
                            matched_vals.append(val)
                            score += 1.0
                            break
            
            if score > 0:
                # Normalize score (max ~10-15 points typically)
                confidence = min(score / 10.0, 1.0)
                scores[domain] = {
                    'confidence': confidence,
                    'matched_columns': matched_cols,
                    'matched_values': matched_vals
                }
        
        if not scores:
            return DomainMatch(
                domain='unknown',
                confidence=0.0,
                matched_columns=[],
                matched_values=[]
            )
        
        # Get best match
        best_domain = max(scores, key=lambda x: scores[x]['confidence'])
        best_score = scores[best_domain]
        
        return DomainMatch(
            domain=best_domain,
            confidence=best_score['confidence'],
            matched_columns=best_score['matched_columns'],
            matched_values=best_score['matched_values']
        )
    
    def get_all_domains(self) -> List[Tuple[str, str]]:
        """Return list of all supported domains with Persian labels"""
        domain_labels = {
            'sales': ('فروش', 'مدیریت فروش و مشتریان'),
            'inventory': ('انبار', 'مدیریت موجودی و انبار'),
            'hr': ('منابع انسانی', 'پرسنل، حضور و غیاب، حقوق'),
            'accounting': ('حسابداری', 'اسناد مالی، چک، حساب‌ها'),
            'purchasing': ('خرید', 'تأمین‌کنندگان و سفارشات خرید'),
            'production': ('تولید', 'خطوط تولید و دستگاه‌ها'),
            'unknown': ('نامشخص', 'نیاز به بررسی دستی')
        }
        
        return [
            (domain, f"{label[0]} - {label[1]}")
            for domain, label in domain_labels.items()
            if domain != 'unknown'
        ]
