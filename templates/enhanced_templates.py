from crewai_tools import BaseTool

class EnhancedTemplateManager(BaseTool):
    """Provide commands for specialized project scaffolding."""

    name: str = "EnhancedTemplateManager"
    description: str = "Génère des commandes de structure pour des templates spécialisés."

    def _run(self, template_name: str, project_name: str) -> str:
        templates = {
            "fishing-platform": [
                f"mkdir -p workspace/{project_name}/frontend",
                f"mkdir -p workspace/{project_name}/backend",
                f"cd workspace/{project_name}/frontend && npm create vite@latest . -- --template react",
                f"cd workspace/{project_name}/backend && npm init -y && npm install express cors dotenv",
                f"cd workspace/{project_name}/backend && npm install leaflet",
            ],
            "ecommerce-stripe": [
                f"mkdir -p workspace/{project_name}/frontend",
                f"mkdir -p workspace/{project_name}/backend",
                f"cd workspace/{project_name}/frontend && npm create vite@latest . -- --template react",
                f"cd workspace/{project_name}/backend && npm init -y && npm install express cors dotenv stripe",
            ],
            "blog-seo": [
                f"mkdir -p workspace/{project_name}/frontend",
                f"mkdir -p workspace/{project_name}/backend",
                f"cd workspace/{project_name}/frontend && npm create vite@latest . -- --template react",
                f"cd workspace/{project_name}/backend && npm init -y && npm install express cors dotenv",
                f"cd workspace/{project_name}/frontend && npm install react-helmet",
            ],
            "realtime-chat": [
                f"mkdir -p workspace/{project_name}/frontend",
                f"mkdir -p workspace/{project_name}/backend",
                f"cd workspace/{project_name}/frontend && npm create vite@latest . -- --template react",
                f"cd workspace/{project_name}/backend && npm init -y && npm install express cors dotenv socket.io",
            ],
        }
        commands = templates.get(template_name)
        if not commands:
            return f"❌ Template '{template_name}' non trouvé."
        return "\n".join(commands)
