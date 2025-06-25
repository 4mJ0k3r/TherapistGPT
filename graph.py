from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os
import sqlite3
from mem0 import Memory

load_dotenv()

llm = init_chat_model(model="gpt-4o-mini")


mem0_config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "therapy_memories",
            "host": "localhost",
            "port": 6333,
        }
    },
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o-mini",
            "temperature": 0.1
        }
    }
}


try:
    memory = Memory.from_config(mem0_config)
except Exception as e:
    memory = None


try:
    conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
    checkpointer = SqliteSaver(conn)
except Exception as e:
    checkpointer = None

class State(TypedDict):
    messages: Annotated[list[SystemMessage], add_messages]
    user_id: str

def retrieve_memories(state: State) -> State:
    if not memory:
        return {"messages": [], "user_id": state.get("user_id", "default_user")}
        
    try:
        user_id = state.get("user_id", "default_user")
        

        last_message = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_message = msg.content
                break
        
        if last_message:

            relevant_memories = memory.search(query=last_message, user_id=user_id, limit=5)
            

            memory_list = []
            
            if isinstance(relevant_memories, dict):

                if 'results' in relevant_memories:
                    memory_list = relevant_memories['results']
                elif 'memories' in relevant_memories:
                    memory_list = relevant_memories['memories']
                elif 'data' in relevant_memories:
                    memory_list = relevant_memories['data']
                else:
                    memory_list = [relevant_memories]
                    
            elif isinstance(relevant_memories, list):
                memory_list = relevant_memories
            else:
                memory_list = []
            
            if memory_list:

                memory_texts = []
                for mem in memory_list:
                    if isinstance(mem, dict):

                        memory_text = (
                            mem.get('memory') or 
                            mem.get('text') or 
                            mem.get('content') or 
                            mem.get('data') or
                            str(mem)
                        )
                    elif isinstance(mem, str):
                        memory_text = mem
                    else:
                        memory_text = str(mem)
                    
                    if memory_text and memory_text.strip():
                        memory_texts.append(memory_text.strip())
                
                if memory_texts:
                    memory_context = "\n".join(memory_texts)
                    memory_prompt = SystemMessage(content=f"""
                    Previous conversation memories about this user:
                    {memory_context}
                    
                    Use this context to provide more personalized and contextual responses. 
                    Remember details about the user's previous sessions, concerns, and progress.
                    Build upon what you know about this user from previous conversations.
                    """)
                    
                    return {"messages": [memory_prompt], "user_id": user_id}
    
    except Exception as e:
        pass
    
    return {"messages": [], "user_id": state.get("user_id", "default_user")}

def chatbot(state: State) -> State:
    system_prompt = SystemMessage(content="""You are a compassionate and supportive virtual therapist chatbot, specially designed to help users manage stress, anger, tension, depression, anxiety, and other life-related challenges. Your primary goal is to listen empathetically, guide users towards understanding their feelings and thoughts, and provide actionable strategies and coping mechanisms to improve their mental and emotional well-being.  

        When interacting with users, always adhere to these guiding principles:

        1. **Empathy and Understanding:**
        * Acknowledge and validate the user's feelings without judgment.
        * Use supportive and reassuring language, such as "It's completely understandable that you feel this way," or "I'm here to support you through this."

        2. **Active Listening:**
        * Encourage users to express their emotions and experiences fully.
        * Use reflective phrases like, "It sounds like you're feeling..." or "What I'm hearing is that you're experiencing..."

        3. **Identifying Issues:**
        * Ask gentle, clarifying questions to better understand the user's concerns, such as "Can you tell me more about what's causing you to feel this way?"

        4. **Providing Insights and Guidance:**
        * Offer insightful perspectives to help users reframe negative thoughts into more balanced viewpoints.
        * Suggest constructive thinking patterns like cognitive restructuring, reframing challenges into growth opportunities.

        5. **Suggesting Coping Mechanisms:**
        * Recommend evidence-based stress-reduction techniques such as deep breathing exercises, mindfulness meditation, progressive muscle relaxation, and journaling.
        * Encourage healthy lifestyle choices, including physical activity, balanced nutrition, and regular sleep patterns.

        6. **Anger Management:**
        * Teach anger management strategies, such as taking a timeout, identifying triggers, and practicing assertive communication.

        7. **Depression and Anxiety Support:**
        * Provide supportive counseling approaches, emphasizing small, achievable goals to improve mood and reduce anxiety.
        * Promote positive activities and routines that boost serotonin and dopamine, such as outdoor walks, engaging hobbies, and social interactions.

        8. **Safety and Professional Referral:**
        * Recognize signs indicating severe distress or crisis.
        * Urge immediate contact with professional human therapists, helplines, or emergency services if the user expresses suicidal thoughts or intentions of self-harm.

        9. **Confidentiality Assurance:**
        * Remind users that their conversations are confidential and designed to provide a safe space for sharing without fear of judgment.

        **Memory Integration:**
        * Use previous session information to provide continuity in therapy
        * Reference past discussions, progress, and concerns when relevant
        * Build upon previous therapeutic work and insights

        Always maintain a calming, respectful tone, consistently encouraging users to take proactive, positive steps towards improving their mental health and overall life quality.
        """)
    

    messages = [system_prompt] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response], "user_id": state.get("user_id", "default_user")}

def store_memories(state: State) -> State:
    if not memory:
        return {"messages": [], "user_id": state.get("user_id", "default_user")}
        
    try:
        user_id = state.get("user_id", "default_user")
        

        recent_messages = state["messages"][-4:]
        

        conversation_text = ""
        for msg in recent_messages:
            if isinstance(msg, (HumanMessage, AIMessage)):
                role = "User" if isinstance(msg, HumanMessage) else "Therapist"
                conversation_text += f"{role}: {msg.content}\n"
        
        if conversation_text:

            memory.add(conversation_text, user_id=user_id)
    
    except Exception as e:
        pass
    
    return {"messages": [], "user_id": state.get("user_id", "default_user")}


graph = StateGraph(State)
graph.add_node("retrieve_memories", retrieve_memories)
graph.add_node("chatbot", chatbot)
graph.add_node("store_memories", store_memories)


graph.add_edge(START, "retrieve_memories")
graph.add_edge("retrieve_memories", "chatbot")
graph.add_edge("chatbot", "store_memories")
graph.add_edge("store_memories", END)


if checkpointer:
    app = graph.compile(checkpointer=checkpointer)
else:
    app = graph.compile()

