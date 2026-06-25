
import json
from slides_agent import validate_slide_content, clean_document_text

def test_investor_audit():
    print("Testing Investor-Ready Audit Logic...")
    print("-" * 60)
    
    # 1. Test Slide 5 Revenue Pillars Fix
    print("[*] Testing Slide 5 Revenue Pillars...")
    test_slides_5 = [
        {
            "title": "Revenue Model",
            "type": "standard",
            "bullets": ["Generic point 1", "Generic point 2"]
        }
    ]
    
    validated_5 = validate_slide_content(test_slides_5, topic="Gaio Investor Presentation", document_text="Investor data context")
    
    # Check if all 7 pillars are present
    pillars_required = [
        "Global Title", "Continental Rights", "Media Rights", 
        "Startup Fees", "Talent Access", "Partnerships", "Global AI Institute"
    ]
    
    content_5 = " ".join([str(b) for b in validated_5[0]["bullets"]])
    missing_5 = [p for p in pillars_required if p.lower() not in content_5.lower()]
    
    if not missing_5:
        print("[PASS] Slide 5: All 7 mandatory pillars found.")
    else:
        print(f"[FAIL] Slide 5: Missing pillars: {missing_5}")
        
    # 2. Test Slide 6 Financial Scaling Fix
    print("[*] Testing Slide 6 Financial Scaling...")
    test_slides_6 = [
        {
            "title": "Financial Projections",
            "type": "standard",
            "bullets": ["Year 1 Target: 1010", "Year 2 Scale: 2420", "Year 3 Maturity: 4950"]
        }
    ]
    
    validated_6 = validate_slide_content(test_slides_6, topic="Gaio Investor Presentation", document_text="Investor data context")
    
    content_6 = " ".join([str(b) for b in validated_6[0]["bullets"]])
    if "1.01M" in content_6 and "2.42M" in content_6 and "4.95M" in content_6:
        print("[PASS] Slide 6: All revenue figures correctly scaled to 'M'.")
    else:
        print(f"[FAIL] Slide 6: Scaling failed. Content: {content_6}")
        
    # 3. Test Professional Polish
    print("[*] Testing Professional Polish (Text Fragments)...")
    fragment_text = "The insti. is high. Participation o"
    cleaned = clean_document_text(fragment_text)
    
    if "institutions" in cleaned and "Participation of global sponsors" in cleaned:
        print("[PASS] Professional Polish: Fragments 'insti.' and 'Participation o' fixed.")
    else:
        print(f"[FAIL] Professional Polish: fragments found. Cleaned text: {cleaned}")

if __name__ == "__main__":
    test_investor_audit()
