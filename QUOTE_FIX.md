# Fix Applied: Quote Enforcement for RAG System

## Problem
The RAG system was rejecting answers with error: "Citation validation failed: No quotes found - evidence required"

The LLM was providing citations like `[chunk:id]` but wasn't including verbatim quotes from the source documents.

## Root Cause
1. The Modelfile system prompt didn't emphasize quote requirements strongly enough
2. The user prompts could be more explicit with examples of correct/wrong formats

## Changes Made

### 1. Updated Modelfile (ollama/Modelfile.rag-grounded)
- Added **CRITICAL RULES** section emphasizing quote requirement
- Added **MANDATORY FORMAT** with clear examples
- Included both correct and incorrect examples to show contrast
- Emphasized "verbatim text copied exactly from the source"

### 2. Strengthened User Prompts (src/local_rag_ollama.py)
- First prompt: Added concrete examples of WRONG vs CORRECT format
- Retry prompt: Made it much more direct with "YOU MUST INCLUDE VERBATIM QUOTES"
- Added specific examples relevant to technical questions (like API calls)

### 3. Recreated the Model
- Ran `update_model.bat` to recreate `rag-grounded-nemo` with the new system prompt
- Model now has quote enforcement baked into its behavior

## Testing
Try asking technical questions in the GUI like:
- "I need the correct API call for creating an index template in dev tools kibana"
- "How do I create a Docker container?"
- "What's the git command to create a branch?"

The model should now respond with proper quotes:
```
To create an index template, use "PUT _index_template/my-template" [chunk:abc123_0001].
```

Instead of the old format without quotes:
```
Use PUT _index_template to create templates [chunk:abc123_0001]
```

## Files Modified
- [ollama/Modelfile.rag-grounded](ollama/Modelfile.rag-grounded) - Updated system prompt
- [src/local_rag_ollama.py](src/local_rag_ollama.py) - Strengthened user prompts
- [update_model.bat](update_model.bat) - New script to recreate model easily

## Next Steps
1. Launch the GUI (via desktop shortcut)
2. Ask your Kibana question again
3. The model should now provide proper quoted answers with citations

Date: 2026-01-01
