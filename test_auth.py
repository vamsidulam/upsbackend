#!/usr/bin/env python3
"""
Test script for authentication endpoints
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:10000/api"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"
TEST_FIRST_NAME = "Test"
TEST_LAST_NAME = "User"

def test_signup():
    """Test user signup"""
    print("Testing signup...")
    
    signup_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "first_name": TEST_FIRST_NAME,
        "last_name": TEST_LAST_NAME
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
        print(f"Signup status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"User created: {user_data['email']}")
            return True
        else:
            print(f"Signup failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Signup error: {e}")
        return False

def test_signin():
    """Test user signin"""
    print("\nTesting signin...")
    
    signin_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/signin", json=signin_data)
        print(f"Signin status: {response.status_code}")
        
        if response.status_code == 200:
            auth_data = response.json()
            print(f"Access token received: {auth_data['access_token'][:20]}...")
            return auth_data['access_token']
        else:
            print(f"Signin failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"Signin error: {e}")
        return None

def test_get_user_info(token):
    """Test getting user info with token"""
    print("\nTesting get user info...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"Get user info status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"User info: {user_data['email']} - {user_data.get('first_name', '')} {user_data.get('last_name', '')}")
            return True
        else:
            print(f"Get user info failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Get user info error: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Authentication System Test ===\n")
    
    # Test signup
    signup_success = test_signup()
    
    # Test signin
    token = test_signin()
    
    if token:
        # Test get user info
        test_get_user_info(token)
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
