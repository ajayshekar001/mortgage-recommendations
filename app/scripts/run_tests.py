import unittest
import sys
import os
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.tests.test_loan_validation import TestLoanValidation

def run_tests():
    """Run the loan validation test suite and display results."""
    print("\n=== Loan Validation System Test Suite ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLoanValidation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Total tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    # Print failures and errors
    if result.failures:
        print("\n=== Failures ===")
        for failure in result.failures:
            print(f"\n{failure[0]}")
            print(failure[1])
    
    if result.errors:
        print("\n=== Errors ===")
        for error in result.errors:
            print(f"\n{error[0]}")
            print(error[1])
    
    # Return success if all tests passed
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 