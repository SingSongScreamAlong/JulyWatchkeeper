"""
Test Threat Classification for WATCHKEEPER

This script tests the threat classification accuracy of the AI processor.
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

from src.processors.ai_processor import AIProcessor
from src.utils.logger import get_logger
from src.utils.config import load_config

# Initialize logger
logger = get_logger("watchkeeper.tests.threat_classification")

# Test data with known threat classifications
TEST_DATA = [
    {
        "title": "Peaceful Protests Continue in Capital City",
        "content": "Peaceful demonstrations continued for the third day in the capital city. Protesters are demanding political reforms, but no violence has been reported. Police presence remains minimal, and businesses are operating normally.",
        "expected_threat": {
            "level": "Low",
            "type": "Civil Unrest"
        }
    },
    {
        "title": "Violent Clashes Between Protesters and Police",
        "content": "Violent clashes erupted between protesters and police in the downtown area. Multiple injuries have been reported, and authorities have deployed riot police. The government has imposed a curfew from 8 PM to 6 AM until further notice. Foreign embassies have advised their citizens to avoid the affected areas.",
        "expected_threat": {
            "level": "High",
            "type": "Civil Unrest"
        }
    },
    {
        "title": "New COVID-19 Variant Detected",
        "content": "Health authorities have confirmed the detection of a new COVID-19 variant in the region. Initial studies suggest it may be more transmissible but not more severe than previous variants. No travel restrictions have been implemented yet, but officials recommend wearing masks in crowded places.",
        "expected_threat": {
            "level": "Medium",
            "type": "Health"
        }
    },
    {
        "title": "Earthquake Strikes Coastal Region",
        "content": "A magnitude 7.2 earthquake struck the coastal region early this morning, causing significant damage to infrastructure. Several buildings have collapsed, and casualties have been reported. Rescue operations are underway, and the government has declared a state of emergency. International aid organizations are mobilizing resources.",
        "expected_threat": {
            "level": "Critical",
            "type": "Natural Disaster"
        }
    },
    {
        "title": "New Trade Agreement Signed",
        "content": "Representatives from five countries signed a new trade agreement today, aimed at reducing tariffs and promoting economic cooperation. The agreement is expected to boost regional trade by 15% over the next five years. Business leaders have welcomed the move, citing potential job creation and investment opportunities.",
        "expected_threat": {
            "level": "None",
            "type": "Political"
        }
    }
]

async def test_threat_classification(model_name: str) -> Dict[str, Any]:
    """
    Test the threat classification accuracy of the AI processor
    
    Args:
        model_name: Name of the Ollama model to use
        
    Returns:
        Dict[str, Any]: Test results
    """
    logger.info(f"Testing threat classification with model: {model_name}")
    
    # Initialize AI processor
    processor = AIProcessor(model_name=model_name)
    
    results = {
        "total_tests": len(TEST_DATA),
        "correct_level": 0,
        "correct_type": 0,
        "correct_both": 0,
        "details": []
    }
    
    # Process each test item
    for i, test_item in enumerate(TEST_DATA):
        logger.info(f"Processing test item {i+1}/{len(TEST_DATA)}: {test_item['title']}")
        
        try:
            # Process the test item
            processed_item = await processor.process(test_item)
            
            # Get the threat classification
            threat = processed_item.get("ai_analysis", {}).get("threat", {})
            
            # Compare with expected threat
            expected = test_item["expected_threat"]
            level_match = threat.get("level") == expected["level"]
            type_match = threat.get("type") == expected["type"]
            
            # Update results
            if level_match:
                results["correct_level"] += 1
            if type_match:
                results["correct_type"] += 1
            if level_match and type_match:
                results["correct_both"] += 1
            
            # Add details
            results["details"].append({
                "title": test_item["title"],
                "expected": expected,
                "actual": {
                    "level": threat.get("level"),
                    "type": threat.get("type"),
                    "confidence": threat.get("confidence")
                },
                "level_match": level_match,
                "type_match": type_match
            })
            
            logger.info(f"Test item {i+1} - Level match: {level_match}, Type match: {type_match}")
            
        except Exception as e:
            logger.error(f"Error processing test item {i+1}: {e}", exc_info=True)
            results["details"].append({
                "title": test_item["title"],
                "error": str(e)
            })
    
    # Calculate accuracy
    results["level_accuracy"] = results["correct_level"] / results["total_tests"] if results["total_tests"] > 0 else 0
    results["type_accuracy"] = results["correct_type"] / results["total_tests"] if results["total_tests"] > 0 else 0
    results["overall_accuracy"] = results["correct_both"] / results["total_tests"] if results["total_tests"] > 0 else 0
    
    return results

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test threat classification accuracy")
    parser.add_argument("--model", type=str, default="llama3.1:8b", help="Ollama model to use")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--output", type=str, default="threat_classification_results.json", help="Output file for results")
    args = parser.parse_args()
    
    # Load configuration
    load_config(args.config)
    
    # Run the test
    results = await test_threat_classification(args.model)
    
    # Print results
    print("\n===== Threat Classification Test Results =====")
    print(f"Model: {args.model}")
    print(f"Total test items: {results['total_tests']}")
    print(f"Correct threat level: {results['correct_level']} ({results['level_accuracy']:.2%})")
    print(f"Correct threat type: {results['correct_type']} ({results['type_accuracy']:.2%})")
    print(f"Correct both level and type: {results['correct_both']} ({results['overall_accuracy']:.2%})")
    
    # Save results to file
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to {args.output}")

if __name__ == "__main__":
    asyncio.run(main())
