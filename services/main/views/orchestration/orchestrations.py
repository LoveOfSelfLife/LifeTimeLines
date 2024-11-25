from common.entity_filter import Filter
from common.orchestration.orchestration_utils import OrchestrationCommand, OrchestrationTaskInstance, OrchestrationDefinition
from common.entity_store import EntityStore

def get_orchestration_definitions(def_id: str = None):

    es = EntityStore()
    if def_id:
        res = es.get_item(OrchestrationDefinition({"id":def_id}))
    else:
        res = list(es.list_items(OrchestrationDefinition()))

    return res


def get_orchestration_instances(orch_def_id: str = None):

    es = EntityStore()

    filters = [ Filter("definition_id", orch_def_id) ] if orch_def_id else []
    res = es.list_items2(OrchestrationTaskInstance(),dfilter=filters)

    return list(res)
