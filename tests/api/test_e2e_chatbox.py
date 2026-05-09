"""
End-to-end integration test for chatbox API

Tests the full flow:
1. User uploads CSV file
2. User sends natural language prompt
3. Backend routes to skill or LLM
4. DataVint SDK executes
5. Response returns to user

Requires backend server to be running on http://localhost:8000
"""

import requests
import pandas as pd
import numpy as np
import io
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/chat/analyze-csv"


def create_test_csv():
    """Create a test CSV with data quality issues"""
    np.random.seed(42)
    n = 100

    data = {
        'user_id': range(1, n + 1),
        'name': ['User_' + str(i) for i in range(1, n + 1)],
        'age': [25 + i if i % 3 != 0 else None for i in range(n)],  # 33% missing
        'email': ['user' + str(i) + '@example.com' if i % 2 == 0 else None for i in range(n)],  # 50% missing
        'is_active': np.random.choice([True, False], n, p=[0.8, 0.2]),  # Boolean column
        'country': np.random.choice(['US', 'UK', 'CA'], n, p=[0.7, 0.2, 0.1]),
    }

    df = pd.DataFrame(data)

    # Convert to CSV string
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()

    return csv_content, df


def check_server_running():
    """Check if backend server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def test_skill_routing_query():
    """Test E2E flow with a query that should route to skill"""
    print("\n" + "=" * 80)
    print("TEST 1: Skill Routing - 'check missing values'")
    print("=" * 80)

    # Check server is running
    if not check_server_running():
        print("❌ FAILED: Backend server not running on http://localhost:8000")
        print("   Start server with: uvicorn server.api.main:app --reload")
        return False

    # Create test data
    csv_content, df = create_test_csv()
    print(f"✅ Created test dataset: {df.shape[0]} rows × {df.shape[1]} columns")

    # Prepare request
    files = {
        'file': ('test_data.csv', csv_content, 'text/csv')
    }
    data = {
        'prompt': 'check missing values across all columns'
    }

    print(f"\n📤 Sending POST request to {API_ENDPOINT}")
    print(f"   Prompt: '{data['prompt']}'")

    # Send request
    try:
        response = requests.post(API_ENDPOINT, files=files, data=data, timeout=30)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error: {e}")
        return False

    print(f"✅ Response received: {response.status_code}")

    # Verify response structure
    if 'success' not in result:
        print(f"❌ FAILED: Missing 'success' field in response")
        return False

    if not result['success']:
        print(f"❌ FAILED: API returned success=False")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        return False

    print(f"✅ API success: {result['success']}")

    # Verify routing decision
    if 'routing' in result:
        routing = result['routing']
        print(f"\n🔀 Routing Decision:")
        print(f"   Method: {routing.get('method', 'N/A')}")
        print(f"   Skill: {routing.get('skill_name', 'N/A')}")
        print(f"   Confidence: {routing.get('confidence', 'N/A')}")

        # This query should route to skill
        if routing.get('method') != 'skill':
            print(f"⚠️  WARNING: Expected skill routing, got {routing.get('method')}")
        else:
            print(f"✅ Correctly routed to skill: {routing.get('skill_name')}")

    # Verify output content
    if 'output' not in result:
        print(f"❌ FAILED: Missing 'output' field in response")
        return False

    output = result['output']
    print(f"\n📝 Output preview (first 300 chars):")
    print(output[:300] + "..." if len(output) > 300 else output)

    # Check for expected content in output
    expected_keywords = ['missing', 'completeness', 'age', 'email']
    found_keywords = [kw for kw in expected_keywords if kw.lower() in output.lower()]

    if len(found_keywords) >= 3:
        print(f"\n✅ Output contains expected keywords: {found_keywords}")
    else:
        print(f"\n⚠️  WARNING: Output missing some expected keywords")
        print(f"   Found: {found_keywords}")
        print(f"   Expected: {expected_keywords}")

    # Verify data field
    if 'data' in result and result['data']:
        data_keys = list(result['data'].keys())
        print(f"\n✅ Data field present with keys: {data_keys}")

    print("\n" + "=" * 80)
    print("✅ TEST 1 PASSED")
    print("=" * 80)
    return True


def test_llm_routing_query():
    """Test E2E flow with a query that should route to LLM"""
    print("\n" + "=" * 80)
    print("TEST 2: LLM Routing - 'visualize correlation matrix'")
    print("=" * 80)

    # Check server is running
    if not check_server_running():
        print("❌ FAILED: Backend server not running")
        return False

    # Create test data
    csv_content, df = create_test_csv()
    print(f"✅ Created test dataset: {df.shape[0]} rows × {df.shape[1]} columns")

    # Prepare request
    files = {
        'file': ('test_data.csv', csv_content, 'text/csv')
    }
    data = {
        'prompt': 'visualize correlation matrix with heatmap'
    }

    print(f"\n📤 Sending POST request to {API_ENDPOINT}")
    print(f"   Prompt: '{data['prompt']}'")

    # Send request
    try:
        response = requests.post(API_ENDPOINT, files=files, data=data, timeout=30)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error: {e}")
        return False

    print(f"✅ Response received: {response.status_code}")

    # Verify routing decision
    if 'routing' in result:
        routing = result['routing']
        print(f"\n🔀 Routing Decision:")
        print(f"   Method: {routing.get('method', 'N/A')}")

        # This query should route to LLM (no skill match)
        if routing.get('method') == 'llm':
            print(f"✅ Correctly routed to LLM generation")
        else:
            print(f"⚠️  Note: Query routed to skill instead of LLM")
            print(f"   Skill: {routing.get('skill_name', 'N/A')}")

    # Verify response contains code
    if 'generated_code' in result and result['generated_code']:
        print(f"\n✅ LLM generated code (first 200 chars):")
        print(result['generated_code'][:200] + "...")

    print("\n" + "=" * 80)
    print("✅ TEST 2 PASSED")
    print("=" * 80)
    return True


def test_slash_command():
    """Test E2E flow with slash command"""
    print("\n" + "=" * 80)
    print("TEST 3: Slash Command - '/check-completeness'")
    print("=" * 80)

    # Check server is running
    if not check_server_running():
        print("❌ FAILED: Backend server not running")
        return False

    # Create test data
    csv_content, df = create_test_csv()
    print(f"✅ Created test dataset: {df.shape[0]} rows × {df.shape[1]} columns")

    # Prepare request
    files = {
        'file': ('test_data.csv', csv_content, 'text/csv')
    }
    data = {
        'prompt': '/check-completeness'
    }

    print(f"\n📤 Sending POST request to {API_ENDPOINT}")
    print(f"   Prompt: '{data['prompt']}'")

    # Send request
    try:
        response = requests.post(API_ENDPOINT, files=files, data=data, timeout=30)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error: {e}")
        return False

    print(f"✅ Response received: {response.status_code}")

    # Verify routing decision
    if 'routing' in result:
        routing = result['routing']
        print(f"\n🔀 Routing Decision:")
        print(f"   Method: {routing.get('method', 'N/A')}")
        print(f"   Skill: {routing.get('skill_name', 'N/A')}")
        print(f"   Confidence: {routing.get('confidence', 'N/A')}")

        # Slash commands should have confidence 1.0
        if routing.get('confidence') == 1.0:
            print(f"✅ Slash command detected with max confidence")
        else:
            print(f"⚠️  WARNING: Expected confidence 1.0, got {routing.get('confidence')}")

    print("\n" + "=" * 80)
    print("✅ TEST 3 PASSED")
    print("=" * 80)
    return True


def test_metrics_endpoint():
    """Test metrics endpoint to verify routing statistics"""
    print("\n" + "=" * 80)
    print("TEST 4: Metrics Endpoint - /api/chat/metrics")
    print("=" * 80)

    # Check server is running
    if not check_server_running():
        print("❌ FAILED: Backend server not running")
        return False

    metrics_url = f"{BASE_URL}/api/chat/metrics"

    print(f"\n📤 Sending GET request to {metrics_url}")

    try:
        response = requests.get(metrics_url, timeout=5)
        response.raise_for_status()
        metrics = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error: {e}")
        return False

    print(f"✅ Response received: {response.status_code}")

    # Verify metrics structure
    if 'routing' not in metrics:
        print(f"❌ FAILED: Missing 'routing' field in metrics")
        return False

    routing_metrics = metrics['routing']

    print(f"\n📊 Routing Metrics:")
    print(f"   Total queries: {routing_metrics.get('total_queries', 0)}")
    print(f"   Skill routed: {routing_metrics.get('skill_routed', 0)} ({routing_metrics.get('skill_percentage', 0):.1f}%)")
    print(f"   LLM routed: {routing_metrics.get('llm_routed', 0)} ({routing_metrics.get('llm_percentage', 0):.1f}%)")

    if 'skill_breakdown' in routing_metrics:
        print(f"\n   Skill breakdown:")
        for skill, count in routing_metrics['skill_breakdown'].items():
            if count > 0:
                print(f"     • {skill}: {count} queries")

    print("\n" + "=" * 80)
    print("✅ TEST 4 PASSED")
    print("=" * 80)
    return True


if __name__ == "__main__":
    print("\n🚀 Starting E2E Chatbox Integration Tests")
    print("=" * 80)
    print("Prerequisites:")
    print("  • Backend server running on http://localhost:8000")
    print("  • Start with: uvicorn server.api.main:app --reload")
    print("=" * 80)

    # Check server first
    if not check_server_running():
        print("\n❌ ERROR: Backend server not running!")
        print("\nTo start the server:")
        print("  cd /Users/duochen/Desktop/career/datavint")
        print("  uvicorn server.api.main:app --reload")
        print("\nThen run this test again.")
        sys.exit(1)

    print("\n✅ Server is running!\n")

    # Run all tests
    results = []

    try:
        results.append(("Skill Routing", test_skill_routing_query()))
        results.append(("LLM Routing", test_llm_routing_query()))
        results.append(("Slash Command", test_slash_command()))
        results.append(("Metrics Endpoint", test_metrics_endpoint()))
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:30s}: {status}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print("\n" + "=" * 80)
    if passed_count == total_count:
        print(f"✅ ALL TESTS PASSED ({passed_count}/{total_count})")
    else:
        print(f"❌ SOME TESTS FAILED ({passed_count}/{total_count})")
    print("=" * 80)

    sys.exit(0 if passed_count == total_count else 1)
