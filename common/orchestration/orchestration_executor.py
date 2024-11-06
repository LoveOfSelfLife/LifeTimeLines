import copy
import re
import os
from datetime import datetime
import itertools
from common.orchestration.orchestration_utils import OrchTaskDefDataStore
import logging
import importlib

def execute_orchestration(orch_cmd, orch_data=None, token=None, executors=None):
    """this method will execute the indicated orchestration command
    auth token is required for the execution of the orchestration
    the orchestration command will be executed in the context of the provided orchestration data
    the orchestration data will be updated as the orchestration progresses"""

    command = orch_cmd.get('command', 'execute')
    orch_instance_id = orch_cmd.get('orch_instance_id', None)

    if orch_data is None:
        orch_data_store = OrchTaskDefDataStore()
    else:
        orch_data_store = orch_data

    executor = OrchestrationExecutor(data_store=orch_data_store, orch_instance_id=orch_instance_id, token=token, executors=executors)

    if command == "execute":
        for step_id in executor.get_steps():
            step_status = executor.get_step_status(step_id)
            # print(f'step_id: {step_id}, step_status: {step_status}')

            if step_status == "not_started" or step_status == "in_progress":
                logging.info(f'step_id: {step_id} with step_status: {step_status} has not started or is in progress, so we will run all unfinished tasks in the step')
                run_tasks_in_step_status = executor.run_all_unfinished_tasks_in_step(step_id)
            elif step_status == "completed":
                logging.info(f'step_id: {step_id} with step_status: {step_status} has completed, so we will move to the next step')
                continue
            else:
                logging.info(f'step_id: {step_id} with step_status: {step_status} has failed tasks, so cannot finish the step')
                # print(f'step_id: {step_id} has failed tasks, so cannot finish the step')
                return False
    elif command == "rerun_all_in_step":
        step_id = orch_cmd.get("step_id", None)
        if step_id:
            logging.info(f'command: {command}, step_id: {step_id}')
            executor.refresh_orch_instance_from_storage()
            executor.run_all_tasks_in_step(step_id)
        else:
            logging.info(f'command: {command}, step_id: {step_id} not recognized')
            return False
    elif command == "rerun_unfinished_in_step":
        step_id = orch_cmd.get("step_id", None)
        if step_id:
            logging.info(f'command: {command}, step_id: {step_id}')
            executor.refresh_orch_instance_from_storage()
            executor.run_all_unfinished_tasks_in_step(step_id)
        else:
            logging.info(f'command: {command}, step_id: {step_id} not recognized')
            return False
    elif command == "run_task_in_step":
        step_id = orch_cmd.get("step_id", None)
        task_id = orch_cmd.get("task_id", None)
        if step_id and task_id:
            logging.info(f'command: {command}, step_id: {step_id}, task_id: {task_id} ')
            executor.refresh_orch_instance_from_storage()
            executor.run_task_in_step(step_id, task_id)
        else:
            logging.info(f'command: {command}, step_id: {step_id}, task_id: {task_id} not recognized')
            return False
    else:
        logging.info(f'command: {command} not recognized')
        return False
    return True


class OrchestrationExecutor:
    """
    Class representing an orchestration executor.

    Each of the task instances will hold their current status. 
    We need to look at the orch definition along with the statuses of the tasks in order to identify the next task that needs to run. 
    
hen before attempting to execute the instance, we check the counter to verify it hasn't exceeded a threshold

    TODO: Need a test harness for the message queue, to simulate the flow locally.

    Once that task has been identified, we should run it. 
    To tun the task we:
    1. get the task definition from the orchestration template
    2. prepare the inputs to the task by substituting values for any variables defined as part of the input to the task
    3. change the status of the task from "not-stared" to "started" and persist
    4. invoke the function that has been identified as the proxy for the task, passing in the input that was just prepared (step #2)
    5. For simple tasks:
        5.a. wait for the function to complete, and then after it completes, we capture the return value of the function
        5.b. set the output attribute of the task instance to the value returned from the function
        5.c  set the status of the task instance based on the function (if exception thrown, then status is failed, othewise it is completed)
    6. For iterator tasks:
        6.a. we need to invoke the task once for every element in the input iterator. 
        6.b. need to decide if we persist the result after each step in the iteration, or wait till the iteration i scomplete.
         6.c. set the status of the result to something that represents the status from all of the executions of the iteration
    7. then persist the task isntance, and then  proceed as indicated at the top level, which is either to:
        7.a. post the next orchestration request message to the task execution message quewue, or 
        7.b. we should proceed to execute the next task, until the desired number of tasks is done
            
    Args:
        data_store: The data store object.
        orch_instance_id: The ID of the orchestration instance.

    Attributes:
        store: The data store object.
        orch_definition: The orchestration definition.
        orch_instance: The orchestration instance.
        task_instances: The task instances.

    Methods:
        find_next_task_inst_to_run: Finds the next task instance to run.
        test_if_iterator: Tests if an expression string represents an iterator.
        extract_var: Extracts the variable name from an expression string.
        resolve: Resolves an expression string by extracting the variable path and checking if it is iterable.
        create_root_dict: Creates a root dictionary for the orchestration.
        get_task_def: Gets the task definition for a task instance.
        get_task_instance: Gets a task instance by task definition ID.
        create_inputs_for_task: Creates inputs for a task instance.
        invoke_function: Invokes a function with the given input.
        get_function: Gets the function to be invoked for a task instance.
        persist: Persists an instance.
        run_task_instance: Runs a task instance.
    """
    def __init__(self, data_store, orch_instance_id, token=None, executors=None):
        """_summary_

        Args:
            data_store (_type_): _description_
            orch_instance_id (_type_): _description_
            token (_type_, optional): _description_. Defaults to None.
            executors (_type_, optional): _description_. Defaults to None.
        """
        self.store = data_store
        self.orch_definition, self.orch_instance, self.task_instances = self.store.get_orch_data(orch_instance_id)
        self.token = token
        self.executors=executors

    def get_steps(self):
        for step in self.orch_definition['flow']:
            yield step['step_id']
    
    def get_step_status(self, step_id):
        step = next((s for s in self.orch_definition['flow'] if s['step_id'] == step_id), None)
        task_statuses = [self.get_task_status(t) for t in step['tasks']]
        return self.aggregate_status(task_statuses)

    def run_all_tasks_in_step(self, step_id):
        step = next((s for s in self.orch_definition['flow'] if s['step_id'] == step_id), None)
        for task_id in step['tasks']:
            task_inst = next((t for t in self.task_instances if t['task_id'] == task_id), None)
            if task_inst:
                self.run_task_instance(task_inst)

    def run_all_unfinished_tasks_in_step(self, step_id):
        step = next((s for s in self.orch_definition['flow'] if s['step_id'] == step_id), None)
        for task_id in step['tasks']:
            task_inst = next((t for t in self.task_instances if t['task_id'] == task_id), None)
            if task_inst and task_inst['status'] != "completed":
                self.run_task_instance(task_inst)   

    def run_task_in_step(self, step_id, task_id):
        step = next((s for s in self.orch_definition['flow'] if s['step_id'] == step_id), None)
        if task_id in step['tasks']:
            task_inst = next((t for t in self.task_instances if t['task_id'] == task_id), None)
            if task_inst:
                logging.info(f"running task: {task_id} in step: {step_id}")
                self.run_task_instance(task_inst)
        else:
            logging.info(f"task: {task_id} not found in step: {step_id} - raising exception")
            raise Exception(f"task: {task_id} not found in step: {step_id}")
        
    def validate_definition(self):
        pass

    def get_task_status(self, task_id):
        task = next((t for t in self.task_instances if t['task_id'] == task_id), None)
        return task['status']
    
    def find_next_step_to_run(self):
        for step in self.get_steps():
            step_status = self.get_step_status(step['step_id'])
            if step_status == "not_started" or step_status == "in_progress":
                return step
        return None
    
    def refresh_orch_instance_from_storage(self):
        self.orch_definition, self.orch_instance, self.task_instances = self.store.get_orch_data(self.orch_instance['id'])
        return self.orch_instance

    def refresh_orch_instance_statuses(self):
        """this method will refresh the statuses of all the steps in the orchestration instance
        and it will also update the status of the orchestration instance itself, based on the statuses of the steps
,
        "step_status":
            {
                "step_once" :   "not_started",
                "step_iterate" : "not_started",
                "step_repeat" : "not_started"
            }        
        """
        step_statuses = { step['step_id'] : self.get_step_status(step['step_id']) for step in self.orch_definition['flow'] }
        self.orch_instance['step_status'] = step_statuses
        self.orch_instance['status'] = self.aggregate_status(step_statuses.values())
        self.persist(self.orch_instance)
    
    def aggregate_status(self, statuses):
        if all(s == "not_started" for s in statuses):
            return "not_started"
        elif all(s == "completed" for s in statuses):
            return "completed"
        elif any(s == "failed" for s in statuses):
            return "failed"
        else:
            return "in_progress"
        
    def find_next_task_inst_to_run(self):
        flow = self.orch_definition['flow']
        task = None
        task_inst = None
        for step in flow:
            for taskid in step['tasks']:
                task_inst = next((t for t in self.task_instances if t['status'] == 'not_started'), None)
                if not task_inst:
                    continue
        return task_inst

    def set_step_status(self, step, status):
        for taskid in step['tasks']:
            task_inst = next((t for t in self.task_instances if t['task_id'] == taskid), None)
            if task_inst:
                task_inst['status'] = status
                self.persist(task_inst)

    def test_if_iterator(self, expression_str):
        _, is_iter = self.extract_var(expression_str)
        return is_iter
    
    def is_expression_a_variable(self, expression):
        return re.match(r'\$<.*>', str(expression))
    
    def extract_var(self, expression_str):
            """
            Extracts the variable name from the given expression string.

            Args:
                expression_str (str): The expression string containing the variable.

            Returns:
                tuple: A tuple containing the variable path (list of strings) and a boolean indicating if it is an iterator.
                       If the variable is not found, the original expression string is returned along with None.
            """
            var = None
            is_iterator = False
            PAT_ITERATOR =  r'\$<\[(.*)\]>'
            PAT_SINGLE =  r'\$<(.*)>'
            m = re.match(PAT_ITERATOR, str(expression_str))
            if m:
                var = m.group(1)
                is_iterator = True
            else:
                m = re.match(PAT_SINGLE, str(expression_str))
                if m:
                    var = m.group(1)
            if var:
                path = var.split('.')
                return { "path": path, "is_iterator" : is_iterator, "is_variable" : True }
            else:
                return { "is_variable" : False }

    def evalutate_expression(self, expression_str, context):
        res = self.extract_var(expression_str)
        if res['is_variable']:
            var_path = res['path']
            is_iter = res['is_iterator']
            res = context
            for p in var_path:
                res = res[p]
            return { "resolved_value" : res, "is_iterator" : is_iter}
        else:
            raise Exception(f"expression: {expression_str} is not a variable")

    def _resolve_vars_with_respect_to_context(self, inputs, context):
        """
        inputs will be either a string or a dictionary.
        if it is a string, then the string is either a static value, or it is variable that will resolve to either a static value or an an iterator of static values
        we return a generator that will yield the resolved value one at a time

        if it is a dictionary, then we will resolve each of the values in the dictionary with respect to the context
        we turn a generator that returns all possible combinations of the resolved values
        """
        if isinstance(inputs, str):
            if self.is_expression_a_variable(inputs):
                res = self.evalutate_expression(inputs, context)
                if res['is_iterator']:
                    return copy.deepcopy(res['resolved_value'])
                else:
                    return [ copy.deepcopy(res['resolved_value']) ]
            else:
                raise Exception(f"illegal value for variable: {inputs} ")

        elif isinstance(inputs, dict):
            resolved_values_list = list()
            for k,v in inputs.items():
                resolved_value = dict()                
                if self.is_expression_a_variable(v):
                    res = self.evalutate_expression(v, context)
                    if res['is_iterator']:
                        resolved_value[k] = copy.deepcopy(res['resolved_value'])
                    else:
                        resolved_value[k] = [ copy.deepcopy(res['resolved_value']) ]
                else:
                    resolved_value[k] = [ copy.deepcopy(v) ]
                resolved_values_list.append(resolved_value)
            return self.get_combinations(resolved_values_list)
        else:
            raise Exception(f"support for variable: {inputs} with type: {type(inputs)} - not implememted")
        

     

    def create_root_context(self, task_instance):
        """
        Create a root dictionary for the orchestration.

        Args:
            task_instance (dict): The task instance dictionary.

        Returns:
            dict: The root dictionary containing the context, tasks, and orchestration instance.
        """
        context1 = self.orch_definition.get('context', {})
        context2 = self.orch_instance.get('context', {})
        context3 = task_instance.get('context', {})

        context1 = {} if context1 is None else context1
        context2 = {} if context2 is None else context2
        context3 = {} if context3 is None else context3

        context = context1 | context2 | context3
        root = {
            "context": context,
            "tasks": {t['task_id']: t for t in self.task_instances},
            "orch": self.orch_instance
        }
        return root

    def get_task_def(self, task_instance):
        task_id = task_instance['task_id']
        task_def = next((t for t in self.orch_definition['tasks'] if t['taskId'] == task_id), None)
        return task_def

    def get_task_instance(self, taskdef_id):
        return next((task for task in self.task_instances if task['task_id'] == taskdef_id), None)

    def get_orchestration_instances(self, orch_instance_id):    
        return self.store.get_orch_data(orch_instance_id)
    
    def get_inputs_for_task(self, task_instance):
        task_def = self.get_task_def(task_instance)
        inputs = task_def['inputs']
        return inputs

    def get_output_attr_for_task(self, task_instance):
        task_def = self.get_task_def(task_instance)
        output = task_def['output']
        return output

    def _resolve_inputs_for_task_as_generator(self, task_instance):
        """will resolve the inputs for a task instance, and return a generator that will yield the resolved inputs one at a time
        here are a few examples of the types of inputs that we might have to resolve:
        1. a single expression that is not an iterator and that resolves to a generator that returns a single value
        2. a single expression that is an iterator, and that resolves to a generator that returns a set of values
        3. a dictionary of keys & expressions, where all the expressions are not iterators, and that resolves to a generator that returns a single dictionary value
        4. a dictionary of keys & expressions, where at least one of the expressions is an iterator, and that resolves to a generator that returns a set of dictionary values, one value for each item in the iterator
        5. a dictionary of keys & expressions, where more than one expressions is an iterator, and that resolves to a generator that returns a set of dictionary values, one value for each item in the cross-product of the iterators

        Args:
            task_instance (_type_): _description_

        Returns:
            _type_: _description_
        """
        inputs = self.get_inputs_for_task(task_instance)
        context = self.create_root_context(task_instance)
        iterator_result = self._resolve_vars_with_respect_to_context(inputs, context)
        return iterator_result

    def _resolve_output_attr_for_task(self, task_instance):
        """will resolve the inputs for a task instance, and return a generator that will yield the resolved inputs one at a time
        here are a few examples of the types of inputs that we might have to resolve:
        1. a single expression that is not an iterator and that resolves to a generator that returns a single value
        2. a single expression that is an iterator, and that resolves to a generator that returns a set of values
        3. a dictionary of keys & expressions, where all the expressions are not iterators, and that resolves to a generator that returns a single dictionary value
        4. a dictionary of keys & expressions, where at least one of the expressions is an iterator, and that resolves to a generator that returns a set of dictionary values, one value for each item in the iterator
        5. a dictionary of keys & expressions, where more than one expressions is an iterator, and that resolves to a generator that returns a set of dictionary values, one value for each item in the cross-product of the iterators

        Args:
            task_instance (_type_): _description_

        Returns:
            _type_: _description_
        """
        output = self.get_output_attr_for_task(task_instance)
        if output:
            context = self.create_root_context(task_instance)
            result = self._resolve_vars_with_respect_to_context(output, context)[0]
            return result
        else:
            return None
    
    def create_inputs_for_task(self, task_instance):
        task_def = self.get_task_def(task_instance)
        inputs = task_def['inputs']
        return self.resolve_variable_for_task(inputs, task_instance)

    def _split_dict(self, input_dict):
        key = list(input_dict.keys())[0]
        splitted = [{key: value} for value in input_dict[key]]
        return splitted

    def get_combinations(self, inp):
        sd = [self._split_dict(x) for x in inp]
        iter = itertools.product(*sd)
        res = [dict([x for d in c for x in d.items()]) for c in iter]  
        return res
    
    # def resolve_to_iterator_input(self, inputs, task_instance):
    #     vl = [{k : list(self.resolve_variable_for_task(v))} for k,v in inputs.items()]
    #     return self.get_combinations(vl)

    def invoke_function(self, func, input):
        logging.info(f"invoking function: {func} with input: {input}")
        input['token'] = self.token
        input['instance_id'] = self.orch_instance['id']
        result_tuple = func(**input)
        (result, status) = result_tuple
        return (result, status)

    def invoke_repeated_function(self, func, input, output_as_input):
        input['token'] = self.token
        input['instance_id'] = self.orch_instance['id']
        input['output'] = output_as_input
        result_tuple = func(**input)
        (result, status) = result_tuple
        return (result, status)

    def get_function(self, task_instance):

        if self.executors:
            imported_module = importlib.import_module(f"{self.executors}")
        else:
            task_def = self.get_task_def(task_instance)
            module = task_def.get('module', 'executors')
            base_pkg = 'common.orchestration.modules'
            if os.getenv("ORCH_TESTING_MODE"):
                module = module + '_test'
            imported_module = importlib.import_module(f"{base_pkg}.{module}")
        func_str = task_def['func']
        func_callable = getattr(imported_module, func_str)
        return func_callable

    def get_max_repititions(self, task_instance):
        task_def = self.get_task_def(task_instance)
        max_repititions = task_def.get('max_repetitions', 100)
        return max_repititions
    
    def persist(self, instance):
        self.store.persist_instance(instance)

    def get_task_type(self, task_instance):
        task_def = self.get_task_def(task_instance)
        return task_def.get('type', 'single')
    

    def run_task_instance(self, task_instance):
        # this method should also update the status of each steps in the orchestration
        # when a task is started, the status of the step should be updated to "in_progress"
        # when a task is completed, the status of the step should be updated to "completed" if all tasks in the step are completed
        # otherwise, the status of the step should be updated to "in_progress"
        # when a task fails, the status of the step should be updated to "failed"
        #
        # TODO: this method needs to be updated to handle the case where the task is repeated.  
        # TODO: It may need to be refactored to handle that case along with the case where the task is a single execution 
        # TODO: as well as the case where the task is an iterator
        #
        # if this is a repeat task, and it is the first time that we're running it, then we should
        # resolve the output attribute, as it may be an input to this task on the first run
        #
        task_instance['status'] = 'starting'

        task_type = self.get_task_type(task_instance)

        if task_type == "repeat":
            self._run_repeat_execution_task(task_instance)
        else:
            self._run_single_execution_task(task_instance)
        self.refresh_orch_instance_statuses()

    def _run_single_execution_task(self, task_instance):
        """this method will run a single execution task on the provided input.
        As the inputs may container iterators, we may run the task multiple times, once for each input extracted
        from the iterator

        Args:
            task_instance (_type_): _description_
        """
        logging.info(f"running task: {task_instance['task_id']}")
        task_instance['status'] = 'starting'
        self.persist(task_instance)

        the_function = self.get_function(task_instance)
        logging.info(f"function: {the_function}")

        # this will return a generator that will yield the resolved inputs one at a time
        inputs = list(self._resolve_inputs_for_task_as_generator(task_instance))
        logging.info(f"inputs: {inputs}")
        for input in inputs:

            execution_details = self.capture_execution_details(task_instance, input)

            task_status = "completed"
            try:
                output, function_status = self.invoke_function(the_function, input)
                logging.info(f"function completed, output: {output}")
                # TODO: the output for the task instance, should be the aggregate of all the outputs from each
                # invocation of the function, not just the output from the last invocation
                task_instance['output'] = output
                execution_details["output"] = output
                execution_details["status"] = "completed"
            except:
                task_status = "failed"
                execution_details["status"] = "failed"
                logging.info(f"function failed")

            execution_details["end"] = datetime.now().isoformat()

            task_instance['execution_details'].append(execution_details)
            task_instance['executions'].append(execution_details['exec_id'])

        task_instance['status'] = task_status
        self.persist(task_instance)

    def _run_repeat_execution_task(self, task_instance):
        """this method will run a single execution task on the provided input multiple times. 
        As the inputs may container iterators, we may run the task multiple times, once for each input extracted
        from the iterator

        Args:
            task_instance (_type_): _description_
        """
        task_instance['status'] = 'starting'


        the_function = self.get_function(task_instance)

        # task_instance['output'] = output
        self.persist(task_instance)

        # this will return a generator that will yield the resolved inputs one at a time
        inputs = list(self._resolve_inputs_for_task_as_generator(task_instance))
        max_repetitions = self.get_max_repititions(task_instance)

        for input in inputs:
            keep_repeating = True
            num_times_repeated = 0

            # because this is a repeat task, we need to make sure that the output attribute is resolved, as it may be an input to this task on the first run
            prev_output = self._resolve_output_attr_for_task(task_instance)        

            # we need to repeat the task until the max_repetitions is reached, or until the function returns a status other than 200
            # each time we call the function, we need to make sure that we pass the output from the previous call in as the input to the next call
            #
            while keep_repeating:
                num_times_repeated += 1
                if num_times_repeated > max_repetitions:
                    keep_repeating = False

                execution_details = self.capture_execution_details(task_instance, input)

                task_status = "completed"
                try:
                    new_output, function_status = self.invoke_repeated_function(the_function, input, prev_output)
                    task_instance['output'] = new_output
                    execution_details["output"] = new_output
                    execution_details["status"] = "completed"
                    if function_status != 200:
                        execution_details["note"] = f"aborting -- function return status {function_status} not == 200"
                        keep_repeating = False

                except Exception as e:
                    task_status = "failed"
                    execution_details["status"] = f"failed with exception: {e}"
                    keep_repeating = False

                if new_output == prev_output:
                    keep_repeating = False
                    execution_details["note"] = "aborting -- output did not change"
                prev_output = new_output

                execution_details["end"] = datetime.now().isoformat()
                task_instance['execution_details'].append(execution_details)
                task_instance['executions'].append(execution_details['exec_id'])


        task_instance['status'] = task_status
        self.persist(task_instance)

    def capture_execution_details(self, task_instance, input):
        exec_index=task_instance.get('exec_index',0)
        exec_id = f"{task_instance['id']}-{exec_index}"
        exec_index += 1
        start_time = datetime.now().isoformat()
        task_instance['exec_index'] = exec_index
        sanitized_input = copy.deepcopy(input)
        sanitized_input['token'] = '************'
        return {"start": start_time, "exec_id": exec_id, "input": sanitized_input }
    
if __name__ == "__main__":
    import itertools
    input = [ { "x" : [1]} , {"y" : [2,3,4] }, {"z" : [6,7,8]} ]
    expected =  [{"x":1, "y":2, "z":6 },  
                {"x":1, "y":2, "z":7 }, 
                {"x":1, "y":2, "z":8 }, 
                {"x":1, "y":3, "z":6 }, 
                {"x":1, "y":3, "z":7 }, 
                {"x":1, "y":3, "z":8 }, 
                {"x":1, "y":4, "z":6 }, 
                {"x":1, "y":4, "z":7 }, 
                {"x":1, "y":4, "z":8 } ]    

    def split_dict(input_dict):
        key = list(input_dict.keys())[0]
        return [{key: value} for value in input_dict[key]]

    def get_combinations(inp):
        sd = [split_dict(x) for x in inp]
        iter = itertools.product(*sd)
        # return {k: v for d in iter for k, v in d.items()}
        return [dict([x for d in c for x in d.items()]) for c in iter]  

    output = get_combinations(input)
    for c in output:
        print(c)







