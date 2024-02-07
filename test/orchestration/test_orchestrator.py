import os
from dotenv import load_dotenv
import unittest
import json
from common.entity_store import EntityStore
from common.orchestration.orchestration_executor import OrchestrationExecutor
from common.table_store import TableStore
import sys

# Add the path to the file to the Python path.
sys.path.append('../services')

import common.orchestration.executors as ex
from common.orchestration.orchestration_utils import OrchTaskDefStore, OrchestrationTaskInstance, TestingStore
from common.orchestration.orchestration_utils import OrchestrationDefinition
from services.otex.orchestration_runner import find_next_task_to_exec, advance_orchestration

class TestOrchestrations(unittest.TestCase):

    def setUp(self) -> None:
        print(f"setUp()")
        load_dotenv('test/.env')
        print(f"{os.getcwd()}")
        TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

        with open('test/orchestration/test_def_orch_tasks.json', "r") as jfd:
            orch_data = json.load(jfd)

        td = TestingStore(orch_data['def'], orch_data['orch'], orch_data['tasks']) 
        self.exec = OrchestrationExecutor(td, '1707171215')
        return super().setUp()

    def test_TestingStore(self):
        print(f"test_TestingStore")
        ostore = OrchTaskDefStore()
        d,o,t = ostore.get_orch_data("1707171215")
        s = json.dumps({"def" : d, "orch" : o, "tasks" : t}, indent=4)
        print(s)
        self.assertTrue(True)

    def test_find_next_task(self):
        
        print("test_find_next_task()")
        task_inst = self.exec.find_next_task_inst_to_run()
        self.assertTrue(True)

    def test_extract_variables(self):
        print("test_extract_variables()")
        tsts = [ '$<var1>', '$<var1.var2>', '$<[ivar1]>', '$<[ivar1.ivar2]>', 'xyz']
        for tst in tsts:
            p = self.exec.extract_var(tst)
            print(p)

    def test_create_root_dict(self):
        task1_instance = self.exec.get_task_instance('task1')
        root = self.exec.create_root_dict(task1_instance)
        print(root)

    def test_create_inputs_dict(self):
        print("test_create_inputs_dict()")

        print(f"original task1 instance: {self.exec.get_task_instance('task1')}")
        task1_instance = self.exec.get_task_instance('task1')
        task1_instance['output']=[{"start":"20210104", "end":"20210401"}, {"start":"20220104", "end":"20220401"}, {"start":"20230104", "end":"20230401"}]
        self.exec.persist(task1_instance)
        print(f"updated task1 instance: {self.exec.get_task_instance('task1')}")

        for inp in self.exec.create_inputs_for_task(self.exec.get_task_instance('task2')):
            print(inp)



    def test_call_executor_function(self):
        import common.orchestration.executors        
        call_fn = getattr(common.orchestration.executors, "foo")
        input = {"x": 23, "y":3}

        result =  call_fn(**input)
        
        print(result)

    def test_run_task1(self):
        print(f"original task1 instance: {self.exec.get_task_instance('task1')}")
        task1_instance = self.exec.get_task_instance('task1')
        self.exec.run_task_instance(task1_instance)
        after = self.exec.get_task_instance('task1')
        print(f"after running task1: {json.dumps(after, indent=4)}")


    def test_run_task1_task2(self):
        print(f"original task1 instance: {self.exec.get_task_instance('task1')}")
        task1_instance = self.exec.get_task_instance('task1')
        self.exec.run_task_instance(task1_instance)
        after1 = self.exec.get_task_instance('task1')
        print(f"after running task1: {json.dumps(after1, indent=4)}")
        task2_instance = self.exec.get_task_instance('task2')
        self.exec.run_task_instance(task2_instance)
        after2 = self.exec.get_task_instance('task2')
        print(f"after running task2: {json.dumps(after2, indent=4)}")
        
if __name__ == '__main__':
    unittest.main()
