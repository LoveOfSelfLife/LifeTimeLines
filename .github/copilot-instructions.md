# LifeTimeLines AI Coding Instructions

## System Architecture

This is a **microservices-based fitness tracking platform** using Flask apps deployed as Azure Container Apps. The system follows a modular architecture with shared domain logic.

### Key Components
- **`/services/`** - Individual Flask microservices (fitnessclub, entities, photos, etc.)
- **`/common/`** - Shared business logic, entity framework, and utilities
- **`/common/orchestration/`** - Workflow orchestration system for complex multi-step operations
- Each service uses `appfactory.py` pattern for Flask app creation with blueprint registration

### Critical Patterns

**Entity Framework**: All data models inherit from `EntityObject` in `common/entity_store.py`. Entities are stored in Azure Table Storage with:
- `table_name`, `key_field`, `partition_field` class attributes
- Registry pattern: `entity_name_to_entity_class_map` for dynamic class lookup
- Example: Exercise entities use fitness-specific filters in `common/fitness/`

**Authentication**: Every service uses `@auth.login_required` decorator with Azure B2C integration via `common/jwt_auth.py`

**Environment**: All config comes through `common/env_context.py` - always use `Env.VARIABLE_NAME` pattern, never direct `os.getenv()`

## Development Workflows

**Local Development**: 
- Use VS Code tasks: `docker-build` then `docker-run: debug` 
- Services run on port 5002 with Flask debug mode
- Redis cache defaults to `localhost` when `ORCH_TESTING_MODE` is set

**Docker**: Services use parameterized Dockerfile at `/services/Dockerfile` with `ARG app` for service selection

**Deployment**: Path-based GitHub Actions trigger on `services/{service}/**` changes using reusable workflow `_build_deploy_containerapp_image.yml`

## Service-Specific Conventions

**Flask Blueprint Pattern**: Each service organizes routes as:
```python
# In views/{domain}/{domain}_routes.py
bp = Blueprint('domain', __name__, template_folder='templates')
@bp.route('/endpoint')
@auth.login_required
def handler(context=None):
```

**HTMX Integration**: Many routes check `request.headers.get('HX-Target')` to return partial templates for SPA-like experience

**Session Management**: Uses Redis-backed sessions with 90-day lifetime via `cachelib.RedisCache`

## Data Flow Patterns

**Entity Filtering**: Use registry pattern in `common/fitness/active_fitness_registry.py`:
- `get_fitnessclub_entity_filters_for_entity(entity_name)` 
- `get_filtered_entities()` for consistent pagination/filtering

**Orchestration**: For multi-step workflows, use `OrchestrationExecutor` with JSON-defined steps and dynamic module loading

## Integration Points

- **Azure Table Storage**: All persistent data via `common/table_store.py`
- **Redis**: Session store and caching (hostname: `rediscache` in containers, `localhost` locally)
- **Azure B2C**: Authentication tokens validated in every protected endpoint
- **Google Drive**: Integration via `common/google_drive.py` for file operations

## Testing & Debugging

Set `ORCH_TESTING_MODE=1` for local development to use localhost services instead of container hostnames.

Critical files to understand before making changes:
- `common/entity_store.py` - Data model base class
- `common/env_init.py` - Environment bootstrapping
- Service-specific `appfactory.py` - Blueprint registration and app config