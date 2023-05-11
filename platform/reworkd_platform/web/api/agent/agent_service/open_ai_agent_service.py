from os import environ
from typing import List, Optional

from langchain.chains import LLMChain

from reworkd_platform.web.api.agent.agent_service.agent_service import AgentService
from reworkd_platform.web.api.agent.analysis import Analysis, get_default_analysis
from reworkd_platform.web.api.agent.helpers import extract_tasks
from reworkd_platform.web.api.agent.model_settings import ModelSettings, create_model
from reworkd_platform.web.api.agent.prompts import (
    start_goal_prompt,
    analyze_task_prompt,
    execute_task_prompt,
    create_tasks_prompt,
)
from reworkd_platform.web.api.agent.tools.tools import get_tools_overview


class OpenAIAgentService(AgentService):
    async def start_goal_agent(
        self, model_settings: ModelSettings, goal: str, language: str
    ) -> List[str]:
        llm = create_model(model_settings)
        chain = LLMChain(llm=llm, prompt=start_goal_prompt)

        completion = chain.run({"goal": goal, "language": language})
        print(f"Goal: {goal}, Completion: {completion}")
        return extract_tasks(completion, [])

    async def analyze_task_agent(
        self, model_settings: ModelSettings, goal: str, task: str
    ) -> Analysis:
        llm = create_model(model_settings)
        chain = LLMChain(llm=llm, prompt=analyze_task_prompt)

        completion = chain.run(
            {"goal": goal, "task": task, "tools_overview": get_tools_overview()}
        )

        print("Analysis completion:\n", completion)
        try:
            return Analysis.parse_raw(completion)
        except Exception as error:
            print(f"Error parsing analysis: {error}")
            return get_default_analysis()

    async def execute_task_agent(
        self,
        model_settings: ModelSettings,
        goal: str,
        language: str,
        task: str,
        analysis: Analysis,
    ) -> str:
        print("Execution analysis:", analysis)

        if analysis.action == "search" and environ.get("SERP_API_KEY"):
            # Implement SERP API call using Serper class if available
            pass

        llm = create_model(model_settings)
        chain = LLMChain(llm=llm, prompt=execute_task_prompt)

        completion = chain.run({"goal": goal, "language": language, "task": task})

        if analysis.action == "search" and not environ.get("SERP_API_KEY"):
            return (
                f"ERROR: Failed to search as no SERP_API_KEY is provided in ENV."
                f"\n\n{completion}"
            )
        return completion

    async def create_tasks_agent(
        self,
        model_settings: ModelSettings,
        goal: str,
        language: str,
        tasks: List[str],
        last_task: str,
        result: str,
        completed_tasks: Optional[List[str]] = None,
    ) -> List[str]:
        llm = create_model(model_settings)
        chain = LLMChain(llm=llm, prompt=create_tasks_prompt)

        completion = chain.run(
            {
                "goal": goal,
                "language": language,
                "tasks": tasks,
                "lastTask": last_task,
                "result": result,
            }
        )

        return extract_tasks(completion, completed_tasks or [])
