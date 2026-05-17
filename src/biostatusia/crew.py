import os

from dotenv import load_dotenv

load_dotenv()

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task

from .tools.analise_base_tool import FerramentaAnaliseBase
from .tools.extracao_tool import FerramentaExtrairBiomarcadores
from .tools.tabular_tool import FerramentaAnaliseTabular
from .tools.treino_tool import FerramentaTreinarClassificador


def _llm() -> LLM:
    """LLM local via Ollama — formato obrigatório: 'ollama/<modelo>'."""
    return LLM(
        model=os.getenv("MODEL", "ollama/qwen2.5:3b"),
        base_url=os.getenv("API_BASE", "http://localhost:11434"),
        temperature=0.1,
    )


@CrewBase
class BioStatusIACrew:
    """Equipe de Agentes do BioStatusIA (fluxo completo de imagem):
    engenheiro_pdi → analista_tecnico → cientista_dados → radiologista_ia."""

    @agent
    def engenheiro_pdi(self) -> Agent:
        return Agent(
            config=self.agents_config["engenheiro_pdi"],
            tools=[FerramentaAnaliseBase()],
            llm=_llm(),
            verbose=True,
            max_iter=5,
            max_retry_limit=3,
            allow_delegation=False,
        )

    @agent
    def analista_tecnico(self) -> Agent:
        return Agent(
            config=self.agents_config["analista_tecnico"],
            tools=[FerramentaExtrairBiomarcadores()],
            llm=_llm(),
            verbose=True,
            max_iter=5,
            max_retry_limit=3,
            allow_delegation=False,
        )

    @agent
    def cientista_dados(self) -> Agent:
        return Agent(
            config=self.agents_config["cientista_dados"],
            tools=[FerramentaTreinarClassificador()],
            llm=_llm(),
            verbose=True,
            max_iter=5,
            max_retry_limit=3,
            allow_delegation=False,
        )

    @agent
    def radiologista_ia(self) -> Agent:
        return Agent(
            config=self.agents_config["radiologista_ia"],
            llm=_llm(),
            verbose=True,
            max_iter=5,
            max_retry_limit=3,
            allow_delegation=False,
        )

    @task
    def tarefa_analise_base(self) -> Task:
        return Task(
            config=self.tasks_config["tarefa_analise_base"],
            agent=self.engenheiro_pdi(),
        )

    @task
    def tarefa_extracao(self) -> Task:
        return Task(
            config=self.tasks_config["tarefa_extracao"],
            agent=self.analista_tecnico(),
        )

    @task
    def tarefa_treinar_classificador(self) -> Task:
        return Task(
            config=self.tasks_config["tarefa_treinar_classificador"],
            agent=self.cientista_dados(),
        )

    @task
    def tarefa_laudo(self) -> Task:
        return Task(
            config=self.tasks_config["tarefa_laudo"],
            agent=self.radiologista_ia(),
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.engenheiro_pdi(),
                self.analista_tecnico(),
                self.cientista_dados(),
                self.radiologista_ia(),
            ],
            tasks=[
                self.tarefa_analise_base(),
                self.tarefa_extracao(),
                self.tarefa_treinar_classificador(),
                self.tarefa_laudo(),
            ],
            process=Process.sequential,
            verbose=True,
        )


@CrewBase
class BioStatusIACrewTabular:
    """Equipe de Agentes do BioStatusIA (fluxo tabular — CSV/TXT)."""

    @agent
    def bioestatistico(self) -> Agent:
        return Agent(
            config=self.agents_config["bioestatistico"],
            tools=[FerramentaAnaliseTabular()],
            llm=_llm(),
            verbose=True,
            max_iter=5,
            max_retry_limit=3,
            allow_delegation=False,
        )

    @task
    def tarefa_laudo_tabular(self) -> Task:
        return Task(
            config=self.tasks_config["tarefa_laudo_tabular"],
            agent=self.bioestatistico(),
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.bioestatistico()],
            tasks=[self.tarefa_laudo_tabular()],
            process=Process.sequential,
            verbose=True,
        )
