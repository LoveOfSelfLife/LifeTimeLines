import unittest
from unittest.mock import MagicMock
from common.orchestration.orchestration_executor import OrchestrationExecutor, execute_orchestration
from common.table_store import TableStore
from mock_orch_datastore import MockOrchDataStore
import json
import unittest
from unittest.mock import MagicMock
from common.orchestration.orchestration_executor import OrchestrationExecutor
from mock_orch_datastore import MockOrchDataStore
import json
import os
from dotenv import load_dotenv


class TestOrchestrationExecutor(unittest.TestCase):

    def setUp(self):
        print(f"setUp()")
        load_dotenv('test/.env')
        print(f"{os.getcwd()}")
        print( f"{os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING')}")
        TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

        with open('test/orchestration/test_def_orch_tasks_simple.json', "r") as jfd:
            orch_data = json.load(jfd)

        td = MockOrchDataStore(orch_data['def'], orch_data['orch'], orch_data['tasks']) 
        self.orchestration_executor = OrchestrationExecutor(td, '1707171215')        

    def test_get_combinations(self):
        input = [ { "x" : [1]} , {"y" : [2,3,4] }, {"z" : [6,7,8]} ]
        expected_output =  [{"x":1, "y":2, "z":6 },  
                    {"x":1, "y":2, "z":7 }, 
                    {"x":1, "y":2, "z":8 }, 
                    {"x":1, "y":3, "z":6 }, 
                    {"x":1, "y":3, "z":7 }, 
                    {"x":1, "y":3, "z":8 }, 
                    {"x":1, "y":4, "z":6 }, 
                    {"x":1, "y":4, "z":7 }, 
                    {"x":1, "y":4, "z":8 } ]    

        output = self.orchestration_executor.get_combinations(input)
        self.assertEqual(list(output), expected_output)
        for c in output:
            # print(c)        
            pass

    def test__resolve_vars(self):

        inputs = "$<variable>"
        context = {"variable": "resolved_value"}
        expected_output = ["resolved_value"]
        output = self.orchestration_executor._resolve_vars_with_respect_to_context(inputs, context)

        inputs = { "attr1" : "$<variable>" }
        context = {"variable": "resolved_value"}
        expected_output = [{'attr1': 'resolved_value'}]
        output = self.orchestration_executor._resolve_vars_with_respect_to_context(inputs, context)
        self.assertEqual(list(output), expected_output)

        inputs = { "attr1" : "$<variable>" }
        context = {"variable": [ "resolved_value1", "resolved_value2" ]}
        expected_output = [{'attr1': ['resolved_value1', 'resolved_value2']}]
        output = self.orchestration_executor._resolve_vars_with_respect_to_context(inputs, context)
        self.assertEqual(list(output), expected_output)

        inputs = { "attr1" : "$<[variable]>" }
        context = {"variable": [ "resolved_value1", "resolved_value2" ]}
        expected_output = [{'attr1': 'resolved_value1'}, {'attr1': 'resolved_value2'}]
        output = self.orchestration_executor._resolve_vars_with_respect_to_context(inputs, context)
        self.assertEqual(list(output), expected_output)

        inputs = { "attr1" : "$<[variable]>",
                     "attr2" : "$<variable2>" }
        context = {"variable": [ "resolved_value1", "resolved_value2" ]
                    , "variable2": "resolved_value2" }
        expected_output = [{'attr1': 'resolved_value1', 'attr2': 'resolved_value2'}, {'attr1': 'resolved_value2', 'attr2': 'resolved_value2'}]
        output = self.orchestration_executor._resolve_vars_with_respect_to_context(inputs, context)
        self.assertEqual(list(output), expected_output)

        inputs = { "attr1" : "$<[variable]>",
                     "attr2" : "$<variable2>",
                     "attr3" : "$<variable3>",
                     }
        context = {"variable": [ "resolved_value1", "resolved_value2" ],
                     "variable2": [ "resolved_value2a", "resolved_value2b" ],
                     "variable3": "resolved_value3" }
        expected_output = [{'attr1': 'resolved_value1', 'attr2': ['resolved_value2a', 'resolved_value2b'], 'attr3': 'resolved_value3'}, {'attr1': 'resolved_value2', 'attr2': ['resolved_value2a', 'resolved_value2b'], 'attr3': 'resolved_value3'}]
        output = self.orchestration_executor._resolve_vars_with_respect_to_context(inputs, context)
        self.assertEqual(list(output), expected_output)

        inputs = { "attr1" : "$<[variable]>",
                     "attr2" : "$<[variable2]>",
                     "attr3" : "$<variable3>",
                     }
        context = {"variable": [ "resolved_value1", "resolved_value2" ],
                     "variable2": [ "resolved_value2a", "resolved_value2b" ],
                     "variable3": "resolved_value3" }
        expected_output = [{'attr1': 'resolved_value1', 'attr2': 'resolved_value2a', 'attr3': 'resolved_value3'}, {'attr1': 'resolved_value1', 'attr2': 'resolved_value2b', 'attr3': 'resolved_value3'}, {'attr1': 'resolved_value2', 'attr2': 'resolved_value2a', 'attr3': 'resolved_value3'}, {'attr1': 'resolved_value2', 'attr2': 'resolved_value2b', 'attr3': 'resolved_value3'}]
        output = self.orchestration_executor._resolve_vars_with_respect_to_context(inputs, context)
        self.assertEqual(list(output), expected_output)



    def test_run_orchestration1(self):
        print(f"test_run_orchestration1")
        cmd = {
            "command": "execute",
            # "orch_instance_id": "1707171215",
            "orch_instance_id": "1709007082",
            "arg" : None
        }

        # execute_orchestration(cmd, orch_data=self.orchestration_executor.store)
        execute_orchestration(cmd)
        # with open('test/orchestration/test_def_orch_tasks_simple_output.json', "w") as jfd:
        # with open('test/orchestration/test_def_orch_tasks_simple_ts_output.json', "w") as jfd:
            # print(str(self.orchestration_executor.store), file=jfd)

if __name__ == '__main__':
    unittest.main()
    