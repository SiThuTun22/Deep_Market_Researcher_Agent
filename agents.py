import os
from typing import Any,List
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from duckduckgo_search import DDGS
from autogen_core.models import ModelFamily
import httpx
from dotenv import load_dotenv
from autogen_agentchat.teams import RoundRobinGroupChat
import asyncio
from autogen_agentchat.conditions import TextMentionTermination
load_dotenv()
#Set up 
model_client = OpenAIChatCompletionClient(
    model="llama-3.3-70b-versatile",
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    model_info={
        "vision":False,
        "function_calling":True,
        "json_output":False,
        "family":ModelFamily.LLAMA_3_3_70B,
        'structured_output': False
    },
    parallel_tool_calls=False,
    include_name_in_message=False,
    extra_configs={'tool_choice':"auto"}
)

# browse internet tool
async def web_search(query: str)-> str:
    """
    Search the internet for real-time market data.
    """
    await asyncio.sleep(1)
    api_key = os.environ.get("BRAVE_API_KEY")
    if not api_key:
        return "Error: BRAVE_API_KEY not found in environment."
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q":query,"count": 5},
                headers = headers,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            results = data.get("web",{}).get("results",[])
            if not results:
                return f"No results found for '{query}'. The topic might be too niche."
            snippets = [f"Source: {r['url']}\nContent: {r['description']}" for r in results]
            return "\n\n---\n\n".join(snippets)
        except httpx.HTTPStatusError as e:
            return f"Search API Error: {e.response.status_code}"
        except Exception as e:
            return f"Unexpected Search Error: {str(e)}"
    
researcher = AssistantAgent(
    name="researcher",
    model_client=model_client,
    tools=[web_search],
    reflect_on_tool_use=False,
    system_message=(
        "You are an expert Market Research Specialist.\n\n"
        "1. use the 'web_search' tool to get data.\n"
        "2. If results are empty, broaden your query and try again immediately.\n"
        "3. You must attempt at least 3 distinct search variations before giving up.\n\n"
        "After gathering data, provide a concise bulleted synthesis with source URLs.\n"
        "After providing your bulleted research and source URLs, you MUST "
        "write the word 'TERMINATE' and stop. "
        "DO NOT ask follow-up questions. DO NOT offer further help. "
        "DO NOT repeat yourself."
        "IMPORTANT: Simply use the tool. Do not explain your steps or use XML tags.\n"
        "IMPORTANT: DO NOT use <function> or </function> tags." 
    )
)

termination = TextMentionTermination("TERMINATE")
research_team = RoundRobinGroupChat([researcher],termination_condition=termination)

