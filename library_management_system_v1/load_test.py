"""
Load Testing Script for Library Management System
Tests current performance limits before optimization
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime
from typing import List, Dict
import uuid


class LoadTestResults:
    def __init__(self):
        self.response_times = []
        self.success_count = 0
        self.error_count = 0
        self.errors = []

    def add_result(self, response_time: float, success: bool, error: str = None):
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            if error:
                self.errors.append(error)

    def get_stats(self) -> dict:
        if not self.response_times:
            return {"error": "No data collected"}

        sorted_times = sorted(self.response_times)
        total_requests = self.success_count + self.error_count

        return {
            "total_requests": total_requests,
            "successful_requests": self.success_count,
            "failed_requests": self.error_count,
            "success_rate": (self.success_count / total_requests) * 100 if total_requests > 0 else 0,
            "avg_response_time": statistics.mean(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "p95_response_time": sorted_times[int(0.95 * len(sorted_times))] if sorted_times else 0,
            "p99_response_time": sorted_times[int(0.99 * len(sorted_times))] if sorted_times else 0,
            "requests_per_second": total_requests / max(max(self.response_times), 1),
            "errors": self.errors[:10]  # First 10 errors for analysis
        }


class LibraryLoadTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=100)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def make_request(self, method: str, endpoint: str, data: dict = None) -> tuple[float, bool, str]:
        """Make HTTP request and return (response_time, success, error_message)"""
        start_time = time.time()
        try:
            if method.upper() == "GET":
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    await response.text()  # Read response body
                    response_time = time.time() - start_time
                    return response_time, response.status < 400, None
            elif method.upper() == "POST":
                async with self.session.post(f"{self.base_url}{endpoint}", json=data) as response:
                    await response.text()
                    response_time = time.time() - start_time
                    return response_time, response.status < 400, None
        except Exception as e:
            response_time = time.time() - start_time
            return response_time, False, str(e)

    async def health_check_test(self, concurrent_users: int = 10, duration: int = 30):
        """Test health endpoint under load"""
        print(f"\n🏥 Testing Health Endpoint: {concurrent_users} concurrent users for {duration}s")

        results = LoadTestResults()
        end_time = time.time() + duration

        async def user_simulation():
            while time.time() < end_time:
                response_time, success, error = await self.make_request("GET", "/health")
                results.add_result(response_time, success, error)
                await asyncio.sleep(0.1)  # 10 requests per second per user

        # Run concurrent users
        tasks = [user_simulation() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks)

        return results.get_stats()

    async def api_endpoint_test(self, concurrent_users: int = 5, duration: int = 20):
        """Test main API endpoints"""
        print(f"\n📚 Testing API Endpoints: {concurrent_users} concurrent users for {duration}s")

        results = LoadTestResults()
        end_time = time.time() + duration

        async def realistic_user_journey():
            """Simulate realistic user behavior"""
            while time.time() < end_time:
                try:
                    # 1. Check root endpoint
                    response_time, success, error = await self.make_request("GET", "/")
                    results.add_result(response_time, success, error)

                    # 2. Register member (might fail if already exists - that's OK)
                    member_data = {
                        "name": f"Test User {uuid.uuid4().hex[:8]}",
                        "email": f"test{uuid.uuid4().hex[:8]}@example.com",
                        "member_type": "REGULAR"
                    }
                    response_time, success, error = await self.make_request("POST", "/api/members", member_data)
                    results.add_result(response_time, success, error)

                    # 3. Add book (might fail if already exists - that's OK)
                    book_data = {
                        "title": f"Test Book {uuid.uuid4().hex[:8]}",
                        "author": "Test Author",
                        "isbn": f"978{uuid.uuid4().hex[:10]}",
                        "genre": "Testing"
                    }
                    response_time, success, error = await self.make_request("POST", "/api/books", book_data)
                    results.add_result(response_time, success, error)

                    # 4. Search books
                    response_time, success, error = await self.make_request("GET", "/api/books?title=Test")
                    results.add_result(response_time, success, error)

                    await asyncio.sleep(1)  # Realistic user pause

                except Exception as e:
                    results.add_result(5.0, False, str(e))

        # Run concurrent users
        tasks = [realistic_user_journey() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks)

        return results.get_stats()

    async def stress_test(self, max_users: int = 50):
        """Gradually increase load to find breaking point"""
        print(f"\n💪 Stress Test: Finding breaking point up to {max_users} users")

        breaking_points = []

        for users in [1, 5, 10, 20, 30, 40, 50]:
            if users > max_users:
                break

            print(f"\n  Testing with {users} concurrent users...")
            stats = await self.health_check_test(concurrent_users=users, duration=10)

            breaking_points.append({
                "concurrent_users": users,
                "success_rate": stats.get("success_rate", 0),
                "avg_response_time": stats.get("avg_response_time", 0),
                "p95_response_time": stats.get("p95_response_time", 0),
                "requests_per_second": stats.get("requests_per_second", 0)
            })

            # Stop if we hit severe degradation
            if stats.get("success_rate", 0) < 50 or stats.get("avg_response_time", 0) > 5:
                print(f"  ⚠️ Severe degradation detected at {users} users")
                break

        return breaking_points


async def run_comprehensive_load_test():
    """Run complete load testing suite"""

    print("🚀 Library Management System - Load Testing Suite")
    print("=" * 60)
    print("📋 Testing current system performance before optimization")
    print("🎯 Goal: Find bottlenecks and establish baseline metrics")

    async with LibraryLoadTester() as tester:
        # Test 1: Basic health check
        print("\n" + "="*60)
        print("TEST 1: HEALTH CHECK PERFORMANCE")
        health_stats = await tester.health_check_test(concurrent_users=10, duration=15)
        print(f"✅ Health Check Results:")
        print(f"   Success Rate: {health_stats['success_rate']:.1f}%")
        print(f"   Avg Response: {health_stats['avg_response_time']:.3f}s")
        print(f"   P95 Response: {health_stats['p95_response_time']:.3f}s")
        print(f"   RPS: {health_stats['requests_per_second']:.1f}")

        # Test 2: API endpoints
        print("\n" + "="*60)
        print("TEST 2: API ENDPOINT PERFORMANCE")
        api_stats = await tester.api_endpoint_test(concurrent_users=3, duration=15)
        print(f"✅ API Endpoint Results:")
        print(f"   Success Rate: {api_stats['success_rate']:.1f}%")
        print(f"   Avg Response: {api_stats['avg_response_time']:.3f}s")
        print(f"   P95 Response: {api_stats['p95_response_time']:.3f}s")
        print(f"   RPS: {api_stats['requests_per_second']:.1f}")
        if api_stats['errors']:
            print(f"   Sample Errors: {api_stats['errors'][:3]}")

        # Test 3: Stress test
        print("\n" + "="*60)
        print("TEST 3: STRESS TEST - FINDING BREAKING POINT")
        stress_results = await tester.stress_test(max_users=30)

        print("\n📊 Stress Test Results:")
        print("Users | Success% | Avg(ms) | P95(ms) | RPS")
        print("-" * 45)
        for result in stress_results:
            print(f"{result['concurrent_users']:5} | "
                  f"{result['success_rate']:7.1f}% | "
                  f"{result['avg_response_time']*1000:7.0f} | "
                  f"{result['p95_response_time']*1000:7.0f} | "
                  f"{result['requests_per_second']:5.1f}")

    # Analysis
    print("\n" + "="*60)
    print("📋 BASELINE PERFORMANCE ANALYSIS")
    print("="*60)

    if stress_results:
        best_result = max(stress_results, key=lambda x: x['success_rate'])
        print(f"🎯 Current System Limits:")
        print(f"   Max Stable Users: ~{best_result['concurrent_users']} concurrent")
        print(f"   Max RPS: ~{best_result['requests_per_second']:.1f}")
        print(f"   Response Time: ~{best_result['avg_response_time']*1000:.0f}ms average")

        # Estimate yearly capacity
        daily_requests = best_result['requests_per_second'] * 86400  # seconds in day
        yearly_requests = daily_requests * 365
        print(f"   Daily Capacity: ~{daily_requests:,.0f} requests")
        print(f"   Yearly Capacity: ~{yearly_requests:,.0f} requests")

        # User estimation (assuming 100 requests per user per day)
        daily_users = daily_requests / 100
        print(f"   Max Daily Active Users: ~{daily_users:,.0f}")

    print(f"\n🔧 OPTIMIZATION TARGETS:")
    print(f"   🎯 Target: 10,000+ concurrent users")
    print(f"   🎯 Target: <100ms average response time")
    print(f"   🎯 Target: 99.9% uptime")
    print(f"   🎯 Target: 1M+ daily active users")

    print(f"\n📈 NEXT STEPS:")
    print(f"   1. Implement PostgreSQL (remove memory bottleneck)")
    print(f"   2. Add Redis caching (faster reads)")
    print(f"   3. Make everything async (better concurrency)")
    print(f"   4. Add load balancing (horizontal scaling)")
    print(f"   5. Re-test and measure improvements")


if __name__ == "__main__":
    print("🧪 Starting Load Test...")
    print("⚠️  Make sure your API server is running on localhost:8001")
    print("💡 Start server with: source venv/bin/activate && uvicorn src.api.main:app --host 0.0.0.0 --port 8001")

    try:
        asyncio.run(run_comprehensive_load_test())
    except KeyboardInterrupt:
        print("\n⏹️ Load test interrupted by user")
    except Exception as e:
        print(f"\n❌ Load test failed: {e}")
        print("🔍 Make sure your API server is running!")