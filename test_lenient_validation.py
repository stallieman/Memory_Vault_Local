"""
Test lenient citation validation mode
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from local_rag_ollama import validate_answer, CitationValidationError  # type: ignore

def test_lenient_mode():
    """Test that lenient mode allows some uncited blocks"""
    
    # Simulate an answer with 4 blocks: 2 cited, 2 uncited (50% coverage)
    answer_text = """## SQL WINDOW Functions

Here's how SQL WINDOW functions work:

WINDOW functions perform calculations across a set of rows. "They differ from GROUP BY in that they don't collapse rows" [chunk:sql_001].

Common functions include ROW_NUMBER(), RANK(), and DENSE_RANK(). "These ranking functions assign numbers to rows based on ordering criteria" [chunk:sql_002].

You can use PARTITION BY to divide results into groups for separate window calculations."""
    
    allowed_ids = {"sql_001", "sql_002", "sql_003"}
    debug_payload = {"test": "lenient_mode"}
    
    # Test STRICT mode (should fail with 2 uncited blocks)
    print("Testing STRICT mode (should fail)...")
    try:
        citations = validate_answer(answer_text, allowed_ids, debug_payload, 
                                   require_quotes=True, lenient_mode=False)
        print(f"❌ UNEXPECTED: Strict mode passed with citations: {citations}")
    except CitationValidationError as e:
        print(f"✅ Expected failure in strict mode: {e.reason}")
    
    # Test LENIENT mode (should pass with 50% coverage)
    print("\nTesting LENIENT mode (should pass)...")
    try:
        citations = validate_answer(answer_text, allowed_ids, debug_payload, 
                                   require_quotes=True, lenient_mode=True)
        print(f"✅ Lenient mode passed with citations: {citations}")
        print(f"   Found {len(citations)} citations from 4 blocks (50% coverage)")
    except CitationValidationError as e:
        print(f"❌ UNEXPECTED: Lenient mode failed: {e.reason}")

if __name__ == "__main__":
    test_lenient_mode()
