# Import the keys
import os
from dotenv import load_dotenv
import pandas as pd
load_dotenv('.env')

WEATHER_API_KEY = os.environ['WEATHER_API_KEY']
TAVILY_API_KEY = os.environ['TAVILY_API_KEY']
#TOGETHER_API_KEY = os.environ['TOGETHER_API_KEY']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

import pandas as pd

# Import the required libraries and methods
import requests
from typing import List, Literal
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from tools import search_web

"""
@tool
def search_web(query: str) -> list:
    Search the web for a query
    tavily_search = TavilySearchResults(api_key=TAVILY_API_KEY, max_results=2, search_depth='advanced', max_tokens=1000)
    results = tavily_search.invoke(query)
    return results
"""

# If you have OpenAI key
llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY, temperature=0)

tools = [search_web]
llm_with_tools = llm.bind_tools(tools)

from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END

tool_node = ToolNode(tools)

def call_model(state: MessagesState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def call_tools(state: MessagesState) -> Literal["tools", END]:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

# initialize the workflow from StateGraph
workflow = StateGraph(MessagesState)

# add a node named LLM, with call_model function. This node uses an LLM to make decisions based on the input given
workflow.add_node("LLM", call_model)

# Our workflow starts with the LLM node
workflow.add_edge(START, "LLM")

# Add a tools node
workflow.add_node("tools", tool_node)

# Add a conditional edge from LLM to call_tools function. It can go tools node or end depending on the output of the LLM. 
workflow.add_conditional_edges("LLM", call_tools)

# tools node sends the information back to the LLM
workflow.add_edge("tools", "LLM")

agent = workflow.compile()

collected_chunks = []
for chunk in agent.stream(
    {"messages": [("user", "Who is wheather Lio Messi?")]},
    stream_mode="values",
    ):
    msg = chunk["messages"][-1]
    msg.pretty_print()

    collected_chunks.append({
        "content": msg.content
    })

# Convert to DataFrame
#df = pd.DataFrame(collected_chunks)
#print("\n\nData saved to DataFrame ✅")
#print(df.head())
    
