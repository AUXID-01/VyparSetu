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
    
    # Step 1: Agentic System Prompt Setup
    system_prompt = f"""You are Paytm VyaparSetu's Digital Munimji. Answer the merchant's inquiries by calling the necessary tools.
Current Date: {date.today().isoformat()}

RULES & CAPABILITIES:
1. COMPOUND & MULTI-PART INQUIRIES:
   - The merchant may ask single questions, compound questions with multiple items/people, or general questions with no names at all (e.g. daily sales, collections, inventory price trends).
   - If the inquiry asks about multiple customers, multiple suppliers, or combines shop totals with customer balances, call tools iteratively until ALL parts of the question are verified.
   - For open-ended questions about suppliers, distributors, or vendor payments without a specific name (e.g., 'Kaunse distributor ka bill paid hai aur kiska payment baaki hai?', 'Kiska payment pending hai?', 'Distributor bills ka kya status hai?'), call 'get_all_suppliers_payment_overview'. Do NOT ask the user for distributor names when they ask an open-ended question.
2. GENERAL INQUIRIES:
   - If the merchant asks general questions or greetings (e.g., 'Hello', 'Aap kya kya hisab dekh sakte ho?'), answer politely and directly without calling tools.
3. INDIC ENTITY NORMALIZATION:
   - The merchant may speak or type in any Indian language or script (Hindi, Hinglish, Bengali, Marathi, Tamil, Telugu, English, etc.).
   - Normalize all extracted entity arguments into lowercase standard English Latin characters:
     * customer_name: TRANSLITERATE proper nouns and personal names phonetically into lowercase English Latin characters (e.g. 'कमल' -> 'kamal', 'नंदिनी' -> 'nandini', 'आयुष' -> 'ayush', 'सुरेश' -> 'suresh'). NEVER translate names to English nouns (e.g. 'kamal', NEVER 'lotus').
     * distributor_name: TRANSLITERATE to lowercase English Latin characters (e.g. 'अमुल' -> 'amul').
     * item_name: TRANSLATE generic goods to standard lowercase English words (e.g. 'तेल' -> 'oil', 'दूध' -> 'milk', 'दही' -> 'curd').
4. SPOKEN RESPONSE RULES:
   - Provide the final answer in polite spoken conversational style matching the user's language (Hindi, Hinglish, Bengali, Marathi, English, etc.).
   - When answering bill, invoice, or supplier payment queries, state the exact bill amount, payment status (paid or unpaid), and if available, include the payout reference or UTR number.
   - ALWAYS write out all currency phonetically (e.g., '350 rupaye', '1055 rupaye', '15 hazar rupaye').
   - NEVER use the currency symbol '₹' or abbreviations like 'Rs' or 'INR'.
   - NEVER use Markdown formatting like asterisks (**), headers (#), bullet points, or tables. Output plain, spoken sentences."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    all_data = {}
    tool_names_used = []
    max_steps = 4

    try:
        # Step 2: Multi-Turn Agentic Tool-Use Loop
        for step in range(max_steps):
            response = await client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                tools=OPERATIONAL_TOOLS_SCHEMA,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            messages.append(message)
            
            # If no more tools called, agent has reached final answer
            if not message.tool_calls:
                raw_answer = message.content or ""
                clean_answer = (
                    raw_answer
                    .replace("₹", "rupaye")
                    .replace("**", "")
                    .replace("*", "")
                    .replace("#", "")
                    .replace("- ", "")
                    .strip()
                )
                logger.info(f"✅ [QA Agent] Completed in {step + 1} steps. Tools used: {tool_names_used}")
                return {
                    "answer": clean_answer,
                    "data": all_data,
                    "tool_used": ",".join(tool_names_used) if tool_names_used else None
                }
                
            # Execute all tool calls for this step
            for tc in message.tool_calls:
                tool_name = tc.function.name
                try:
                    arguments = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except Exception:
                    arguments = {}

                logger.info(f"🔧 [QA Agent] [Step {step + 1}] Executing tool: {tool_name} with args: {arguments}")
                result = execute_tool_call(db=db, merchant_id=merchant_id, tool_name=tool_name, arguments=arguments)
                
                # Prevent key collisions when same tool is called multiple times
                storage_key = tool_name
                if storage_key in all_data:
                    sub_key = arguments.get("customer_name") or arguments.get("distributor_name") or len(all_data)
                    storage_key = f"{tool_name}_{sub_key}"
                all_data[storage_key] = result.get("data")
                
                if tool_name not in tool_names_used:
                    tool_names_used.append(tool_name)

                # Feed execution result back into message history for next turn
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tool_name,
                    "content": json.dumps(result)
                })

        # Fallback if loop exceeded max_steps
        logger.warning(f"⚠️ [QA Agent] Reached max_steps ({max_steps}). Requesting final synthesis.")
        synthesis_response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages + [{"role": "user", "content": "Please summarize all verified database results into a spoken answer."}]
        )
        raw_answer = synthesis_response.choices[0].message.content or ""
        clean_answer = raw_answer.replace("₹", "rupaye").replace("**", "").replace("*", "").replace("#", "").strip()

        return {
            "answer": clean_answer,
            "data": all_data,
            "tool_used": ",".join(tool_names_used) if tool_names_used else None
        }

    except Exception as e:
        logger.error(f"❌ [QA Agent] Error: {e}", exc_info=True)
        return {
            "status": "error",
            "answer": "Maaf kijiye, abhi yeh record check karne mein takleef ho rahi hai.",
            "data": None,
            "tool_used": None
        }
