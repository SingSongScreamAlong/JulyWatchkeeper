"""
Test Multi-Language Processing for WATCHKEEPER

This script tests the language detection and translation capabilities of the language processor.
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.processors.language_processor import LanguageProcessor
from src.utils.logger import get_logger
from src.utils.config import load_config

# Initialize logger
logger = get_logger("watchkeeper.tests.language_processing")

# Test data with different languages
TEST_DATA = [
    {
        "title": "Peaceful Protests Continue in Capital City",
        "content": "Peaceful demonstrations continued for the third day in the capital city. Protesters are demanding political reforms, but no violence has been reported. Police presence remains minimal, and businesses are operating normally.",
        "expected_language": "en"
    },
    {
        "title": "Manifestations Pacifiques dans la Capitale",
        "content": "Les manifestations pacifiques se sont poursuivies pour le troisième jour dans la capitale. Les manifestants réclament des réformes politiques, mais aucune violence n'a été signalée. La présence policière reste minimale et les entreprises fonctionnent normalement.",
        "expected_language": "fr"
    },
    {
        "title": "Friedliche Proteste in der Hauptstadt",
        "content": "Die friedlichen Demonstrationen gingen den dritten Tag in der Hauptstadt weiter. Die Demonstranten fordern politische Reformen, aber es wurde keine Gewalt gemeldet. Die Polizeipräsenz bleibt minimal und die Geschäfte funktionieren normal.",
        "expected_language": "de"
    },
    {
        "title": "Mixed Language Test",
        "content": "This is a test with some French: Les manifestants sont dans la rue. And some German: Die Polizei ist anwesend. But mainly English content to test language detection with mixed content.",
        "expected_language": "en"
    }
]

async def test_language_processing() -> Dict[str, Any]:
    """
    Test the language detection and translation capabilities
    
    Returns:
        Dict[str, Any]: Test results
    """
    logger.info("Testing language processing")
    
    # Initialize language processor
    processor = LanguageProcessor()
    
    results = {
        "total_tests": len(TEST_DATA),
        "correct_detection": 0,
        "successful_translations": 0,
        "details": []
    }
    
    # Process each test item
    for i, test_item in enumerate(TEST_DATA):
        logger.info(f"Processing test item {i+1}/{len(TEST_DATA)}: {test_item['title']}")
        
        try:
            # Process the test item
            processed_item = await processor.process(test_item)
            
            # Get the detected language
            detected_language = processed_item.get("language_data", {}).get("detected_language", "unknown")
            
            # Check if language detection is correct
            language_match = detected_language == test_item["expected_language"]
            
            # Check translation if applicable
            translation_success = True
            if detected_language != "en" and processed_item.get("language_data", {}).get("is_translated", False):
                # Simple check that translation exists and is not empty
                translated_title = processed_item.get("language_data", {}).get("translated", {}).get("title", "")
                translated_content = processed_item.get("language_data", {}).get("translated", {}).get("content", "")
                
                translation_success = bool(translated_title) and bool(translated_content)
            
            # Update results
            if language_match:
                results["correct_detection"] += 1
            
            if translation_success and detected_language != "en":
                results["successful_translations"] += 1
            
            # Add details
            results["details"].append({
                "title": test_item["title"],
                "expected_language": test_item["expected_language"],
                "detected_language": detected_language,
                "language_match": language_match,
                "translation_success": translation_success,
                "translated_title": processed_item.get("language_data", {}).get("translated", {}).get("title", "N/A"),
                "translated_content_preview": processed_item.get("language_data", {}).get("translated", {}).get("content", "N/A")[:100] + "..." if processed_item.get("language_data", {}).get("translated", {}).get("content", "") else "N/A"
            })
            
            logger.info(f"Test item {i+1} - Language match: {language_match}, Translation success: {translation_success}")
            
        except Exception as e:
            logger.error(f"Error processing test item {i+1}: {e}", exc_info=True)
            results["details"].append({
                "title": test_item["title"],
                "error": str(e)
            })
    
    # Calculate accuracy
    results["detection_accuracy"] = results["correct_detection"] / results["total_tests"] if results["total_tests"] > 0 else 0
    
    # Calculate translation success rate (only for non-English items)
    non_english_count = sum(1 for item in TEST_DATA if item["expected_language"] != "en")
    results["translation_success_rate"] = results["successful_translations"] / non_english_count if non_english_count > 0 else 0
    
    return results

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test language processing capabilities")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--output", type=str, default="language_processing_results.json", help="Output file for results")
    args = parser.parse_args()
    
    # Load configuration
    load_config(args.config)
    
    # Run the test
    results = await test_language_processing()
    
    # Print results
    print("\n===== Language Processing Test Results =====")
    print(f"Total test items: {results['total_tests']}")
    print(f"Correct language detection: {results['correct_detection']} ({results['detection_accuracy']:.2%})")
    print(f"Successful translations: {results['successful_translations']} ({results['translation_success_rate']:.2%})")
    
    # Print details
    print("\nTest Details:")
    for i, detail in enumerate(results["details"]):
        print(f"\nItem {i+1}: {detail['title']}")
        print(f"  Expected language: {detail['expected_language']}")
        print(f"  Detected language: {detail['detected_language']}")
        print(f"  Language match: {'✓' if detail.get('language_match') else '✗'}")
        
        if detail.get("translation_success") is not None:
            print(f"  Translation success: {'✓' if detail['translation_success'] else '✗'}")
            if detail.get("translated_title") != "N/A":
                print(f"  Translated title: {detail['translated_title']}")
                print(f"  Translated content preview: {detail['translated_content_preview']}")
    
    # Save results to file
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to {args.output}")

if __name__ == "__main__":
    asyncio.run(main())
