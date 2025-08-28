#!/usr/bin/env python3
"""
Test script for the Hotel Receptionist Chat Agent

This script tests the basic functionality of the chat service without requiring
the full application to be running.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_chat_service():
    """Test the chat service functionality"""
    try:
        print("🧪 Testing Hotel Receptionist Chat Service...")
        print("=" * 50)
        
        # Test 1: Service initialization
        print("1. Testing service initialization...")
        from app.services.simple_chat_service import SimpleChatService
        
        chat_service = SimpleChatService()
        print(f"   ✅ Chat service created successfully")
        
        # Test 2: Session creation
        print("2. Testing session creation...")
        session_id = chat_service.create_chat_session(guest_id=123)
        print(f"   ✅ Session created: {session_id}")
        
        # Test 3: Available tools
        print("3. Testing available tools...")
        tools = await chat_service.get_available_tools()
        print(f"   ✅ Found {len(tools)} available tools")
        
        # Test 4: Basic message processing (mock database)
        print("4. Testing message processing...")
        class MockDB:
            pass
        
        mock_db = MockDB()
        response = await chat_service.process_user_message(
            session_id, 
            "Hello, I'd like to book a room", 
            mock_db
        )
        
        if response and not response.startswith("I apologize"):
            print(f"   ✅ Message processed successfully")
            print(f"   📝 Response: {response[:100]}...")
        else:
            print(f"   ⚠️ Message processed but got error response: {response}")
        
        print("=" * 50)
        print("🎉 Chat service test completed!")
        
        # Check for potential issues
        if not chat_service.gemini_service:
            print("\n⚠️  WARNING: Gemini service not available!")
            print("   Make sure you have set GEMINI_API_KEY in your .env file")
        
        if not chat_service.agent_tools_service:
            print("\n⚠️  WARNING: Agent tools service not available!")
        
        print("\n💡 Next steps:")
        print("1. If you see warnings above, fix the configuration issues")
        print("2. Start the application: python start.py")
        print("3. Test the streaming chat at: http://localhost:8000/docs")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you have installed all dependencies: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_service()) 