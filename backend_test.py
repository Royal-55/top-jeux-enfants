#!/usr/bin/env python3
"""
Backend API Testing for Community Alerts System - Côte d'Ivoire
Tests all CRUD operations, WebSocket functionality, and data endpoints
"""

import requests
import json
import asyncio
import websockets
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://0f09c76e-b0ca-4ff7-84ec-4b669a0c24ee.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"
WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://') + '/ws'

print(f"Testing backend at: {API_BASE_URL}")
print(f"WebSocket URL: {WS_URL}")

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.created_alert_id = None
        self.test_results = {
            'zones_endpoint': False,
            'alert_types_endpoint': False,
            'create_alert': False,
            'get_alerts': False,
            'get_alert_by_id': False,
            'update_alert': False,
            'websocket_connection': False,
            'websocket_broadcast': False
        }
    
    def test_zones_endpoint(self):
        """Test GET /api/zones - Should return 33 zones of Côte d'Ivoire"""
        print("\n=== Testing Zones Endpoint ===")
        try:
            response = self.session.get(f"{API_BASE_URL}/zones")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                zones = data.get('zones', [])
                print(f"Number of zones returned: {len(zones)}")
                
                # Check for key Côte d'Ivoire cities
                expected_zones = ['Abidjan', 'Bouaké', 'Daloa', 'Yamoussoukro']
                found_zones = [zone for zone in expected_zones if zone in zones]
                print(f"Key zones found: {found_zones}")
                
                if len(zones) >= 30 and all(zone in zones for zone in expected_zones):
                    self.test_results['zones_endpoint'] = True
                    print("✅ Zones endpoint working correctly")
                    return True
                else:
                    print("❌ Missing expected zones or insufficient zone count")
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
        
        return False
    
    def test_alert_types_endpoint(self):
        """Test GET /api/alert-types - Should return vol, accident, catastrophe"""
        print("\n=== Testing Alert Types Endpoint ===")
        try:
            response = self.session.get(f"{API_BASE_URL}/alert-types")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                alert_types = data.get('alert_types', [])
                print(f"Alert types returned: {len(alert_types)}")
                
                # Check for expected alert types
                expected_types = ['vol', 'accident', 'catastrophe']
                found_types = [at['id'] for at in alert_types if 'id' in at]
                print(f"Alert type IDs found: {found_types}")
                
                if all(at_id in found_types for at_id in expected_types):
                    self.test_results['alert_types_endpoint'] = True
                    print("✅ Alert types endpoint working correctly")
                    return True
                else:
                    print("❌ Missing expected alert types")
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
        
        return False
    
    def test_create_alert(self):
        """Test POST /api/alerts - Create new alert"""
        print("\n=== Testing Create Alert ===")
        try:
            # Realistic French data for Côte d'Ivoire
            alert_data = {
                "title": "Vol de moto signalé",
                "description": "Une moto Honda rouge a été volée près du marché de Treichville. Le voleur portait un t-shirt blanc.",
                "alert_type": "vol",
                "zone": "Abidjan",
                "reporter_name": "Kouassi Jean-Baptiste"
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/alerts",
                json=alert_data,
                headers={'Content-Type': 'application/json'}
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                alert = response.json()
                self.created_alert_id = alert.get('id')
                print(f"Created alert ID: {self.created_alert_id}")
                print(f"Alert title: {alert.get('title')}")
                print(f"Alert zone: {alert.get('zone')}")
                
                # Verify all fields are present
                required_fields = ['id', 'title', 'description', 'alert_type', 'zone', 'reporter_name', 'timestamp', 'status']
                if all(field in alert for field in required_fields):
                    self.test_results['create_alert'] = True
                    print("✅ Alert creation working correctly")
                    return True
                else:
                    print("❌ Missing required fields in response")
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
        
        return False
    
    def test_get_alerts(self):
        """Test GET /api/alerts - List alerts with filters"""
        print("\n=== Testing Get Alerts ===")
        try:
            # Test without filters
            response = self.session.get(f"{API_BASE_URL}/alerts")
            print(f"Status Code (no filters): {response.status_code}")
            
            if response.status_code == 200:
                alerts = response.json()
                print(f"Number of alerts returned: {len(alerts)}")
                
                # Test with zone filter
                response_zone = self.session.get(f"{API_BASE_URL}/alerts?zone=Abidjan")
                print(f"Status Code (zone filter): {response_zone.status_code}")
                
                # Test with alert_type filter
                response_type = self.session.get(f"{API_BASE_URL}/alerts?alert_type=vol")
                print(f"Status Code (type filter): {response_type.status_code}")
                
                # Test with status filter
                response_status = self.session.get(f"{API_BASE_URL}/alerts?status=active")
                print(f"Status Code (status filter): {response_status.status_code}")
                
                if all(r.status_code == 200 for r in [response_zone, response_type, response_status]):
                    self.test_results['get_alerts'] = True
                    print("✅ Get alerts with filters working correctly")
                    return True
                else:
                    print("❌ Some filter queries failed")
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
        
        return False
    
    def test_get_alert_by_id(self):
        """Test GET /api/alerts/{id} - Get specific alert"""
        print("\n=== Testing Get Alert by ID ===")
        if not self.created_alert_id:
            print("❌ No alert ID available for testing")
            return False
        
        try:
            response = self.session.get(f"{API_BASE_URL}/alerts/{self.created_alert_id}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                alert = response.json()
                print(f"Retrieved alert ID: {alert.get('id')}")
                print(f"Alert title: {alert.get('title')}")
                
                if alert.get('id') == self.created_alert_id:
                    self.test_results['get_alert_by_id'] = True
                    print("✅ Get alert by ID working correctly")
                    return True
                else:
                    print("❌ Retrieved alert ID doesn't match")
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
        
        return False
    
    def test_update_alert(self):
        """Test PUT /api/alerts/{id} - Update alert status"""
        print("\n=== Testing Update Alert ===")
        if not self.created_alert_id:
            print("❌ No alert ID available for testing")
            return False
        
        try:
            update_data = {"status": "resolved"}
            response = self.session.put(
                f"{API_BASE_URL}/alerts/{self.created_alert_id}",
                json=update_data,
                headers={'Content-Type': 'application/json'}
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                alert = response.json()
                print(f"Updated alert status: {alert.get('status')}")
                
                if alert.get('status') == 'resolved':
                    self.test_results['update_alert'] = True
                    print("✅ Update alert working correctly")
                    return True
                else:
                    print("❌ Alert status not updated correctly")
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
        
        return False
    
    async def test_websocket_connection(self):
        """Test WebSocket connection and basic functionality"""
        print("\n=== Testing WebSocket Connection ===")
        try:
            async with websockets.connect(WS_URL) as websocket:
                print("✅ WebSocket connection established")
                self.test_results['websocket_connection'] = True
                
                # Send a test message
                test_message = "Test message from backend tester"
                await websocket.send(test_message)
                print(f"Sent message: {test_message}")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"Received response: {response}")
                    
                    if "Message reçu" in response:
                        print("✅ WebSocket echo functionality working")
                        return True
                    else:
                        print("❌ Unexpected WebSocket response")
                except asyncio.TimeoutError:
                    print("❌ WebSocket response timeout")
                
        except Exception as e:
            print(f"❌ WebSocket connection failed: {str(e)}")
        
        return False
    
    async def test_websocket_broadcast(self):
        """Test WebSocket broadcast when creating alerts"""
        print("\n=== Testing WebSocket Broadcast ===")
        try:
            # Connect to WebSocket
            async with websockets.connect(WS_URL) as websocket:
                print("WebSocket connected for broadcast test")
                
                # Create a new alert via API (should trigger broadcast)
                alert_data = {
                    "title": "Accident de circulation",
                    "description": "Collision entre deux véhicules sur l'autoroute du Nord près de Bouaké",
                    "alert_type": "accident",
                    "zone": "Bouaké",
                    "reporter_name": "Marie Adjoua"
                }
                
                # Start listening for WebSocket messages
                listen_task = asyncio.create_task(websocket.recv())
                
                # Create alert via HTTP API
                response = requests.post(
                    f"{API_BASE_URL}/alerts",
                    json=alert_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    print("Alert created successfully via API")
                    
                    # Wait for WebSocket broadcast
                    try:
                        broadcast_message = await asyncio.wait_for(listen_task, timeout=10.0)
                        print(f"Received broadcast: {broadcast_message[:100]}...")
                        
                        # Parse the broadcast message
                        try:
                            broadcast_data = json.loads(broadcast_message)
                            if broadcast_data.get('type') == 'new_alert':
                                self.test_results['websocket_broadcast'] = True
                                print("✅ WebSocket broadcast working correctly")
                                return True
                            else:
                                print("❌ Broadcast message type incorrect")
                        except json.JSONDecodeError:
                            print("❌ Broadcast message not valid JSON")
                    
                    except asyncio.TimeoutError:
                        print("❌ No broadcast received within timeout")
                else:
                    print(f"❌ Failed to create alert for broadcast test: {response.status_code}")
                
        except Exception as e:
            print(f"❌ WebSocket broadcast test failed: {str(e)}")
        
        return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests for Community Alerts System")
        print("=" * 60)
        
        # Test basic endpoints
        self.test_zones_endpoint()
        self.test_alert_types_endpoint()
        
        # Test CRUD operations
        self.test_create_alert()
        self.test_get_alerts()
        self.test_get_alert_by_id()
        self.test_update_alert()
        
        # Test WebSocket functionality
        print("\n🔌 Testing WebSocket functionality...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.test_websocket_connection())
            loop.run_until_complete(self.test_websocket_broadcast())
        finally:
            loop.close()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All backend tests PASSED!")
        else:
            print("⚠️  Some backend tests FAILED!")
        
        return passed == total

if __name__ == "__main__":
    tester = BackendTester()
    tester.run_all_tests()