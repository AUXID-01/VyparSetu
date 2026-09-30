import json
import time
from datetime import date
from groq import AsyncGroq
from config import settings
from sqlalchemy.orm import Session
from services.qa_tools import OPERATIONAL_TOOLS_SCHEMA, execute_tool_call
from core.logging import get_logger

logger = get_logger("core.llm_client")

# Initialize AsyncGroq
client = AsyncGroq(api_key=settings.GROQ_API_KEY)

async def run_grounded_qa_agent(db: Session, merchant_id: str, question: str) -> dict:
    start_time = time.time()
    logger.info(f"🤖 [QA Agent] Received question: '{question}'")
    
    # Step 1: System Prompt Setup
    system_prompt = f"""You are Paytm VyaparSetu's Digital Munimji. Route the merchant's inquiry to the correct tool. Do NOT guess figures.
Current Date: {date.today().isoformat()}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    try:
        # Step 2: Initial Groq Tool-Calling Request
        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=OPERATIONAL_TOOLS_SCHEMA,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if not message.tool_calls:
            return {
                "answer": "Main kewal aapke ledger, bills, aur balance ke sawal bata sakta hoon.",
                "data": None,
                "tool_used": None
            }
            
        all_data = {}
        tool_names = []
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            logger.info(f"🔧 [QA Agent] Dispatching to tool: {tool_name} with args: {arguments}")
            
            result = execute_tool_call(db=db, merchant_id=merchant_id, tool_name=tool_name, arguments=arguments)
            
            if result.get("status") == "ambiguous":
                candidates = result.get("candidates", [])
                return {
                    "answer": "Mujhe ek se zyada records mile. Aap kiski baat kar rahe hain: " + ", ".join(candidates) + "?",
                    "data": None,
                    "tool_used": tool_name
                }
                
            elif result.get("status") == "error":
                return {
                    "status": "error",
                    "answer": "Maaf kijiye, abhi yeh record check karne mein takleef ho rahi hai.",
                    "data": None,
                    "tool_used": tool_name
                }
                
            elif not result.get("data") or result.get("status") == "not_found":
                return {
                    "answer": "Aapke records mein iski koi jaankari nahi mili.",
                    "data": None,
                    "tool_used": tool_name
                }
            
            all_data[tool_name] = result["data"]
            tool_names.append(tool_name)

        synthesis_messages = [
            {
                "role": "system", 
                "content": f"You are VyaparSetu. Narrate the verified database results in clear, polite Hindi/Hinglish for voice playback. You MUST ONLY use the exact figures present in the tool data. Do NOT invent, assume, or estimate any numbers. IMPORTANT: You must write out all currency phonetically in Devanagari or Hinglish (e.g., '15 hazar rupaye', '320 rupaye') instead of using the ₹ symbol, so the TTS engine pronounces it correctly.\n\nDatabase Results:\n{json.dumps(all_data)}"
            },
            {"role": "user", "content": question}
        ]

        synthesis_response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=synthesis_messages
        )
        
        return {
            "answer": synthesis_response.choices[0].message.content,
            "data": all_data,
            "tool_used": ",".join(tool_names)
        }

    except Exception as e:
        logger.error(f"❌ [QA Agent] Error: {e}", exc_info=True)
        return {
            "status": "error",
            "answer": "Maaf kijiye, abhi yeh record check karne mein takleef ho rahi hai.",
            "data": None,
            "tool_used": None
        }
