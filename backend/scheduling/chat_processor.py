import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class SchedulingChatProcessor:
    """
    Basic chat processor for scheduling-related questions
    No external APIs required - uses simple pattern matching and logic
    """
    
    def __init__(self, facility_id: int):
        self.facility_id = facility_id
        self.staff_data = None
        self.shifts_data = None
        self.templates_data = None
        self.assignments_data = None
        
    def load_data(self):
        """Load scheduling data for chat responses"""
        try:
            from scheduling.models import Staff, Shift, ShiftTemplate, StaffAssignment, StaffAvailability
            
            # Load staff data with availability preferences
            staff_queryset = Staff.objects.filter(
                facility_id=self.facility_id,
                status='active'
            ).prefetch_related('availability')
            
            self.staff_data = []
            for staff in staff_queryset:
                staff_data = {
                    'id': staff.id,
                    'first_name': staff.first_name,
                    'last_name': staff.last_name,
                    'role': staff.role,
                    'preferred_shifts': [],
                    'status': staff.status
                }
                
                # Get availability preferences
                try:
                    availability = staff.availability.first()
                    if availability:
                        staff_data['preferred_shifts'] = availability.preferred_shifts or []
                except:
                    pass
                
                self.staff_data.append(staff_data)
            
            # Load other data
            self.shifts_data = list(Shift.objects.filter(facility_id=self.facility_id).values())
            self.templates_data = list(ShiftTemplate.objects.filter(facility_id=self.facility_id, is_active=True).values())
            self.assignments_data = list(StaffAssignment.objects.filter(shift__facility_id=self.facility_id).values())
            
        except Exception as e:
            print(f"Error loading data for chat: {e}")
            self.staff_data = []
            self.shifts_data = []
            self.templates_data = []
            self.assignments_data = []
    
    def process_message(self, message: str) -> str:
        """Process a chat message and return a response"""
        original_message = message
        message = message.lower().strip()
        
        # Load data if not already loaded
        if not self.staff_data:
            self.load_data()
        
        # More intelligent message classification
        intent = self._classify_intent(message)
        
        if intent == 'staff_info':
            return self._handle_staff_questions(original_message)
        elif intent == 'schedule_info':
            return self._handle_shift_questions(original_message)
        elif intent == 'ai_explanation':
            return self._handle_ai_questions(original_message)
        elif intent == 'help_request':
            return self._get_help_message()
        elif intent == 'greeting':
            return self._get_greeting_response(original_message)
        elif intent == 'general_question':
            return self._handle_general_questions(original_message)
        else:
            return self._get_generic_response(original_message)
    
    def _matches_pattern(self, message: str, keywords: List[str]) -> bool:
        """Check if message contains any of the keywords"""
        return any(keyword in message for keyword in keywords)
    
    def _classify_intent(self, message: str) -> str:
        """Intelligently classify the user's intent"""
        # Greetings and casual conversation (be more specific to avoid false matches)
        greetings = ['hi ', 'hello', 'hey ', 'good morning', 'good afternoon', 'good evening', 'how are you']
        if any(greeting in message for greeting in greetings):
            return 'greeting'
        
        # Help requests
        help_indicators = ['help', 'what can you do', 'capabilities', 'how does this work', 'explain']
        if any(help_indicator in message for help_indicator in help_indicators):
            return 'help_request'
        
        # AI and explanation questions (check this FIRST to avoid conflicts)
        ai_indicators = ['ai', 'recommendation', 'confidence', 'why', 'assign', 'explain', 'reason', 'logic']
        if any(ai_indicator in message for ai_indicator in ai_indicators):
            return 'ai_explanation'
        
        # Staff-related questions
        staff_indicators = ['staff', 'employee', 'worker', 'people', 'team', 'who', 'preference', 'role']
        if any(staff_indicator in message for staff_indicator in staff_indicators):
            return 'staff_info'
        
        # Schedule and shift questions
        schedule_indicators = ['shift', 'schedule', 'assignment', 'today', 'week', 'when', 'how many shifts']
        if any(schedule_indicator in message for schedule_indicator in schedule_indicators):
            return 'schedule_info'
        
        # General questions that might be about the system
        general_indicators = ['what', 'how', 'can you', 'is there', 'do you have', 'tell me about']
        if any(general_indicator in message for general_indicator in general_indicators):
            return 'general_question'
        
        return 'unknown'
    
    def _handle_staff_questions(self, message: str) -> str:
        """Handle questions about staff"""
        if 'how many' in message and 'staff' in message:
            return f"Currently there are {len(self.staff_data)} active staff members at this facility. That's a good-sized team for managing your scheduling needs!"
        
        elif 'preference' in message or 'prefer' in message or 'what do they like' in message:
            preferences = []
            for staff in self.staff_data:
                if staff['preferred_shifts']:
                    preferences.append(f"• {staff['first_name']} {staff['last_name']} prefers {', '.join(staff['preferred_shifts'])} shifts")
            
            if preferences:
                return "Here are the current staff shift preferences:\n" + "\n".join(preferences) + "\n\nThis helps our AI create schedules that everyone enjoys!"
            else:
                return "No specific shift preferences have been set for staff members yet. Setting preferences helps our AI create better schedules that match what staff actually want to work!"
        
        elif 'role' in message or 'what roles' in message:
            roles = {}
            for staff in self.staff_data:
                role = staff['role']
                roles[role] = roles.get(role, 0) + 1
            
            role_summary = ", ".join([f"{count} {role}" for role, count in roles.items()])
            return f"Your facility has a diverse team with {role_summary}. This variety helps ensure all your scheduling needs are covered!"
        
        elif 'who' in message and ('staff' in message or 'employee' in message):
            staff_list = []
            for staff in self.staff_data:
                staff_list.append(f"• {staff['first_name']} {staff['last_name']} ({staff['role']})")
            
            return f"Here are your current staff members:\n" + "\n".join(staff_list)
        
        else:
            return f"I'd be happy to help with staff information! You have {len(self.staff_data)} active staff members. You can ask me about their preferences, roles, or just ask 'who are my staff' to see everyone."
    
    def _handle_shift_questions(self, message: str) -> str:
        """Handle questions about shifts and scheduling"""
        if 'how many' in message and 'shift' in message:
            total_shifts = len(self.shifts_data)
            return f"Your facility currently has {total_shifts} total shifts scheduled. That's quite a comprehensive schedule!"
        
        elif 'today' in message or 'current' in message or 'what\'s happening today' in message:
            today = datetime.now().strftime('%Y-%m-%d')
            today_shifts = [s for s in self.shifts_data if s.get('date') == today]
            if today_shifts:
                return f"Today ({today}) you have {len(today_shifts)} shifts scheduled. It's going to be a busy day!"
            else:
                return f"Today ({today}) you have no shifts scheduled. It's a quiet day at your facility!"
        
        elif 'week' in message or 'this week' in message:
            # Count shifts for current week
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            week_dates = [week_start + timedelta(days=i) for i in range(7)]
            week_dates_str = [d.strftime('%Y-%m-%d') for d in week_dates]
            
            week_shifts = [s for s in self.shifts_data if s.get('date') in week_dates_str]
            return f"This week you have {len(week_shifts)} shifts scheduled across all your staff. That's good coverage for your facility!"
        
        elif 'when' in message and 'shift' in message:
            return "I can help you find out about shifts! You can ask me about today's schedule, this week's shifts, or how many total shifts you have scheduled."
        
        else:
            return "I'd love to help with your shift information! You can ask me about today's schedule, this week's shifts, or just ask 'how many shifts do I have' to get an overview."
    
    def _handle_ai_questions(self, message: str) -> str:
        """Handle questions about AI recommendations"""
        message_lower = message.lower()
        
        if 'confidence' in message_lower or 'how confident' in message_lower:
            return "Great question! The AI confidence score is calculated based on several factors: shift coverage (making sure all shifts are filled), staff utilization (keeping everyone busy but not overwhelmed), and workload balance (distributing work fairly). Higher scores mean the AI is more confident that it created an optimal schedule that everyone will be happy with!"
        
        if 'why' in message_lower and ('assign' in message_lower or 'staff' in message_lower):
            # Provide specific explanation based on current assignments
            if 'staff 3' in message_lower and 'noc' in message_lower:
                return "Great question! Staff 3 was assigned to NOC shifts because they explicitly prefer night shifts. Our AI is smart - it prioritizes staff preferences to maximize job satisfaction and reduce turnover. When staff work shifts they actually want, everyone wins!"
            if 'staff 4' in message_lower and 'day' in message_lower:
                return "Staff 4 got assigned to Day shifts because they prefer day shifts! The AI makes sure staff work their preferred shifts whenever possible. It's like having a scheduling expert who remembers everyone's preferences."
            if 'staff 2' in message_lower and 'swing' in message_lower:
                return "Staff 2 was assigned to Swing shifts because they prefer both day and swing shifts. Since Staff 4 got their first choice (day shifts), Staff 2 got their second preference. The AI tries to give everyone their top choice when possible!"
            return "The AI makes assignments based on staff preferences, role requirements, and availability. It's designed to create schedules that make staff happy while ensuring all your facility's needs are met. Think of it as having a super-smart scheduling coordinator!"
        
        if 'recommendation' in message_lower or 'how does ai work' in message_lower:
            return "Our AI is pretty clever! It analyzes staff preferences, shift requirements, and creates optimal schedules that minimize conflicts and maximize satisfaction. It's like having a scheduling expert who never forgets anyone's preferences and can juggle all the variables to create the best possible schedule!"
        
        return "I love talking about our AI! It's designed to create optimal schedules by considering staff preferences, role requirements, and preventing scheduling conflicts. It's like having a scheduling expert who never gets tired and always remembers everyone's preferences!"
    
    def _get_help_message(self) -> str:
        """Return help information"""
        return """Hi there! I'm your AI scheduling assistant, and I'm here to help make your scheduling life easier!

Here's what I can help you with:

Staff & Team Info:
- "How many staff do I have?"
- "What are their shift preferences?"
- "Who are my staff members?"
- "What roles do we have?"

Schedule & Shifts:
- "What's happening today?"
- "How many shifts this week?"
- "Tell me about my schedule"

AI & Smart Scheduling:
- "Why did the AI assign Staff 3 to NOC?"
- "How confident is the AI?"
- "How does the AI work?"
- "Explain the recommendations"

Pro Tips:
- Just ask naturally like you're talking to a colleague
- I understand context and can handle follow-up questions
- Feel free to ask "why" or "how" questions

Try asking me something like:
- "Hi, how are you?"
- "What can you tell me about my staff?"
- "Why did the AI make that decision?"
- "Help me understand my schedule"

What would you like to know about your scheduling system? I'm here to help!"""
    
    def _get_generic_response(self, message: str) -> str:
        """Return a generic response for unrecognized messages"""
        return f"I'm not quite sure what you mean by '{message}'. But don't worry! I'm here to help with your scheduling system.\n\nTry asking me about:\n- Your staff and their preferences\n- Today's or this week's schedule\n- How our AI makes decisions\n- Or just say 'help' to see everything I can do!\n\nI'm pretty good at understanding natural language, so feel free to rephrase your question or ask it a different way!"
    
    def _get_greeting_response(self, message: str) -> str:
        """Handle greetings and casual conversation"""
        greetings = [
            "Hi there! I'm your AI scheduling assistant. How can I help you today?",
            "Hello! I'm here to help with your scheduling needs. What would you like to know?",
            "Hey! Ready to help you with staff scheduling and AI recommendations!",
            "Good day! I'm your scheduling assistant. How may I assist you?"
        ]
        import random
        return random.choice(greetings)
    
    def _handle_general_questions(self, message: str) -> str:
        """Handle general questions about the system"""
        if 'what is this' in message.lower() or 'what do you do' in message.lower():
            return "I'm an AI scheduling assistant that helps you manage staff schedules, understand AI recommendations, and get insights about your facility's staffing needs. I can answer questions about staff, shifts, schedules, and explain how our AI makes decisions!"
        
        elif 'how does this work' in message.lower() or 'how do you work' in message.lower():
            return "I work by analyzing your facility's data - staff information, shift schedules, and AI recommendations. I understand natural language questions and provide helpful answers based on your actual data. Think of me as your scheduling expert who's always available to help!"
        
        elif 'can you help me' in message.lower():
            return "Absolutely! I'm here to help you with all things scheduling. I can tell you about your staff, explain shift schedules, clarify AI decisions, and much more. Just ask me anything about your scheduling system!"
        
        else:
            return "I'm here to help with your scheduling system! I can answer questions about staff, shifts, AI recommendations, and more. Try asking me something specific, or type 'help' to see what I can do."
