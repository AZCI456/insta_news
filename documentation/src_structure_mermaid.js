/**
 * Mermaid diagram for the current `src/` directory layout.
 *
 * How to use:
 * 1) Import this string into any script that initializes Mermaid.
 * 2) Render it in an element with class `mermaid`, or pass it to Mermaid's API.
 * 3) Keep this file in sync when folders/files in `src/` change.
 */
export const srcStructureMermaid = `
flowchart TD
    SRC["src/"]
    SRC --> SRC_INIT["__init__.py"]
    SRC --> CONFIG["config.py"]

    SRC --> DATABASE["database/"]
    DATABASE --> DATABASE_INIT["__init__.py"]
    DATABASE --> MANAGER["manager.py"]
    DATABASE --> SCHEMAS["schemas.sql"]
    DATABASE --> MIGRATIONS["migrations/"]

    SRC --> WEB["web/"]
    WEB --> WEB_INIT["__init__.py"]
    WEB --> WEB_MAIN["main.py"]
    WEB --> WEB_REQ["requirements.txt"]
    WEB --> EMAIL_SYSTEM["email_system/"]
    EMAIL_SYSTEM --> EMAIL_SYSTEM_INIT["__init__.py"]
    EMAIL_SYSTEM --> EMAIL_SMTP_CONFIG["email_smtp_config.py"]
    EMAIL_SYSTEM --> EMAIL_UTILITIES["email_utilites.py"]
    WEB --> UTILITIES["utilities/"]
    UTILITIES --> UTILITIES_INIT["__init__.py"]
    UTILITIES --> CREATE_FERNET_KEY["create_fernet_key.py"]
    WEB --> STATIC["static/"]
    STATIC --> THEME["theme.css"]
    WEB --> TEMPLATES["templates/"]
    TEMPLATES --> INDEX_HTML["index.html"]
    TEMPLATES --> MANAGE_HTML["manage.html"]
    TEMPLATES --> MANAGE_INVALID_HTML["manage_invalid.html"]
    TEMPLATES --> QUERY_SCRIPTS["query_scripts.sql"]
    WEB --> ROUTES["routes/"]
    ROUTES --> ROUTES_INIT["__init__.py"]
    ROUTES --> AUTH_ROUTE["auth.py"]
    ROUTES --> DASHBOARD_ROUTE["dashboard.py"]
    ROUTES --> MANAGE_ROUTE["manage.py"]
    WEB --> SERVICES["services/"]
    SERVICES --> SERVICES_INIT["__init__.py"]
    SERVICES --> AUTH_SERVICE["auth_service.py"]
    SERVICES --> EMAIL_SERVICE["email.py"]

    SRC --> ETL["etl/"]
    ETL --> ETL_INIT["__init__.py"]
    ETL --> PROD["prod/"]
    PROD --> PROD_INIT["__init__.py"]
    PROD --> DATA_PATHS["data_paths.py"]
    PROD --> GEMINI_SUMMARISER["gemini_summariser.py"]
    PROD --> INSTA_SCRAPER["insta_scraper_prod.py"]
    PROD --> POST_TIME_WINDOW["post_time_window.py"]
    PROD --> PROMPTS["prompts/"]
    PROMPTS --> PROMPTS_INIT["__init__.py"]
    PROMPTS --> SYSTEM_PROMPTS["system_prompts.py"]
    ETL --> PIPELINES["pipelines/"]
    PIPELINES --> PIPELINES_INIT["__init__.py"]
    ETL --> PROCESSORS["processors/"]
    PROCESSORS --> PROCESSORS_INIT["__init__.py"]

    SRC --> SHARED["shared/"]
    SHARED --> SHARED_INIT["__init__.py"]
`;

/**
 * Tiny helper that wraps the diagram in a mermaid container.
 * This is optional; use it when you want a copy-paste HTML snippet quickly.
 */
export function getSrcStructureMermaidHtml() {
    return `<pre class="mermaid">${srcStructureMermaid}</pre>`;
}
