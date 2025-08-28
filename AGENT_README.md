# 🏨 Hotel Receptionist AI Agent System

Welcome to the Hotel Receptionist AI Agent System! This intelligent agent uses Google's Gemini AI to provide professional hotel receptionist services to guests.

## 🚀 Features

### **AI-Powered Receptionist**
- **Natural Language Processing**: Understands guest requests in natural language
- **Context Awareness**: Remembers conversation history and guest preferences
- **Professional Tone**: Maintains a warm, welcoming, and professional demeanor
- **Multi-language Support**: Can handle requests in various languages

### **Available Tools & Capabilities**
- **Guest Management**: Create, update, and search guest profiles
- **Room Information**: Provide details about room types, availability, and pricing
- **Reservation System**: Handle bookings, modifications, and cancellations
- **Hotel Services**: Information about amenities, local attractions, and services
- **Check-in/Check-out**: Assist with arrival and departure processes

### **Chat Session Management**
- **Persistent Conversations**: Maintains chat history across sessions
- **Guest Context**: Remembers guest preferences and previous interactions
- **Session Analytics**: Track conversation metrics and engagement
- **Multi-device Support**: Continue conversations from different devices

## 🛠️ Setup Instructions

### 1. **Environment Configuration**
```bash
# Copy the environment template
cp env.example .env

# Edit .env and add your Gemini API key
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 2. **Install Dependencies**
```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 3. **Database Setup**
```bash
# Start your Docker containers
docker-compose up -d

# Run database migrations
alembic upgrade head

# Seed the database with sample data
python seed_database.py
```

### 4. **Start the Application**
```bash
python start.py
```

## 📡 API Endpoints

### **Chat Session Management**

#### **Start Chat Session**
```http
POST /api/v1/chat/start?guest_id={optional_guest_id}
```
Creates a new chat session. If `guest_id` is provided, the agent will have access to guest information.

#### **Send Message**
```http
POST /api/v1/chat/message
Content-Type: application/json

{
  "message": "I'd like to book a room for next weekend",
  "session_id": "optional_session_id",
  "guest_id": "optional_guest_id"
}
```

#### **Get Chat Session**
```http
GET /api/v1/chat/session/{session_id}
```
Retrieves chat session information and message history.

#### **End Chat Session**
```http
POST /api/v1/chat/session/{session_id}/end
Content-Type: application/json

{
  "reason": "Guest completed their request"
}
```

#### **Get Session Summary**
```http
GET /api/v1/chat/session/{session_id}/summary
```
Provides statistics and metadata about the chat session.

#### **View Available Tools**
```http
GET /api/v1/chat/tools
```
Lists all tools available to the AI agent.

## 💬 Example Conversations

### **Room Booking Request**
```
Guest: "Hi, I'd like to book a double room for next weekend, March 15-17."

Agent: "Hello! I'd be happy to help you book a double room for March 15-17. Let me check our availability for you.

I can see we have several double rooms available for those dates. Our double rooms feature:
- Comfortable bedding for 2 guests
- Private bathroom
- WiFi and TV
- Starting at $129.99 per night

Would you like me to check if you have an existing guest profile, or should I create a new one for you? Also, do you have any specific preferences like floor level or view?"
```

### **Guest Profile Creation**
```
Guest: "I don't have a profile yet. My name is Sarah Johnson, email is sarah.j@email.com."

Agent: "Perfect! I'll create a guest profile for you, Sarah Johnson. Let me set that up right away.

I've created your guest profile with the email sarah.j@email.com. Now, let me proceed with your room booking for March 15-17.

For your double room reservation, the total for 2 nights would be $259.98. Would you like me to proceed with the booking? I can also add any special requests or preferences to your reservation."
```

### **Room Availability Inquiry**
```
Guest: "What types of rooms do you have available?"

Agent: "I'd be happy to show you our available room types! Let me check our current inventory.

Here's what we have available:

🏨 **Single Rooms** (1 guest)
- Starting at $89.99/night
- Perfect for solo travelers
- Includes WiFi, TV, air conditioning, and private bathroom

🏨 **Double Rooms** (2 guests) 
- Starting at $129.99/night
- Ideal for couples or friends
- Features balcony options and mini fridge

🏨 **Suites** (4-6 guests)
- Starting at $249.99/night
- Separate living area and kitchenette
- Premium amenities and panoramic views

🏨 **Deluxe Rooms** (3 guests)
- Starting at $189.99/night
- Premium bedding and mini bar
- Work desk and enhanced amenities

Which type of room interests you? I can provide more specific details about any category!"
```

## 🔧 Agent Tools

The AI agent has access to the following tools:

### **Guest Management**
- `create_guest`: Create new guest profiles
- `update_guest`: Update existing guest information
- `get_guest`: Retrieve guest details
- `search_guests`: Search guests by name or email

### **Room Management**
- `get_all_rooms`: View all room information
- `get_available_rooms`: Check room availability
- `get_rooms_by_type`: Filter rooms by type
- `get_room_status`: Check specific room status

### **Reservation Management**
- `create_reservation`: Book new reservations
- `update_reservation`: Modify existing bookings
- `cancel_reservation`: Cancel reservations
- `get_guest_reservations`: View guest's booking history

## 🎯 Best Practices

### **For Developers**
1. **Error Handling**: Always handle potential API failures gracefully
2. **Session Management**: Maintain chat sessions for better context
3. **Rate Limiting**: Implement appropriate rate limiting for production use
4. **Logging**: Monitor agent interactions for quality improvement

### **For Users**
1. **Clear Communication**: Be specific about your needs and preferences
2. **Session Continuity**: Use the same session ID for related requests
3. **Guest Profile**: Provide guest ID if you have an existing profile
4. **Feedback**: Let us know if the agent's responses are helpful

## 🚨 Troubleshooting

### **Common Issues**

#### **Agent Not Responding**
- Check if your `GEMINI_API_KEY` is set correctly
- Verify the database connection is working
- Check application logs for error messages

#### **Session Errors**
- Ensure session IDs are valid and active
- Check if sessions haven't expired
- Verify guest IDs exist in the system

#### **Database Connection Issues**
- Confirm Docker containers are running
- Check database credentials in `.env`
- Verify network connectivity

### **Getting Help**
1. Check the application logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure all dependencies are installed
4. Check the Swagger documentation at `/docs`

## 🔮 Future Enhancements

- **Voice Integration**: Add speech-to-text and text-to-speech capabilities
- **Multi-language Support**: Enhanced language processing for international guests
- **Sentiment Analysis**: Monitor guest satisfaction and escalate issues
- **Integration APIs**: Connect with external booking systems and payment processors
- **Advanced Analytics**: Detailed insights into guest interactions and preferences

## 📞 Support

For technical support or questions about the AI agent system:
- Check the application logs
- Review the Swagger documentation at `/docs`
- Ensure all setup steps have been completed correctly

---

**Happy coding! 🎉** The Hotel Receptionist AI Agent is ready to provide exceptional guest experiences! 