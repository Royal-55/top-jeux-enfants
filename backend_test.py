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
import base64
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
            'websocket_broadcast': False,
            # New enhanced features
            'geolocation_detection': False,
            'photo_upload_system': False,
            'voting_system': False,
            'statistics_endpoint': False,
            'nearby_alerts': False,
            'enhanced_alert_creation': False
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
    
    def test_geolocation_detection(self):
        """Test POST /api/detect-zone - Geolocation auto-detection"""
        print("\n=== Testing Geolocation Auto-Detection ===")
        try:
            # Test with Abidjan coordinates
            abidjan_coords = {"latitude": 5.36, "longitude": -4.0083}
            response = self.session.post(
                f"{API_BASE_URL}/detect-zone",
                json=abidjan_coords,
                headers={'Content-Type': 'application/json'}
            )
            print(f"Abidjan detection - Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                detected_zone = data.get('zone')
                print(f"Detected zone for Abidjan: {detected_zone}")
                
                # Test with Bouaké coordinates
                bouake_coords = {"latitude": 7.6906, "longitude": -5.03}
                response2 = self.session.post(
                    f"{API_BASE_URL}/detect-zone",
                    json=bouake_coords,
                    headers={'Content-Type': 'application/json'}
                )
                print(f"Bouaké detection - Status Code: {response2.status_code}")
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    detected_zone2 = data2.get('zone')
                    print(f"Detected zone for Bouaké: {detected_zone2}")
                    
                    # Verify correct zone detection
                    if detected_zone == "Abidjan" and detected_zone2 == "Bouaké":
                        self.test_results['geolocation_detection'] = True
                        print("✅ Geolocation auto-detection working correctly")
                        return True
                    else:
                        print(f"❌ Zone detection incorrect. Expected Abidjan/Bouaké, got {detected_zone}/{detected_zone2}")
                else:
                    print(f"❌ Bouaké detection failed: {response2.text}")
            else:
                print(f"❌ Abidjan detection failed: {response.text}")
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
        
        return False
    
    def test_photo_upload_system(self):
        """Test enhanced alert creation with photos"""
        print("\n=== Testing Photo Upload System ===")
        try:
            # Create a small base64 encoded test image (1x1 pixel PNG)
            test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=="
            
            alert_data = {
                "title": "Accident avec photos",
                "description": "Accident grave sur la route d'Aboisso. Photos des dégâts disponibles.",
                "alert_type": "accident",
                "zone": "Abidjan",
                "reporter_name": "Koffi Aya",
                "latitude": 5.36,
                "longitude": -4.0083,
                "photos": [test_image_b64, test_image_b64],  # Two test photos
                "location_accuracy": 10.5
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/alerts",
                json=alert_data,
                headers={'Content-Type': 'application/json'}
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                alert = response.json()
                photos = alert.get('photos', [])
                print(f"Number of photos stored: {len(photos)}")
                print(f"Alert has GPS coordinates: lat={alert.get('latitude')}, lon={alert.get('longitude')}")
                print(f"Location accuracy: {alert.get('location_accuracy')}")
                
                # Verify photos are stored correctly
                if len(photos) == 2 and all(photo == test_image_b64 for photo in photos):
                    self.test_results['photo_upload_system'] = True
                    print("✅ Photo upload system working correctly")
                    return True
                else:
                    print("❌ Photos not stored correctly")
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
        
        return False
    
    def test_voting_system(self):
        """Test community voting and validation system"""
        print("\n=== Testing Voting and Validation System ===")
        try:
            # First create an alert to vote on
            alert_data = {
                "title": "Vol de téléphone confirmé",
                "description": "Téléphone Samsung volé au marché de Cocody",
                "alert_type": "vol",
                "zone": "Abidjan",
                "reporter_name": "Adjoua Marie"
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/alerts",
                json=alert_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                alert = response.json()
                alert_id = alert.get('id')
                print(f"Created alert for voting test: {alert_id}")
                
                # Test voting with different voter IDs
                voters = ["voter_192.168.1.1", "voter_192.168.1.2", "voter_192.168.1.3", "voter_192.168.1.4"]
                
                for i, voter_id in enumerate(voters[:3]):  # First 3 votes
                    vote_data = {"voter_id": voter_id}
                    vote_response = self.session.post(
                        f"{API_BASE_URL}/alerts/{alert_id}/vote",
                        json=vote_data,
                        headers={'Content-Type': 'application/json'}
                    )
                    print(f"Vote {i+1} - Status Code: {vote_response.status_code}")
                    
                    if vote_response.status_code == 200:
                        vote_result = vote_response.json()
                        votes = vote_result.get('votes')
                        verified = vote_result.get('verified')
                        print(f"Votes: {votes}, Verified: {verified}")
                        
                        # After 3 votes, should be verified
                        if i == 2 and verified:
                            print("✅ Auto-verification after 3 votes working")
                
                # Test double voting prevention
                double_vote_data = {"voter_id": voters[0]}  # Same voter as first vote
                double_vote_response = self.session.post(
                    f"{API_BASE_URL}/alerts/{alert_id}/vote",
                    json=double_vote_data,
                    headers={'Content-Type': 'application/json'}
                )
                print(f"Double vote prevention - Status Code: {double_vote_response.status_code}")
                
                if double_vote_response.status_code == 400:
                    print("✅ Double voting prevention working")
                    self.test_results['voting_system'] = True
                    return True
                else:
                    print("❌ Double voting prevention failed")
            else:
                print(f"❌ Failed to create alert for voting test: {response.text}")
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
        
        return False
    
    def test_statistics_endpoint(self):
        """Test GET /api/stats - Statistics and analytics"""
        print("\n=== Testing Statistics and Analytics ===")
        try:
            response = self.session.get(f"{API_BASE_URL}/stats")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                stats = response.json()
                print(f"Statistics received: {json.dumps(stats, indent=2)}")
                
                # Check required fields
                required_fields = ['total_alerts', 'active_alerts', 'verified_alerts', 'types_stats', 'zones_stats']
                if all(field in stats for field in required_fields):
                    print(f"Total alerts: {stats['total_alerts']}")
                    print(f"Active alerts: {stats['active_alerts']}")
                    print(f"Verified alerts: {stats['verified_alerts']}")
                    print(f"Types stats: {stats['types_stats']}")
                    print(f"Top zones: {len(stats['zones_stats'])} zones")
                    
                    self.test_results['statistics_endpoint'] = True
                    print("✅ Statistics endpoint working correctly")
                    return True
                else:
                    print("❌ Missing required statistics fields")
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
        
        return False
    
    def test_nearby_alerts(self):
        """Test GET /api/alerts/nearby - Location-based queries"""
        print("\n=== Testing Nearby Alerts API ===")
        try:
            # First create some alerts with GPS coordinates
            alerts_to_create = [
                {
                    "title": "Accident près d'Abidjan",
                    "description": "Collision sur l'autoroute",
                    "alert_type": "accident",
                    "zone": "Abidjan",
                    "reporter_name": "Jean Kouassi",
                    "latitude": 5.36,
                    "longitude": -4.0083
                },
                {
                    "title": "Vol à Bouaké",
                    "description": "Cambriolage signalé",
                    "alert_type": "vol",
                    "zone": "Bouaké",
                    "reporter_name": "Marie Adjoua",
                    "latitude": 7.6906,
                    "longitude": -5.03
                }
            ]
            
            created_alerts = []
            for alert_data in alerts_to_create:
                response = self.session.post(
                    f"{API_BASE_URL}/alerts",
                    json=alert_data,
                    headers={'Content-Type': 'application/json'}
                )
                if response.status_code == 200:
                    created_alerts.append(response.json())
            
            print(f"Created {len(created_alerts)} alerts with GPS coordinates")
            
            # Test nearby alerts query for Abidjan area
            params = {
                "latitude": 5.36,
                "longitude": -4.0083,
                "radius": 0.1  # Small radius
            }
            
            response = self.session.get(f"{API_BASE_URL}/alerts/nearby", params=params)
            print(f"Nearby alerts query - Status Code: {response.status_code}")
            
            if response.status_code == 200:
                nearby_alerts = response.json()
                print(f"Found {len(nearby_alerts)} nearby alerts")
                
                # Should find at least the Abidjan alert
                abidjan_alerts = [alert for alert in nearby_alerts if alert.get('zone') == 'Abidjan']
                if len(abidjan_alerts) > 0:
                    self.test_results['nearby_alerts'] = True
                    print("✅ Nearby alerts API working correctly")
                    return True
                else:
                    print("❌ No nearby alerts found for Abidjan coordinates")
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
        
        return False
    
    def test_enhanced_alert_creation(self):
        """Test enhanced alert creation with all new fields"""
        print("\n=== Testing Enhanced Alert Creation ===")
        try:
            # Create alert with all enhanced features
            test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=="
            
            enhanced_alert_data = {
                "title": "Catastrophe naturelle - Inondation",
                "description": "Inondation importante dans le quartier de Marcory suite aux fortes pluies. Plusieurs maisons touchées.",
                "alert_type": "catastrophe",
                "zone": "",  # Will be auto-detected
                "reporter_name": "Koffi Adjoua",
                "latitude": 5.36,
                "longitude": -4.0083,
                "photos": [test_image_b64],
                "location_accuracy": 15.2
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/alerts",
                json=enhanced_alert_data,
                headers={'Content-Type': 'application/json'}
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                alert = response.json()
                print(f"Created enhanced alert ID: {alert.get('id')}")
                print(f"Auto-detected zone: {alert.get('zone')}")
                print(f"GPS coordinates: {alert.get('latitude')}, {alert.get('longitude')}")
                print(f"Photos count: {len(alert.get('photos', []))}")
                print(f"Location accuracy: {alert.get('location_accuracy')}")
                print(f"Votes: {alert.get('votes')}")
                print(f"Verified: {alert.get('verified')}")
                
                # Verify all enhanced fields are present and correct
                checks = [
                    alert.get('zone') == 'Abidjan',  # Auto-detected from coordinates
                    alert.get('latitude') == 5.36,
                    alert.get('longitude') == -4.0083,
                    len(alert.get('photos', [])) == 1,
                    alert.get('location_accuracy') == 15.2,
                    alert.get('votes') == 0,
                    alert.get('verified') == False,
                    'voters' in alert
                ]
                
                if all(checks):
                    self.test_results['enhanced_alert_creation'] = True
                    print("✅ Enhanced alert creation working correctly")
                    return True
                else:
                    print("❌ Some enhanced fields not working correctly")
                    print(f"Checks results: {checks}")
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
        
        return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Enhanced Backend API Tests for Community Alerts System")
        print("=" * 70)
        
        # Test basic endpoints
        self.test_zones_endpoint()
        self.test_alert_types_endpoint()
        
        # Test CRUD operations
        self.test_create_alert()
        self.test_get_alerts()
        self.test_get_alert_by_id()
        self.test_update_alert()
        
        # Test enhanced features (HIGH PRIORITY)
        print("\n🌟 Testing Enhanced Features...")
        self.test_geolocation_detection()
        self.test_photo_upload_system()
        self.test_voting_system()
        self.test_statistics_endpoint()
        self.test_nearby_alerts()
        self.test_enhanced_alert_creation()
        
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