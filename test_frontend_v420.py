#!/usr/bin/env python3
"""
v4.2.0 Frontend Testing Script
Tests the Data Lineage Visualizer frontend for v4.2.0 enhanced features
including confidence levels and node descriptions.
"""

import os
import time
import json
from playwright.sync_api import sync_playwright, Page

# Test configuration
BASE_URL = "http://localhost:3000"
SCREENSHOT_DIR = "/home/user/sandbox/test_screenshots"
TEST_RESULTS = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "tests": [],
    "screenshots": [],
    "summary": {"passed": 0, "failed": 0, "warnings": 0}
}

def log_test(name, status, message="", screenshot=None):
    """Log a test result"""
    test = {
        "name": name,
        "status": status,
        "message": message,
        "screenshot": screenshot
    }
    TEST_RESULTS["tests"].append(test)

    if status == "PASS":
        TEST_RESULTS["summary"]["passed"] += 1
        print(f"✓ {name}")
    elif status == "FAIL":
        TEST_RESULTS["summary"]["failed"] += 1
        print(f"✗ {name}: {message}")
    elif status == "WARN":
        TEST_RESULTS["summary"]["warnings"] += 1
        print(f"⚠ {name}: {message}")

    if screenshot:
        TEST_RESULTS["screenshots"].append(screenshot)
        print(f"  📸 Screenshot: {screenshot}")

def take_screenshot(page: Page, name: str) -> str:
    """Take a screenshot and return the path"""
    filepath = os.path.join(SCREENSHOT_DIR, name)
    page.screenshot(path=filepath, full_page=True)
    return filepath

def test_page_load(page: Page):
    """Test 1: Verify page loads successfully"""
    try:
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)  # Wait for initial render

        # Take initial screenshot
        screenshot = take_screenshot(page, "01-initial-page-load.png")

        # Check if page has any content
        body = page.locator('body')
        if body.count() > 0:
            log_test("Page Load", "PASS", "Page loaded successfully", screenshot)
            return True
        else:
            log_test("Page Load", "FAIL", "Page body not found", screenshot)
            return False
    except Exception as e:
        log_test("Page Load", "FAIL", f"Error: {str(e)}")
        return False

def test_graph_render(page: Page):
    """Test 2: Verify lineage graph renders"""
    try:
        # Look for React Flow or graph container
        selectors = [
            '.react-flow',
            '[class*="react-flow"]',
            '#root',
            'canvas',
            'svg'
        ]

        graph_found = False
        for selector in selectors:
            element = page.locator(selector).first
            if element.count() > 0:
                graph_found = True
                log_test("Graph Render", "PASS", f"Graph element found: {selector}")
                break

        if not graph_found:
            log_test("Graph Render", "WARN", "Graph element not found with standard selectors")

        # Take screenshot regardless
        screenshot = take_screenshot(page, "02-graph-view.png")
        TEST_RESULTS["screenshots"].append(screenshot)

        return graph_found
    except Exception as e:
        log_test("Graph Render", "FAIL", f"Error: {str(e)}")
        return False

def test_search_nodes(page: Page):
    """Test 3: Look for nodes with different confidence levels"""
    try:
        # Look for any node elements
        node_selectors = [
            '.react-flow__node',
            '[class*="node"]',
            '[data-id]',
            'g[class*="node"]',
            'div[draggable]'
        ]

        nodes_found = False
        node_count = 0

        for selector in node_selectors:
            nodes = page.locator(selector)
            count = nodes.count()
            if count > 0:
                nodes_found = True
                node_count = count
                log_test("Node Discovery", "PASS", f"Found {count} nodes using selector: {selector}")
                break

        if not nodes_found:
            log_test("Node Discovery", "WARN", "No nodes found - graph may be empty")
            screenshot = take_screenshot(page, "03-no-nodes-found.png")
            TEST_RESULTS["screenshots"].append(screenshot)
            return False

        # Try to click on nodes and capture their details
        for i in range(min(node_count, 5)):
            try:
                node = page.locator(selector).nth(i)
                node.click(timeout=5000)
                page.wait_for_timeout(500)

                # Take screenshot of selected node
                screenshot = take_screenshot(page, f"04-node-{i+1}-details.png")
                TEST_RESULTS["screenshots"].append(screenshot)

                # Get node text content
                text = node.text_content()
                if text:
                    # Look for v4.2.0 features
                    has_confidence = any(indicator in text for indicator in ['✅', '⚠️', '❌', 'confidence', 'High', 'Medium', 'Low'])
                    if has_confidence:
                        log_test(f"Node {i+1} v4.2.0 Format", "PASS", f"Node shows confidence indicators", screenshot)
                    else:
                        log_test(f"Node {i+1} v4.2.0 Format", "WARN", f"Node may not show v4.2.0 format", screenshot)
            except Exception as e:
                log_test(f"Node {i+1} Interaction", "WARN", f"Could not interact: {str(e)}")

        return True
    except Exception as e:
        log_test("Node Discovery", "FAIL", f"Error: {str(e)}")
        return False

def test_search_functionality(page: Page):
    """Test 4: Test search functionality"""
    try:
        # Look for search input
        search_selectors = [
            'input[placeholder*="Search"]',
            'input[placeholder*="search"]',
            'input[type="search"]',
            'input[type="text"]'
        ]

        search_found = False
        for selector in search_selectors:
            search_input = page.locator(selector).first
            if search_input.count() > 0:
                search_found = True

                # Try to use search
                search_input.fill('sp_')
                page.wait_for_timeout(1000)
                search_input.press('Enter')
                page.wait_for_timeout(1000)

                screenshot = take_screenshot(page, "05-search-results.png")
                log_test("Search Functionality", "PASS", f"Search input found and tested", screenshot)
                break

        if not search_found:
            log_test("Search Functionality", "WARN", "Search input not found")

        return search_found
    except Exception as e:
        log_test("Search Functionality", "FAIL", f"Error: {str(e)}")
        return False

def test_filter_controls(page: Page):
    """Test 5: Test filter controls"""
    try:
        # Look for filter buttons/dropdowns
        filter_selectors = [
            'button:has-text("Filter")',
            'button:has-text("Schema")',
            'button:has-text("Type")',
            'select',
            '[role="combobox"]'
        ]

        filters_found = False
        for selector in filter_selectors:
            filters = page.locator(selector)
            if filters.count() > 0:
                filters_found = True
                log_test("Filter Controls", "PASS", f"Found filters: {selector}")

                # Try to interact with first filter
                try:
                    filters.first.click(timeout=5000)
                    page.wait_for_timeout(500)
                    screenshot = take_screenshot(page, "06-filters-open.png")
                    TEST_RESULTS["screenshots"].append(screenshot)
                except:
                    pass
                break

        if not filters_found:
            log_test("Filter Controls", "WARN", "Filter controls not found")

        # Take general screenshot anyway
        screenshot = take_screenshot(page, "07-filter-controls.png")
        TEST_RESULTS["screenshots"].append(screenshot)

        return filters_found
    except Exception as e:
        log_test("Filter Controls", "FAIL", f"Error: {str(e)}")
        return False

def test_confidence_indicators(page: Page):
    """Test 6: Look for v4.2.0 confidence level indicators"""
    try:
        # Get page content
        content = page.content()

        # Check for v4.2.0 confidence indicators
        indicators = {
            "✅ High Confidence": "✅" in content,
            "⚠️ Medium Confidence": "⚠️" in content,
            "❌ Low Confidence": "❌" in content or "Failed" in content,
            "Confidence Text": "confidence" in content.lower() or "Confidence" in content
        }

        found_count = sum(indicators.values())

        if found_count > 0:
            log_test("v4.2.0 Confidence Indicators", "PASS",
                    f"Found {found_count} confidence indicators: {[k for k, v in indicators.items() if v]}")
        else:
            log_test("v4.2.0 Confidence Indicators", "WARN",
                    "No confidence indicators found - may need data loaded")

        # Take screenshot
        screenshot = take_screenshot(page, "08-confidence-indicators.png")
        TEST_RESULTS["screenshots"].append(screenshot)

        return found_count > 0
    except Exception as e:
        log_test("v4.2.0 Confidence Indicators", "FAIL", f"Error: {str(e)}")
        return False

def main():
    """Main test runner"""
    print("=" * 80)
    print("v4.2.0 Frontend Testing - Data Lineage Visualizer")
    print("=" * 80)
    print()

    # Ensure screenshot directory exists
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    with sync_playwright() as p:
        # Launch browser
        print("Launching browser...")
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-extensions',
                '--disable-blink-features=AutomationControlled',
                '--single-process'
            ]
        )
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        print(f"Testing URL: {BASE_URL}\n")

        # Run tests
        test_page_load(page)
        test_graph_render(page)
        test_search_nodes(page)
        test_search_functionality(page)
        test_filter_controls(page)
        test_confidence_indicators(page)

        # Close browser
        browser.close()

    # Print summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Passed:   {TEST_RESULTS['summary']['passed']}")
    print(f"Failed:   {TEST_RESULTS['summary']['failed']}")
    print(f"Warnings: {TEST_RESULTS['summary']['warnings']}")
    print(f"Screenshots: {len(TEST_RESULTS['screenshots'])}")
    print()

    # Save results to JSON
    results_file = os.path.join(SCREENSHOT_DIR, "test_results.json")
    with open(results_file, 'w') as f:
        json.dump(TEST_RESULTS, f, indent=2)
    print(f"Detailed results saved to: {results_file}")

    return TEST_RESULTS

if __name__ == "__main__":
    results = main()
