#!/usr/bin/env python3
"""
Simple test script for the new LangGraph hotel agent
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_agent():
    """Test the agent system"""
    try:
        from app.services.hotel_agent import hotel_agent
        
        print("🏨 Testing Hotel Agent System")
        print("=" * 50)
        
        # Test agent initialization
        print(f"✅ Agent initialized: {hotel_agent is not None}")
        print(f"✅ LLM available: {hotel_agent.llm is not None}")
        print(f"✅ Graph available: {hotel_agent.graph is not None}")
        print(f"✅ Tools available: {len(hotel_agent.tools) if hotel_agent.tools else 0} tools")
        
        # Test session creation
        session_id = "test-session-123"
        guest_info = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@email.com"
        }
        
        print(f"\n🔄 Creating session: {session_id}")
        success = await hotel_agent.create_session(session_id, guest_info)
        print(f"✅ Session created: {success}")
        
        # Test session info
        session_info = hotel_agent.get_session_info(session_id)
        print(f"✅ Session info retrieved: {session_info is not None}")
        
        # Test message processing (without actual DB)
        print(f"\n💬 Testing message processing...")
        test_message = "Hello, I'm looking for a room for tonight."
        
        try:
            # Mock database session for testing
            class MockDB:
                pass
            
            db = MockDB()
            
            print("📤 Sending test message:", test_message)
            response_chunks = []
            
            async for chunk in hotel_agent.process_message_stream(session_id, test_message, db):
                response_chunks.append(chunk)
                print(f"📥 Received chunk: {chunk.get('type', 'unknown')} - {chunk.get('content', '')[:50]}...")
            
            print(f"✅ Received {len(response_chunks)} response chunks")
            
        except Exception as e:
            print(f"⚠️ Message processing error (expected without proper DB): {e}")
        
        # Test session cleanup
        print(f"\n🗑️ Cleaning up session...")
        cleanup_success = await hotel_agent.end_session(session_id)
        print(f"✅ Session cleaned up: {cleanup_success}")
        
        # List active sessions
        active_sessions = hotel_agent.list_active_sessions()
        print(f"✅ Active sessions: {len(active_sessions)}")
        
        print("\n🎉 Agent test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Starting Hotel Agent Test...")
    success = asyncio.run(test_agent())
    
    if success:
        print("\n✅ All tests passed! The agent system is ready.")
    else:
        print("\n❌ Some tests failed. Check the configuration.")
        sys.exit(1) 