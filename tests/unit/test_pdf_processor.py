"""
Unit tests for PDF processor
Tests PDF text extraction and metadata parsing
"""
import os
import pytest
from src.services.pdf_processor import _is_valid_title, _extract_pdf_metadata, extract_pages_text


def test_is_valid_title_valid():
    """Test validation of proper paper titles"""
    assert _is_valid_title("Attention is All You Need") == True
    assert _is_valid_title("A Survey of Deep Learning Techniques") == True
    assert _is_valid_title("Blockchain Applications in Healthcare") == True


def test_is_valid_title_invalid():
    """Test rejection of invalid titles"""
    # Too short
    assert _is_valid_title("abc") == False
    assert _is_valid_title("") == False
    
    # Just numbers
    assert _is_valid_title("123 456 789") == False
    assert _is_valid_title("253 255..260") == False
    
    # Page numbers
    assert _is_valid_title("Page 1") == False
    assert _is_valid_title("page 5") == False
    
    # Figure/Table labels
    assert _is_valid_title("Figure 1") == False
    assert _is_valid_title("Table 3") == False


def test_extract_pages_text_returns_tuple():
    """Test that extract_pages_text returns list of (page_num, text) tuples"""
    # This test requires an actual PDF file
    # We'll create a simple test that checks the structure
    # In a real scenario, you'd need a fixture PDF
    pass  # Skip for now - would need fixture PDF


def test_metadata_extraction_structure():
    """Test that metadata extraction returns expected keys"""
    # Note: This test would need a real PDF file to work properly
    # For now, we test the function exists and has correct signature
    from inspect import signature
    sig = signature(_extract_pdf_metadata)
    params = list(sig.parameters.keys())
    assert 'file_path' in params


def test_section_patterns_coverage():
    """Test that common section patterns are recognized"""
    from src.services.pdf_processor import SECTION_PATTERNS
    
    # Check that key sections are defined
    section_names = [name for name, _ in SECTION_PATTERNS]
    
    expected_sections = ["Abstract", "Introduction", "Methods", "Results", 
                        "Discussion", "Conclusion", "References"]
    
    for expected in expected_sections:
        assert expected in section_names, f"Missing section: {expected}"


def test_section_pattern_matching():
    """Test regex patterns match common section header formats"""
    from src.services.pdf_processor import SECTION_PATTERNS
    
    # Test various formats
    test_cases = [
        ("Abstract", ["Abstract", "ABSTRACT", "1. Abstract", "1) Abstract"]),
        ("Introduction", ["Introduction", "INTRODUCTION", "1. Introduction", "Background"]),
        ("Methods", ["Methods", "Methodology", "Materials and Methods", "2. Methods"]),
        ("Results", ["Results", "3. Results", "Findings", "Experiments"]),
        ("Conclusion", ["Conclusion", "Conclusions", "Concluding Remarks"]),
        ("References", ["References", "Bibliography", "Citations"]),
    ]
    
    for section_name, test_strings in test_cases:
        pattern = next(pat for name, pat in SECTION_PATTERNS if name == section_name)
        
        for test_str in test_strings:
            match = pattern.search(test_str)
            assert match is not None, f"Pattern for '{section_name}' should match '{test_str}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
