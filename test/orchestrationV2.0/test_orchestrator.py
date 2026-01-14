import os
from dotenv import load_dotenv
import unittest
import json
from common.entity_store import EntityStore
from mock_orch_datastore import MockOrchDataStore
from common.orchestration.orchestration_executor import OrchestrationExecutor, execute_orchestration
from common.table_store import TableStore
import sys

# Add the path to the file to the Python path.
sys.path.append('../services')

from common.orchestration.orchestration_utils import OrchTaskDefDataStore, OrchestrationTaskInstance, create_orch2_instances

class TestOrchestrations2(unittest.TestCase):

    def setUp(self) -> None:
        print(f"setUp()")
        load_dotenv('test/.env')
        print(f"current dir: {os.getcwd()}")
        TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
        with open('test_orch2_def.json', "r") as jfd:
            orch_def = json.load(jfd)
        instances = create_orch2_instances(orch_def, {"x": 3, "y":4, "z":5})

        td = MockOrchDataStore(orch_def, instances[0], instances[1:])
        self.exec = OrchestrationExecutor(td, instances[0]['id'])  


    def test_create_root_dict(self):
        task1_instance = self.exec.get_task_instance('task_iterate')
        root = self.exec.create_root_context(task1_instance)
        # print(f"root context: {json.dumps(root, indent=4)}")
        self.assertTrue(True)

    def test_run_orchestration_execute(self):
        print(f"test_run_orchestration1")
        self.exec.execute()
        print(f"final orchestration instance: {json.dumps(self.exec.orch_instance, indent=4)}")
        for task in self.exec.task_instances:
            print(f"final task instance {task['task_id']}: {json.dumps(task, indent=4)}")
        self.assertTrue(True)
    """
    def test_update_status(self):
        print("test_update_status()")
        self.exec.refresh_orch_instance_statuses()
        for task in self.exec.task_instances:
            print(f"task {task['task_id']} status: {task['status']}")

        for step in self.exec.orch_instance['list_of_steps']:
            print(f"step status: {step['status']}")

        print(f"orch instance status: {self.exec.orch_instance['status']}")            
        self.assertTrue(True)

    def test_find_next_task(self):
        
        print("test_find_next_task()")
        task_inst = self.exec.find_next_task_inst_to_run()
        self.assertTrue(True)

    def test_extract_variables(self):
        print("test_extract_variables()")
        tsts = [ '$<var1>', '$<var1.var2>', '$<[ivar1]>', '$<[ivar1.ivar2]>', 'xyz']
        for tst in tsts:
            p = self.exec._extract_var_info(tst)
            print(p)



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
        import common.orchestration.modules.executors        
        call_fn = getattr(common.orchestration.modules.executors, "foo")
        input = {"x": 23, "y":3}
        result =  call_fn(**input)
        print(result)

    def test_run_task1(self):
        print(f"original task1 instance: {self.exec.get_task_instance('task1')}")
        task1_instance = self.exec.get_task_instance('task1')
        self.exec._run_task_instance(task1_instance)
        after = self.exec.get_task_instance('task1')
        print(f"after running task1: {json.dumps(after, indent=4)}")


    def test_run_task1_task2(self):
        print(f"original task1 instance: {self.exec.get_task_instance('task1')}")
        task1_instance = self.exec.get_task_instance('task1')
        self.exec._run_task_instance(task1_instance)
        after1 = self.exec.get_task_instance('task1')
        print(f"after running task1: {json.dumps(after1, indent=4)}")
        task2_instance = self.exec.get_task_instance('task2')
        self.exec._run_task_instance(task2_instance)
        after2 = self.exec.get_task_instance('task2')
        print(f"after running task2: {json.dumps(after2, indent=4)}")

    def test_run_orchestration1(self):
        print(f"test_run_orchestration1")
        cmd = {
            "command": "execute",
            "orch_instance_id": "1707171215",
            "arg" : None
        }

        execute_orchestration(cmd, orch_data=self.exec.store)
    """        
if __name__ == '__main__':
    unittest.main()
