"""
Unit tests for citation validator

Tests the fixed validation logic that no longer bans generic words.
"""

import sys
sys.path.insert(0, "src")

from local_rag_ollama import validate_answer, CitationValidationError, IDK


def test_case(name: str, text: str, allowed_ids: set, should_pass: bool, require_quotes: bool = True):
    """Run a single test case."""
    print(f"\n{'='*80}")
    print(f"TEST: {name}")
    print(f"{'='*80}")
    print(f"Input text: {text[:200]}...")
    print(f"Allowed IDs: {sorted(allowed_ids)}")
    print(f"Expected: {'PASS' if should_pass else 'FAIL'}")
    print(f"Require quotes: {require_quotes}")
    
    debug_payload = {
        'model': 'test-model',
        'user_prompt': 'test prompt',
        'allowed_ids': allowed_ids,
    }
    
    try:
        result = validate_answer(text, allowed_ids, debug_payload, require_quotes=require_quotes)
        if should_pass:
            print(f"✅ PASS - Citations found: {result}")
            return True
        else:
            print(f"❌ FAIL - Expected validation error, but passed with: {result}")
            return False
    except CitationValidationError as e:
        if not should_pass:
            print(f"✅ PASS - Correctly rejected: {e.reason}")
            return True
        else:
            print(f"❌ FAIL - Unexpected validation error: {e.reason}")
            return False
    except Exception as e:
        print(f"❌ FAIL - Unexpected exception: {e}")
        return False


def main():
    print("="*80)
    print("CITATION VALIDATOR UNIT TESTS")
    print("="*80)
    
    test_results = []
    
    # TEST 1: Valid answer with "page" word (should PASS now)
    test_results.append(test_case(
        name="Valid answer with 'page' word",
        text='"The configuration is on page 42" [chunk:abc123_0001]',
        allowed_ids={'abc123_0001'},
        should_pass=True
    ))
    
    # TEST 2: Valid answer with "chapter" word (should PASS now)
    test_results.append(test_case(
        name="Valid answer with 'chapter' word",
        text='"As explained in chapter 5, Docker uses namespaces" [chunk:docker_001]',
        allowed_ids={'docker_001'},
        should_pass=True
    ))
    
    # TEST 3: Invalid chunk ID (should FAIL)
    test_results.append(test_case(
        name="Invalid chunk ID (hallucinated)",
        text='"The answer is here" [chunk:fake_chunk_999]',
        allowed_ids={'abc123_0001'},
        should_pass=False
    ))
    
    # TEST 4: No citations (should FAIL)
    test_results.append(test_case(
        name="No citations found",
        text='"This is an answer without any citations at all."',
        allowed_ids={'abc123_0001'},
        should_pass=False
    ))
    
    # TEST 5: External URL (should FAIL)
    test_results.append(test_case(
        name="External URL detected",
        text='"See https://stackoverflow.com/questions/123 for more info" [chunk:abc123_0001]',
        allowed_ids={'abc123_0001'},
        should_pass=False
    ))
    
    # TEST 5b: "https://" in text without full URL (should PASS)
    test_results.append(test_case(
        name="https:// mentioned in explanation (not a real URL)",
        text='"Configure the endpoint using https:// protocol" [chunk:abc123_0001]',
        allowed_ids={'abc123_0001'},
        should_pass=True
    ))
    
    # TEST 6: Valid answer with section reference
    test_results.append(test_case(
        name="Valid answer with 'section' word",
        text='"According to section 3.2, the cache is configured as follows" [chunk:tdv_guide_042]',
        allowed_ids={'tdv_guide_042'},
        should_pass=True
    ))
    
    # TEST 7: IDK response (should PASS)
    test_results.append(test_case(
        name="IDK response",
        text=IDK,
        allowed_ids={'abc123_0001'},
        should_pass=True,
        require_quotes=False
    ))
    
    # TEST 8: IDK response (Dutch variant)
    test_results.append(test_case(
        name="IDK response (Dutch variant)",
        text='Ik weet het niet gebaseerd op het gegeven context.',
        allowed_ids={'abc123_0001'},
        should_pass=True,
        require_quotes=False
    ))
    
    # TEST 9: No quotes (should FAIL when require_quotes=True)
    test_results.append(test_case(
        name="No quotes (evidence missing)",
        text='The answer is here [chunk:abc123_0001]',  # No quotes
        allowed_ids={'abc123_0001'},
        should_pass=False,
        require_quotes=True
    ))
    
    # TEST 10: Multiple valid citations
    test_results.append(test_case(
        name="Multiple valid citations",
        text='"First point" [chunk:doc1_001] and "second point" [chunk:doc2_002]',
        allowed_ids={'doc1_001', 'doc2_002'},
        should_pass=True
    ))
    
    # TEST 11: Mixed valid and invalid IDs (should FAIL)
    test_results.append(test_case(
        name="Mixed valid and invalid chunk IDs",
        text='"Valid source" [chunk:doc1_001] and "fake source" [chunk:hallucinated_999]',
        allowed_ids={'doc1_001'},  # hallucinated_999 not in allowed
        should_pass=False
    ))
    
    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    passed = sum(test_results)
    total = len(test_results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ {total - passed} TEST(S) FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
