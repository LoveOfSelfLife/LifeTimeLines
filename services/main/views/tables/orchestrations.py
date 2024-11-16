from common.entity_filter import Filter
from common.orchestration.orchestration_utils import OrchestrationCommand, OrchestrationTaskInstance, OrchestrationDefinition
from common.entity_store import EntityStore

def get_orchestration_definitions():

    es = EntityStore()
    res = es.list_items(OrchestrationDefinition())

    return list(res)


def get_orchestration_instances(orch_def_id: str = None):

    es = EntityStore()

    filters = [ Filter("definition_id", orch_def_id) ] if orch_def_id else []
    res = es.list_items2(OrchestrationTaskInstance(),dfilter=filters)

    return list(res)
