
from common.orchestration.orchestration_utils import AbstratctOrchDataStore

import copy
import json

class TestOrchDataStore (AbstratctOrchDataStore):
    def __init__(self, definition, orch_instance, task_instances):
        self.definition = definition
        self.orch_instance = [ orch_instance ]
        self.task_instances = {}
        for task in task_instances:
            self.task_instances[task['task_id']] = [ task ]

    def get_orch_data(self, orch_instance_id):
        return self.definition, copy.deepcopy(self.orch_instance[-1]), [ copy.deepcopy(t[-1]) for t in self.task_instances.values()]

    def persist_instance(self, instance):
        if instance['is_parent']:
            self.orch_instance.append(instance)
        else:
            self.task_instances[instance['task_id']].append(instance)

    def get_all_orch_data(self, orch_instance_id):
        return self.definition, self.orch_instance, [ t for t in self.task_instances.values()]

    def __str__(self):
        d,o,t = self.get_orch_data(None)
        d,o_all,t_all = self.get_all_orch_data(None)

        return json.dumps({"latest" : { "instances" :  o,
                                        "tasks" : t},
                            "all": { "instances" :  o_all,
                                    "tasks" : t_all},
                }, indent=4)
    