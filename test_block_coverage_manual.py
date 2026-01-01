"""
Manual test: validate the problematic answer that triggered this feature request.
"""

import sys
sys.path.insert(0, "src")

from local_rag_ollama import validate_answer, CitationValidationError

# The problematic answer from user's report
problematic_answer = '''"SELECT customer_id, order_id, order_date, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) AS rn FROM orders" [chunk:a071ddb5f343_2]

In deze query wordt eerst een CTE (Common Table Expression) gemaakt met de naam `ranked_orders`. In deze CTE worden de orders geïndexeerd per klant (`PARTITION BY customer_id`) en gesorteerd op de datum van de bestelling in aflopende volgorde (`ORDER BY order_date DESC`). Vervolgens wordt een unieke nummering toegewezen aan elke rij binnen elke groep met behulp van `ROW_NUMBER()`.

In de hoofdquery worden dan alleen de rijen geselecteerd waar het gerangschikte nummer 1 is, wat de laatste bestelling per klant vertegenwoordigt.

Wanneer je beter een `CROSS APPLY (SELECT TOP 1 ... ORDER BY ...)` zou kunnen gebruiken in plaats van window functions, hangt af van verschillende factoren. In sommige gevallen kan het gebruik van `CROSS APPLY` sneller en efficiënter zijn dan het gebruik van window functions, vooral bij grote hoeveelheden data. Daarnaast kan `CROSS APPLY` handiger zijn om te implementeren in bestaande queries of procedures.

Tegenover oficer kunnen window functions echter meer flexibiliteit bieden voor complexe query's en kunnen ze gemakkelijker gecombineerd worden met andere SQL-constructies, zoals aggregaties of subqueries. Bovendien ondersteunen sommige databasesystemen niet alle functies van `CROSS APPLY`, waardoor het gebruik van window functions een betere keuze kan zijn.

In de gegeven context is er geen informatie beschikbaar over welke database gebruikt wordt of welke prestatieve factoren relevant zijn, dus ik kan niet zeggen welk alternatief beter zou zijn in deze specifieke situatie.'''

debug_payload = {
    'model': 'test-manual',
    'user_prompt': 'Test prompt',
    'allowed_ids': {'a071ddb5f343_2'},
}

print("=" * 80)
print("MANUAL TEST: Problematic Answer from User Report")
print("=" * 80)
print("\nThis answer has 1 citation at the top, then many uncited paragraphs.")
print("Expected: FAIL with citation coverage error\n")

try:
    result = validate_answer(
        problematic_answer,
        allowed_ids={'a071ddb5f343_2'},
        debug_payload=debug_payload,
        require_quotes=False  # Don't check quotes for this test
    )
    print(f"\n❌ TEST FAILED - Answer was accepted but should be rejected!")
    print(f"   Citations found: {result}")
    sys.exit(1)
except CitationValidationError as e:
    print(f"\n✅ TEST PASSED - Answer correctly rejected!")
    print(f"   Reason: {e.reason}")
    print(f"\nThis is the desired behavior: hallucinated paragraphs are now blocked.")
    sys.exit(0)
