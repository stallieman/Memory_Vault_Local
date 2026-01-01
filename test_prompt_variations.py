"""
Test RAG system with 5 different prompt variations
to verify consistent citation behavior
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestion import DocumentIngestion
from local_rag_ollama import (
    check_ollama_connection, get_effective_model,
    retrieve_context, ask_with_strict_validation,
    CitationValidationError
)

# 5 different ways to ask for the same information
TEST_PROMPTS = [
    "How do I read a CSV file in Python using pandas?",
    
    "Show me an example of loading a CSV file with pandas and displaying the first few rows",
    
    "What's the code to import and read a CSV file using the pandas library?",
    
    "Give me a Python example for reading CSV data with pandas, I need to see the basic syntax",
    
    "I want to load a CSV file into a pandas dataframe, how do I do that?"
]

def test_prompt(kb, model, prompt_num, prompt):
    """Test a single prompt and return result summary."""
    print(f"\n{'='*80}")
    print(f"TEST {prompt_num}/5")
    print(f"{'='*80}")
    print(f"Prompt: {prompt}")
    print(f"\n🔍 Searching knowledge base...")
    
    try:
        # Retrieve context
        context_chunks, allowed_ids, diagnostics = retrieve_context(kb, prompt)
        
        if not context_chunks:
            return {
                'prompt_num': prompt_num,
                'prompt': prompt[:60] + "...",
                'status': '⚠️ NO_CONTEXT',
                'error': 'No relevant context found',
                'citations': []
            }
        
        print(f"✓ Retrieved {diagnostics['final_count']} chunks")
        
        # Get answer with validation
        answer, citations = ask_with_strict_validation(
            prompt, context_chunks, allowed_ids, model, lenient_mode=True
        )
        
        # Extract first 150 chars of answer
        answer_preview = answer.replace('\n', ' ')[:150]
        
        print(f"\n✅ SUCCESS")
        print(f"Answer preview: {answer_preview}...")
        print(f"Citations: {sorted(citations)}")
        
        return {
            'prompt_num': prompt_num,
            'prompt': prompt[:60] + "...",
            'status': '✅ SUCCESS',
            'citations': sorted(citations),
            'answer_preview': answer_preview,
            'full_answer': answer
        }
        
    except CitationValidationError as e:
        print(f"\n❌ VALIDATION FAILED")
        print(f"Reason: {e.reason}")
        
        return {
            'prompt_num': prompt_num,
            'prompt': prompt[:60] + "...",
            'status': '❌ VALIDATION_FAILED',
            'error': e.reason,
            'citations': []
        }
        
    except Exception as e:
        print(f"\n❌ ERROR")
        print(f"Error: {str(e)}")
        
        return {
            'prompt_num': prompt_num,
            'prompt': prompt[:60] + "...",
            'status': '❌ ERROR',
            'error': str(e),
            'citations': []
        }

def main():
    print("\n" + "="*80)
    print("RAG SYSTEM PROMPT VARIATION TEST")
    print("Testing 5 different prompts for reading CSV files with pandas")
    print("="*80)
    
    # Check Ollama
    print("\n🔍 Checking Ollama connection...")
    is_connected, available_models = check_ollama_connection()
    
    if not is_connected:
        print("❌ Ollama is not running. Please start Ollama first.")
        return 1
    
    print(f"✓ Ollama is running")
    model = get_effective_model(available_models)
    print(f"✓ Using model: {model}")
    
    # Initialize knowledge base
    print("\n📚 Initializing knowledge base...")
    kb = DocumentIngestion()
    stats = kb.get_stats()
    print(f"✓ Loaded {stats['total_chunks']} chunks")
    
    # Run all tests
    results = []
    for i, prompt in enumerate(TEST_PROMPTS, 1):
        result = test_prompt(kb, model, i, prompt)
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    success_count = sum(1 for r in results if r['status'] == '✅ SUCCESS')
    
    print(f"\nResults: {success_count}/{len(TEST_PROMPTS)} successful\n")
    
    for r in results:
        status = r['status']
        print(f"{status} Test {r['prompt_num']}: {r['prompt']}")
        if r['citations']:
            print(f"         Citations: {r['citations']}")
        if 'error' in r:
            print(f"         Error: {r['error']}")
        print()
    
    # Check citation consistency
    successful_results = [r for r in results if r['status'] == '✅ SUCCESS']
    if len(successful_results) > 1:
        print("\n📊 Citation Analysis:")
        all_citations = [set(r['citations']) for r in successful_results]
        common_citations = set.intersection(*all_citations) if all_citations else set()
        
        if common_citations:
            print(f"   Common citations across all successful prompts: {sorted(common_citations)}")
        else:
            print(f"   ⚠️ No common citations - different chunks used for different prompts")
            for r in successful_results:
                print(f"      Test {r['prompt_num']}: {r['citations']}")
    
    print("\n" + "="*80)
    if success_count == len(TEST_PROMPTS):
        print("🎉 ALL TESTS PASSED - System handles prompt variations well!")
    elif success_count >= 3:
        print("⚠️ PARTIAL SUCCESS - Some prompts need refinement")
    else:
        print("❌ MOST TESTS FAILED - System needs improvement")
    print("="*80 + "\n")
    
    return 0 if success_count == len(TEST_PROMPTS) else 1

if __name__ == "__main__":
    sys.exit(main())
