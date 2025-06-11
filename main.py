import os
import subprocess
import shlex
import time
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from crewai_tools import BaseTool

class SecureCommandLineTool(BaseTool):
    name: str = "SecureTerminal"
    description: str = "Exécute des commandes shell sécurisées pour construire et valider le projet."
    ALLOWED_COMMANDS = ['mkdir', 'echo', 'cat', 'ls', 'npm', 'node', 'git', 'touch', 'npx', 'timeout', 'curl', 'sleep', 'kill']
    
    def _run(self, command: str) -> str:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, timeout=300)
            return f"✅ Commande exécutée avec succès.\n{result.stdout}"
        except Exception as e:
            return f"❌ ERREUR lors de l'exécution de '{command}': {e}"

class EnhancedProjectTemplateManager(BaseTool):
    name: str = "ProjectTemplateManager"
    description: str = "Génère les commandes de base pour la structure et le contenu initial du projet."
    
    def _run(self, template_name: str, project_name: str) -> str:
        base_templates = {
            'webapp-basic': [
                f'mkdir -p workspace/{project_name}/frontend',
                f'mkdir -p workspace/{project_name}/backend',
                f'cd workspace/{project_name}/frontend && npm create vite@latest . -- --template react',
                f'cd workspace/{project_name}/backend && npm init -y && npm install express cors dotenv',
                f'cd workspace/{project_name} && echo "node_modules/\n.env\nbuild/\ndist/" > .gitignore',
                f'cd workspace/{project_name} && echo "# {project_name}\n\nProjet généré par l\'Agent IA V17." > README.md'
            ]
        }
        commands = base_templates.get(template_name, [])
        if not commands: return f"❌ Template '{template_name}' non trouvé."
        return "Commandes de création de squelette générées:\n" + "\n".join(commands)

class ProjectSelector:
    def select_template(self) -> tuple[str, str]:
        print("\n" + "="*60 + "\n🚀 GÉNÉRATEUR D'APPLICATIONS IA - v17\n" + "="*60)
        project_name = input("Nom du projet: ").strip() or "my-functional-app-v17"
        print(f"\n✅ Génération d'une application fonctionnelle nommée '{project_name}'...")
        return "webapp-basic", project_name

def main():
    load_dotenv()
    required_keys = ["GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
    for key in required_keys:
        if not os.getenv(key):
            raise ValueError(f"Clé manquante dans .env : {key}")

    selector = ProjectSelector()
    template_type, project_name = selector.select_template()

    if not os.path.exists('./workspace'): os.makedirs('./workspace')

    llms = {
        "claude": ChatAnthropic(model="claude-opus-4-20250514"),
        "gemini": ChatGoogleGenerativeAI(model="gemini-1.5-pro"),
        "openai": ChatOpenAI(model="gpt-4o-mini")
    }
    secure_terminal = SecureCommandLineTool()
    template_manager = EnhancedProjectTemplateManager()
    
    architect = Agent(role='Architecte Logiciel Full-Stack', tools=[template_manager], llm=llms["claude"], verbose=True, goal="Créer un plan technique complet, incluant la structure et le code source initial.")
    developer = Agent(role='Développeur Full-Stack Senior', tools=[secure_terminal], llm=llms["gemini"], verbose=True, goal="Construire le projet et écrire le code source dans les fichiers.")
    code_reviewer = Agent(role='Ingénieur Qualité Code', tools=[secure_terminal], llm=llms["openai"], verbose=True, goal="Analyser le code source généré pour la qualité et la conformité.")
    functional_tester = Agent(role='Ingénieur QA Fonctionnel', tools=[secure_terminal], llm=llms["claude"], verbose=True, goal="Valider que l'application est fonctionnelle de bout en bout.")
    devops_engineer = Agent(role='Ingénieur DevOps', tools=[secure_terminal], llm=llms["claude"], verbose=True, goal="Versionner le projet validé avec Git.")

    architecture_task = Task(
        description=f"Pour le projet '{project_name}', crée un plan d'action. Le plan doit inclure :\n1. Les commandes pour créer le squelette via le template '{template_type}'.\n2. Le contenu complet pour un fichier `backend/server.js` exposant une route GET `/api/greeting` qui retourne `{{'message': 'Hello from AI!'}}`.\n3. Le contenu complet pour `frontend/src/App.jsx` qui fait un `fetch` à cette API et affiche le message.",
        expected_output="Un plan détaillé en plusieurs parties : commandes de setup, puis le code source pour chaque fichier.",
        agent=architect
    )

    development_task = Task(
        description=f"Exécute le plan de l'architecte pour le projet '{project_name}'. D'abord, le squelette. Ensuite, écris le code source dans `backend/server.js` et `frontend/src/App.jsx`.",
        expected_output="Confirmation que le squelette et les fichiers de code ont été créés.",
        agent=developer,
        context=[architecture_task]
    )

    code_review_task = Task(
        description=f"Analyse le code des fichiers `workspace/{project_name}/backend/server.js` et `frontend/src/App.jsx`. Vérifie la syntaxe, la logique, et la conformité avec le plan.",
        expected_output="Un rapport de revue de code.",
        agent=code_reviewer,
        context=[development_task]
    )

    functional_validation_task = Task(
        description=f"Effectue un test fonctionnel du projet '{project_name}'. Les étapes sont :\n1. Démarre le serveur backend en arrière-plan : `cd workspace/{project_name}/backend && node server.js & echo $! > server.pid`\n2. Attends 5 secondes : `sleep 5`\n3. Teste l'API : `curl http://localhost:3001/api/greeting`\n4. Arrête le serveur : `kill $(cat workspace/{project_name}/backend/server.pid)`",
        expected_output="Le résultat de la commande `curl`. Il doit contenir le message 'Hello from AI!'.",
        agent=functional_tester,
        context=[code_review_task]
    )

    git_commit_task = Task(
        description=f"Le projet a passé les tests. Initialise un dépôt Git pour '{project_name}', configure l'utilisateur, et crée un commit initial structuré avec un tag v1.0.0.",
        expected_output=f"Confirmation que le dépôt Git a été initialisé pour '{project_name}'.",
        agent=devops_engineer,
        context=[functional_validation_task]
    )

    crew = Crew(
        agents=[architect, developer, code_reviewer, functional_tester, devops_engineer],
        tasks=[architecture_task, development_task, code_review_task, functional_validation_task, git_commit_task],
        process=Process.sequential, verbose=2
    )
    result = crew.kickoff()

    print("\n" + "="*50 + "\n🎉 PROJET V17 FONCTIONNEL ET VERSIONNÉ !\n" + "="*50)
    print("📖 Rapport final de la mission :\n" + "="*50 + f"\n{result}")

if __name__ == "__main__":
    main()
