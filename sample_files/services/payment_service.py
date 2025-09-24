"""
Payment Service - No Type Hints Test

All functions and methods have no type annotations.
Should generate maximum violations for comprehensive testing.
"""

from decimal import Decimal
from datetime import datetime


class PaymentProcessor:
    """Payment processor with no type hints."""
    
    def __init__(self, provider_name, api_key, sandbox_mode):
        """No type hints."""
        self.provider_name = provider_name
        self.api_key = api_key
        self.sandbox_mode = sandbox_mode
        self.transactions = []
    
    def validate_card(self, card_number, expiry_month, expiry_year, cvv):
        """No type hints."""
        # Basic validation logic
        if len(str(card_number)) != 16:
            return False
        if expiry_month < 1 or expiry_month > 12:
            return False
        if len(str(cvv)) != 3:
            return False
        return True
    
    def process_payment(self, amount, card_number, expiry_month, expiry_year, cvv):
        """No type hints."""
        if not self.validate_card(card_number, expiry_month, expiry_year, cvv):
            return False
        
        transaction_id = f"txn_{datetime.now().timestamp()}"
        transaction = {
            'id': transaction_id,
            'amount': amount,
            'status': 'completed',
            'processed_at': datetime.now()
        }
        self.transactions.append(transaction)
        return transaction_id
    
    def refund_payment(self, transaction_id, amount):
        """No type hints."""
        for transaction in self.transactions:
            if transaction['id'] == transaction_id:
                refund_record = {
                    'original_transaction': transaction_id,
                    'refund_amount': amount,
                    'refunded_at': datetime.now(),
                    'status': 'refunded'
                }
                self.transactions.append(refund_record)
                return True
        return False
    
    def get_transaction_status(self, transaction_id):
        """No type hints."""
        for transaction in self.transactions:
            if transaction.get('id') == transaction_id:
                return transaction['status']
        return None


class PaymentService:
    """Payment service with no type hints."""
    
    def __init__(self, processor):
        """No type hints."""
        self.processor = processor
        self.payment_history = []
        self.failed_payments = []
    
    def charge_customer(self, customer_id, amount, payment_method):
        """No type hints."""
        try:
            if payment_method['type'] == 'credit_card':
                transaction_id = self.processor.process_payment(
                    amount,
                    payment_method['card_number'],
                    payment_method['expiry_month'],
                    payment_method['expiry_year'],
                    payment_method['cvv']
                )
                
                if transaction_id:
                    payment_record = {
                        'customer_id': customer_id,
                        'amount': amount,
                        'transaction_id': transaction_id,
                        'status': 'success',
                        'charged_at': datetime.now()
                    }
                    self.payment_history.append(payment_record)
                    return transaction_id
            
            return None
        except Exception as e:
            self.record_failed_payment(customer_id, amount, str(e))
            return None
    
    def record_failed_payment(self, customer_id, amount, error_message):
        """No type hints."""
        failed_payment = {
            'customer_id': customer_id,
            'amount': amount,
            'error': error_message,
            'failed_at': datetime.now()
        }
        self.failed_payments.append(failed_payment)
    
    def get_customer_payment_history(self, customer_id):
        """No type hints."""
        return [
            payment for payment in self.payment_history
            if payment['customer_id'] == customer_id
        ]
    
    def calculate_total_revenue(self):
        """No type hints."""
        return sum(
            payment['amount'] for payment in self.payment_history
            if payment['status'] == 'success'
        )
