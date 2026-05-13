from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from .tools.custom_tool import FerramentaAnaliseImagem 

@CrewBase
class BioStatusIACrew():
    """Equipe de Agentes do BioStatusIA"""
    
    # Define o modelo local via Ollama
    llm_local = "ollama/llama3.1"

    @agent
    def analista_tecnico(self) -> Agent:
        return Agent(
            config=self.agents_config['analista_tecnico'],
            tools=[FerramentaAnaliseImagem()], 
            llm=self.llm_local,
            verbose=True,
            # Limita a 3 tentativas de uso da ferramenta para evitar loops
            max_iter=3, 
            allow_delegation=False
        )

    @agent
    def radiologista_ia(self) -> Agent:
        return Agent(
            config=self.agents_config['radiologista_ia'],
            llm=self.llm_local,
            verbose=True,
            # Limita a 2 tentativas de raciocínio para ser mais direto
            max_iter=2, 
            allow_delegation=False
        )

    @task
    def tarefa_extracao(self) -> Task:
        return Task(
            config=self.tasks_config['tarefa_extracao'],
            agent=self.analista_tecnico()
        )

    @task
    def tarefa_laudo(self) -> Task:
        return Task(
            config=self.tasks_config['tarefa_laudo'],
            agent=self.radiologista_ia()
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )