#!/usr/bin/env python3
"""
Intelligence Source Verification Utility
This script verifies and validates intelligence sources for reliability and availability
"""

import json
import logging
import argparse
import os
import sys
import asyncio
import aiohttp
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('watchkeeper.verify_sources')

class SourceVerifier:
    """Intelligence source verification and validation tool"""
    
    def __init__(self, sources_file: str = 'config/combined_sources.json'):
        """Initialize the verifier with sources configuration"""
        self.sources_file = sources_file
        self.sources = []
        self.results = {}
        
        if not os.path.exists(sources_file):
            logger.error(f"Sources file not found: {sources_file}")
            sys.exit(1)
            
        try:
            with open(sources_file, 'r') as f:
                data = json.load(f)
                self.sources = data.get('sources', [])
                
            logger.info(f"Loaded {len(self.sources)} intelligence sources from {sources_file}")
        except Exception as e:
            logger.error(f"Error loading sources: {e}")
            sys.exit(1)
    
    async def verify_all_sources(self) -> Dict[str, Any]:
        """Verify all intelligence sources"""
        tasks = []
        
        async with aiohttp.ClientSession() as session:
            for source in self.sources:
                name = source.get('name', 'Unknown')
                url = source.get('url', '')
                source_type = source.get('type', 'rss')
                
                if not url:
                    logger.warning(f"Source {name} has no URL, skipping")
                    continue
                
                tasks.append(self.verify_source(session, source))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for source, result in zip(self.sources, results):
                name = source.get('name', 'Unknown')
                if isinstance(result, Exception):
                    logger.error(f"Error verifying source {name}: {result}")
                    self.results[name] = {
                        'status': 'error',
                        'error': str(result),
                        'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                    }
                else:
                    self.results[name] = result
        
        return self.results
    
    async def verify_source(self, session: aiohttp.ClientSession, source: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a single intelligence source"""
        name = source.get('name', 'Unknown')
        url = source.get('url', '')
        source_type = source.get('type', 'rss')
        
        logger.info(f"Verifying source: {name} ({url}) - Type: {source_type}")
        
        result = {
            'name': name,
            'url': url,
            'type': source_type,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        start_time = time.time()
        
        try:
            # Prepare headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Add API key if required
            if source.get('api_key_required', False):
                api_key_env = source.get('api_key_env', '')
                if api_key_env and api_key_env in os.environ:
                    api_key = os.environ.get(api_key_env)
                    headers['Authorization'] = f"Bearer {api_key}"
                else:
                    result['status'] = 'error'
                    result['error'] = f"API key required but not found in environment: {api_key_env}"
                    return result
            
            # Add custom headers if specified
            if 'headers' in source:
                headers.update(source['headers'])
            
            # Prepare query parameters
            params = {}
            if 'query_params' in source:
                params.update(source['query_params'])
            
            # Make request
            async with session.get(url, headers=headers, params=params, timeout=30) as response:
                result['status_code'] = response.status
                result['response_time'] = round(time.time() - start_time, 2)
                
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    result['content_type'] = content_type
                    
                    # Check content based on source type
                    if source_type == 'rss' and 'xml' not in content_type.lower():
                        result['status'] = 'warning'
                        result['warning'] = f"RSS source but content type is {content_type}"
                    elif source_type == 'api' and 'json' not in content_type.lower():
                        result['status'] = 'warning'
                        result['warning'] = f"API source but content type is {content_type}"
                    else:
                        result['status'] = 'success'
                        
                    # Get content sample for validation
                    content = await response.text(encoding='utf-8', errors='ignore')
                    content_sample = content[:1000] + ('...' if len(content) > 1000 else '')
                    result['content_sample'] = content_sample
                    
                    # Validate content structure
                    if source_type == 'rss':
                        if '<rss' not in content.lower() and '<feed' not in content.lower():
                            result['status'] = 'warning'
                            result['warning'] = "Content doesn't appear to be valid RSS/Atom"
                    elif source_type == 'api':
                        try:
                            json_data = await response.json()
                            result['json_structure'] = self._describe_json_structure(json_data)
                        except:
                            result['status'] = 'warning'
                            result['warning'] = "Content doesn't appear to be valid JSON"
                    
                else:
                    result['status'] = 'error'
                    result['error'] = f"HTTP error {response.status}"
        
        except asyncio.TimeoutError:
            result['status'] = 'error'
            result['error'] = 'Request timed out'
            result['response_time'] = 30.0
        
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def _describe_json_structure(self, data: Any, max_depth: int = 2, current_depth: int = 0) -> Dict[str, Any]:
        """Generate a description of JSON structure for validation"""
        if current_depth >= max_depth:
            return {"type": type(data).__name__, "truncated": True}
        
        if isinstance(data, dict):
            return {
                "type": "object",
                "keys": list(data.keys())[:10] + (["..."] if len(data) > 10 else []),
                "sample": {
                    k: self._describe_json_structure(v, max_depth, current_depth + 1)
                    for k, v in list(data.items())[:3]
                }
            }
        elif isinstance(data, list):
            return {
                "type": "array",
                "length": len(data),
                "sample": [
                    self._describe_json_structure(item, max_depth, current_depth + 1)
                    for item in data[:3]
                ] if data else []
            }
        else:
            return {"type": type(data).__name__}
    
    def generate_report(self, output_file: str = None) -> Dict[str, Any]:
        """Generate a verification report"""
        if not self.results:
            logger.warning("No verification results available")
            return {}
        
        # Compile report statistics
        total = len(self.results)
        success_count = sum(1 for r in self.results.values() if r.get('status') == 'success')
        warning_count = sum(1 for r in self.results.values() if r.get('status') == 'warning')
        error_count = sum(1 for r in self.results.values() if r.get('status') == 'error')
        
        avg_response_time = 0
        response_times = [r.get('response_time', 0) for r in self.results.values() 
                         if r.get('response_time') is not None]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
        
        # Group by type
        by_type = {}
        for name, result in self.results.items():
            source_type = result.get('type', 'unknown')
            if source_type not in by_type:
                by_type[source_type] = {
                    'total': 0,
                    'success': 0,
                    'warning': 0,
                    'error': 0
                }
            
            by_type[source_type]['total'] += 1
            status = result.get('status', 'unknown')
            if status in by_type[source_type]:
                by_type[source_type][status] += 1
        
        # Create report
        report = {
            "report_type": "Intelligence Source Verification",
            "generated_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "summary": {
                "total_sources": total,
                "successful": success_count,
                "warnings": warning_count,
                "errors": error_count,
                "success_rate": round(success_count / total * 100, 1) if total > 0 else 0,
                "average_response_time": round(avg_response_time, 2)
            },
            "by_type": by_type,
            "results": self.results
        }
        
        # Write report to file if specified
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=4)
            logger.info(f"Verification report saved to {output_file}")
        
        return report

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Watchkeeper Intelligence Source Verifier')
    parser.add_argument('--sources', default='config/combined_sources.json', 
                      help='Path to sources configuration file')
    parser.add_argument('--output', default='reports/source_verification.json',
                      help='Output file for verification report')
    args = parser.parse_args()
    
    verifier = SourceVerifier(args.sources)
    
    print(f"Verifying {len(verifier.sources)} intelligence sources...")
    results = await verifier.verify_all_sources()
    
    # Generate and print report summary
    report = verifier.generate_report(args.output)
    summary = report.get('summary', {})
    
    print("\nVerification Results:")
    print(f"Total Sources: {summary.get('total_sources', 0)}")
    print(f"Successful: {summary.get('successful', 0)} ({summary.get('success_rate', 0)}%)")
    print(f"Warnings: {summary.get('warnings', 0)}")
    print(f"Errors: {summary.get('errors', 0)}")
    print(f"Average Response Time: {summary.get('average_response_time', 0)} seconds")
    
    if args.output:
        print(f"\nDetailed report saved to {args.output}")

if __name__ == "__main__":
    asyncio.run(main())
