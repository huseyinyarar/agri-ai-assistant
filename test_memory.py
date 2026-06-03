import os
from crewai import Crew, Agent, Task
import logging

logging.basicConfig(level=logging.INFO)

try:
    print("Testing memory=True without explicit embedder")
    
    agent = Agent(
        role="Test Agent",
        goal="Test",
        backstory="Test",
        verbose=True,
        allow_delegation=False
    )
    
    task = Task(description="Say hi", expected_output="Hi", agent=agent)
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        memory=True
    )
    
    res = crew.kickoff()
    print("Success!", res)
except Exception as e:
    print(f"Error occurred: {e}")
