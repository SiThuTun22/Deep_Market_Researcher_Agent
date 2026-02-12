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
    reflect_on_tool_use=True,
    system_message=(
        "you are a market researcher"
        "Use the 'web_search' tool to find data."
        "always include the source urls in your findings."
        "Format: [Fact] - [URL]."
        "Do not say 'Done' until you have provided at least 3 URLs."
    )
)
reviewer = AssistantAgent(
    name="reviewer",
    model_client=model_client,
    system_message=(
        "Verify the researcher's findings. Check if URLs are present."
        "If URLs are missing, tell the researcher: 'REDO: Missing URLs'."
        "If URLs are present and data is solid, say 'VERIFIED'."
        )

)

synthesizer = AssistantAgent(
    name="synthesizer",
    model_client=model_client,
    system_message=(
        "Create a professional market report using the verified data."
        "Include a 'Sources' section at the end listing all URLs."
        "End your message with the word: TERMINATE"
    )
)
termination = TextMentionTermination("TERMINATE")
research_team = RoundRobinGroupChat([researcher,reviewer,synthesizer],termination_condition=termination)

