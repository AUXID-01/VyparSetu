import json
import time
import re
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
    
    # Step 1: Single-Hop System Prompt Setup with Transliteration Rules
    system_prompt = f"""You are Paytm VyaparSetu's Digital Munimji. Route the merchant's inquiry to the correct tool. Do NOT guess figures.
Current Date: {date.today().isoformat()}

CRITICAL INDIC ENTITY NORMALIZATION RULES:
1. The merchant may speak or ask in any Indian language or script (Hindi, Hinglish, Bengali, Marathi, Tamil, Telugu, Gujarati, English, etc.).
2. You must directly understand their inquiry and map it to the correct tool.
3. Normalize all extracted entity arguments strictly into standard lowercase English Latin characters:
   - customer_name: TRANSLITERATE proper nouns and personal names phonetically into lowercase English Latin characters (e.g. 'आयुष' -> 'ayush', 'कमल' -> 'kamal', 'सुरेश' -> 'suresh', 'नंदिनी' -> 'nandini'). NEVER translate names into English dictionary words (e.g. 'kamal', NEVER 'lotus').
   - distributor_name: TRANSLITERATE to lowercase English Latin characters (e.g. 'अमुल' -> 'amul').
   - item_name: TRANSLATE generic goods to standard lowercase English words (e.g. 'तेल' -> 'oil', 'दूध' -> 'milk', 'दही' -> 'curd').
4. Date ranges: Select the appropriate DateRange enum (TODAY, YESTERDAY, THIS_WEEK, LAST_WEEK, LAST_7_DAYS, THIS_MONTH, LAST_MONTH)."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    try:
        # Step 2: Single-Hop Groq Tool-Calling Request
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

        # Step 3: Localized Spoken Synthesis for Voice Audio
        synthesis_prompt = f"""You are VyaparSetu. Narrate the verified database results in clear, polite spoken style for audio playback.

CRITICAL VOICE & LOCALIZATION RULES:
1. MATCH THE USER'S QUERY LANGUAGE:
   - If the merchant asked in Hindi or Hinglish, answer in polite, natural spoken Hindi/Hinglish.
   - If the merchant asked in Bengali, Marathi, Tamil, or English, answer in that respective language.
2. STRICT NUMERIC ACCURACY: ONLY use the exact figures present in the Database Results. Do NOT invent, assume, or estimate any numbers.
3. PHONETIC CURRENCY: NEVER use the currency symbol '₹' or abbreviations like 'Rs' or 'INR'. ALWAYS spell currency phonetically in spoken text (e.g. '350 rupaye', 'teen sau pachas rupaye', or '15 hazar rupaye') so the text-to-speech voice sounds completely natural.
4. NO MARKDOWN: NEVER use asterisks (**), headers (#), bullet points, or tables. Output plain, conversational sentences designed for spoken voice.
5. Keep the response to 1 or 2 clear, helpful sentences.

Database Results:
{json.dumps(all_data)}"""

        synthesis_messages = [
            {"role": "system", "content": synthesis_prompt},
            {"role": "user", "content": question}
        ]

        synthesis_response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=synthesis_messages
        )
        
        raw_answer = synthesis_response.choices[0].message.content or ""
        # Clean any accidental Markdown or currency symbols
        clean_answer = raw_answer.replace("₹", "rupaye").replace("**", "").replace("*", "").strip()

        return {
            "answer": clean_answer,
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
