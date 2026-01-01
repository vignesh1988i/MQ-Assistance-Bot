"""Agent - Synchronous version optimized for CPU deployment"""

import httpx
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import config

class Agent:
    """Agent that manages conversation and delegates tool execution to bridge"""
    
    def __init__(self, session_id:  str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id
        self.conversation_history: List[Dict[str, str]] = []
        self.created_at = datetime.now()
        self.last_activity = datetime. now()
        self.context: Dict[str, any] = {}
    
    def is_expired(self) -> bool:
        """Check if session has expired"""
        timeout = timedelta(minutes=config.SESSION_TIMEOUT_MINUTES)
        return datetime.now() - self.last_activity > timeout
    
    def _extract_qmgr_names(self, text: str) -> List[str]:
        """Extract all potential queue manager names from text"""
        # Match uppercase words 2-20 chars (alphanumeric + underscore/dot)
        pattern = r'\b[A-Z][A-Z0-9_. ]{1,19}\b'
        matches = re.findall(pattern, text)
        
        # Filter out common words
        exclude = {'MQ', 'IBM', 'THE', 'QMGR', 'QUEUE', 'MANAGER', 'IS', 'ON', 'IN', 'TO', 'OF', 'FOR', 'AND', 'OR'}
        return [m for m in matches if m not in exclude]
    
    def _is_question_missing_qmgr(self, question: str) -> bool:
        """Check if question needs a queue manager but doesn't have one"""
        # Patterns that require a queue manager
        needs_qmgr_patterns = [
            r'how many.*queue', r'list.*queue', r'show.*queue', r'count.*queue',
            r'how many.*channel', r'list.*channel', r'show.*channel',
            r'status', r'running', r'check.*queue', r'on.*qmgr', r'on.*queue manager',
            r'queues.*on', r'queues.*in', r'channels.*on', r'channels.*in'
        ]
        
        question_lower = question.lower()
        needs_qmgr = any(re.search(pattern, question_lower) for pattern in needs_qmgr_patterns)
        
        if not needs_qmgr: 
            return False
        
        # Check if question has a qmgr name
        has_qmgr = len(self._extract_qmgr_names(question)) > 0
        
        # Check if asking to list all qmgrs (doesn't need specific qmgr)
        is_listing_qmgrs = 'list all queue manager' in question_lower or 'list queue manager' in question_lower
        
        return needs_qmgr and not has_qmgr and not is_listing_qmgrs
    
    def _enhance_question_with_context(self, question: str) -> str:
        """Add context information to question if available"""
        # Extract and store qmgr if mentioned
        qmgrs = self._extract_qmgr_names(question)
        if qmgrs:
            self. context['last_qmgr'] = qmgrs[0]
            print(f"[CONTEXT] Stored qmgr: {qmgrs[0]}")
            return question
        
        # If question is vague but we have context, enhance it
        if self._is_question_missing_qmgr(question):
            if 'last_qmgr' in self.context:
                qmgr = self.context['last_qmgr']
                
                # Replace vague references with specific qmgr
                enhanced = question.replace('the qmgr', qmgr)
                enhanced = enhanced.replace('on qmgr', f'on {qmgr}')
                enhanced = enhanced.replace('in qmgr', f'in {qmgr}')
                enhanced = enhanced.replace('the queue manager', qmgr)
                enhanced = enhanced.replace('that qmgr', qmgr)
                
                # If no replacement happened, append qmgr
                if enhanced == question:
                    enhanced = f"{question} (Queue manager: {qmgr})"
                
                print(f"[CONTEXT ENHANCED] '{question}' → '{enhanced}'")
                return enhanced
        
        return question
    
    def _call_bridge(self, question:  str) -> str:
        """Call MCP bridge with a clean, standalone question"""
        print(f"[BRIDGE CALL] {question[:100]}...")
    
        start_time = time.time()
    
        try:
            # Synchronous HTTP client
            with httpx.Client() as client:
                print(f"[BRIDGE] Sending to {config.MCP_BRIDGE_URL}")
                
                response = client.post(
                    config.MCP_BRIDGE_URL,
                    json={
                        "model": config.LLM_MODEL,
                        "messages": [
                            {"role": "user", "content": question}
                        ],
                        "stream": False
                    },
                    timeout=1200.0  # 10 minutes for CPU
                )
            
                
                elapsed = round(time.time() - start_time, 1)
                print(f"[BRIDGE] Response in {elapsed}s, Status: {response.status_code}")
                
                response.raise_for_status()
                result = response.json()
                
                # Extract answer from response
                if "message" in result and "content" in result["message"]:
                    answer = result["message"]["content"]
                    print(f"[BRIDGE SUCCESS] {len(answer)} chars: {answer[:100]}...")
                    return answer
                else:
                    print(f"[BRIDGE ERROR] Unexpected format: {result}")
                    return "❌ Unexpected response format from bridge"
                    
        except httpx.TimeoutException:
            elapsed = round(time.time() - start_time, 1)
            print(f"[BRIDGE TIMEOUT] After {elapsed}s")
            return f"⏱️ Request timed out after {elapsed} seconds. The query might be too complex or the server is busy."
            
        except httpx.HTTPStatusError as e:
            elapsed = round(time.time() - start_time, 1)
            print(f"[BRIDGE HTTP ERROR] {e.response.status_code} after {elapsed}s")
            return f"❌ Bridge returned error {e.response.status_code}. Please check if the bridge is running properly."
            
        except httpx.ConnectError:
            print(f"[BRIDGE CONNECT ERROR] Cannot reach {config.MCP_BRIDGE_URL}")
            return f"❌ Cannot connect to MCP Bridge at {config.MCP_BRIDGE_URL}. Please verify:\n- Bridge is running\n- URL is correct\n- Network is accessible"
            
        except Exception as e:
            elapsed = round(time.time() - start_time, 1)
            print(f"[BRIDGE EXCEPTION] {type(e).__name__}: {str(e)} after {elapsed}s")
            return f"❌ Unexpected error: {str(e)}"
    
    
    def chat(self, user_message:  str) -> str:
        """Main chat interface"""
        self. last_activity = datetime.now()
        
        print(f"\n{'='*80}")
        print(f"[CHAT] User: {user_message[:100]}...")
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Check if question needs clarification
        if self._is_question_missing_qmgr(user_message) and 'last_qmgr' not in self.context:
            clarification = "Which queue manager would you like me to check?  (You can say 'list all queue managers' to see available ones)"
            
            self.conversation_history.append({"role": "assistant", "content":  clarification})
            
            print(f"[CLARIFICATION] Asked for queue manager name")
            print(f"{'='*80}\n")
            return clarification
        
        # Enhance question with context if needed
        enhanced_question = self._enhance_question_with_context(user_message)
        
        # Call bridge
        answer = self._call_bridge(enhanced_question)
        
        # Add to history
        self.conversation_history. append({"role": "assistant", "content": answer})
        
        # Trim history to keep memory usage reasonable
        if len(self. conversation_history) > config.MAX_CONVERSATION_HISTORY * 2:
            self.conversation_history = self.conversation_history[-(config.MAX_CONVERSATION_HISTORY * 2):]
            print(f"[HISTORY] Trimmed to {len(self.conversation_history)} messages")
        
        print(f"{'='*80}\n")
        return answer


class SessionManager:
    """Manages multiple user sessions"""
    
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
    
    def get_agent(self, session_id: str, user_id: str) -> Agent:
        """Get or create agent for session"""
        # Check if session exists and is not expired
        if session_id in self._agents:
            agent = self._agents[session_id]
            if not agent.is_expired():
                return agent
            else:
                # Clean up expired session
                print(f"[SESSION EXPIRED] {session_id[: 8]}...")
                del self._agents[session_id]
        
        # Create new agent
        agent = Agent(session_id, user_id)
        self._agents[session_id] = agent
        print(f"[NEW SESSION] {session_id[: 8]}...  for user {user_id}")
        return agent
    
    def cleanup_expired(self):
        """Remove expired sessions (call periodically)"""
        expired = [sid for sid, agent in self._agents.items() if agent.is_expired()]
        for sid in expired:
            del self._agents[sid]
        if expired:
            print(f"[CLEANUP] Removed {len(expired)} expired sessions")
    
    def get_stats(self) -> Dict[str, int]:
        """Get session statistics"""
        total = len(self._agents)
        active = len([a for a in self._agents.values() if not a.is_expired()])
        return {
            "total_sessions": total,
            "active_sessions": active
        }

# Global session manager instance
session_manager = SessionManager()