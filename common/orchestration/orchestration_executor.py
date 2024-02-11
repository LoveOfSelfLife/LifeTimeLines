import copy
import re


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
        5.c  set the status of the task instance based on the function (if exception thrown, then status is failed, othewise it is success)
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
    def __init__(self, data_store, orch_instance_id, token=None):
        self.store = data_store
        self.orch_definition, self.orch_instance, self.task_instances = self.store.get_orch_data(orch_instance_id)
        self.token = token

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

    def update_step_status(self, step, status):
        # TODO: need to review this co-pilot generated code
        for taskid in step['tasks']:
            task_inst = next((t for t in self.task_instances if t['task_id'] == taskid), None)
            if task_inst:
                task_inst['status'] = status
                self.persist(task_inst)

    def test_if_iterator(self, expression_str):
        _, is_iter = self.extract_var(expression_str)
        return is_iter

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
            m = re.match(PAT_ITERATOR, expression_str)
            if m:
                var = m.group(1)
                is_iterator = True
            else:
                m = re.match(PAT_SINGLE, expression_str)
                if m:
                    var = m.group(1)
            if var:
                path = var.split('.')
                return path, is_iterator
            return expression_str, None

    def resolve(self, expression_str, task_instance):
        """
        Resolves the given expression string by extracting the variable path and checking if it is iterable.
        If the variable path exists, it creates a root dictionary from the task instance and traverses the path to return the result.
        If the variable path does not exist, it returns the original expression string.

        Args:
            expression_str (str): The expression string to resolve.
            task_instance: The task instance object.

        Returns:
            The resolved value of the expression string or the original expression string if it cannot be resolved.
        """
        var_path, is_iter = self.extract_var(expression_str)
        if var_path:
            root_dict = self.create_root_dict(task_instance)
            res = root_dict
            for p in var_path:
                res = res[p]
            return res
        return expression_str

    def create_root_dict(self, task_instance):
        """
        Create a root dictionary for the orchestration.

        Args:
            task_instance (dict): The task instance dictionary.

        Returns:
            dict: The root dictionary containing the context, tasks, and orchestration instance.
        """
        context1 = self.orch_definition['context'] if self.orch_definition['context'] else {}
        context2 = self.orch_instance['context'] if self.orch_instance['context'] else {}
        context3 = task_instance['context'] if task_instance['context'] else {}

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
    
    def create_inputs_for_task(self, task_instance):
        new_inputs = {}
        is_iterator = { "iterator" : False, "key": None, "val" : None}
        task_def = self.get_task_def(task_instance)
        inputs = task_def['inputs']
        if isinstance(inputs, list):
            raise Exception("support for list value inputs not implememted")
        elif isinstance(inputs, str):
            if self.test_if_iterator(inputs):
                for item in self.resolve(inputs, task_instance):
                    yield item
            else:
                item = self.resolve(inputs, task_instance)
                yield item
        elif isinstance(inputs, dict):

            for k,v in inputs.items():
                if self.test_if_iterator(v):
                    if is_iterator["iterator"]:
                        raise Exception('can only have one iterator')
                    else:
                        is_iterator = { "iterator": True, "key" : k, "val" : v }

            for k,v in inputs.items():
                if k != is_iterator["key"]:
                    new_val = self.resolve(v, task_instance)
                    new_inputs[k] = new_val

            if is_iterator['iterator']:
                for item in self.resolve(is_iterator['val'], task_instance):
                    new_inputs[is_iterator['key']] = item
                    yield copy.deepcopy(new_inputs)
            else:
                yield new_inputs
        else:
            raise Exception(f"support for {type(inputs)} value inputs not implememted")
        
    def invoke_function(self, func, input):
        input['token'] = self.token
        result = func(**input)
        return result

    def get_function(self, task_instance):
        import common.orchestration.executors    
        task_def = self.get_task_def(task_instance)
        func_str = task_def['worker']['pyfunc']
        func_callable = getattr(common.orchestration.executors, func_str)
        return func_callable
    
    def persist(self, instance):
        self.store.persist_instance(instance)

    def run_task_instance(self, task_instance):
        # this method should also update the status of each steps in the orchestration
        # when a task is started, the status of the step should be updated to "in-progress"
        # when a task is completed, the status of the step should be updated to "completed" if all tasks in the step are completed
        # otherwise, the status of the step should be updated to "in-progress"
        # when a task fails, the status of the step should be updated to "failed"
        from datetime import datetime

        task_instance['status'] = 'starting'
        self.persist(task_instance)
        
        inputs = list(self.create_inputs_for_task(task_instance))
        the_function = self.get_function(task_instance)

        num_inputs = len(inputs)
        task_instance_id = task_instance['id']

        if num_inputs > 1:
            task_instance['output'] = []

        task_status = "success"
        exec_index=task_instance['exec_index']
        for input in inputs:
            exec_id = f"{task_instance_id}-{exec_index}"
            exec_index += 1
            start_time = datetime.now().isoformat()
            output = self.invoke_function(the_function, input)
            try:
                output = self.invoke_function(the_function, input)
                if num_inputs == 1:
                    task_instance['output'] = output
                else:
                    task_instance['output'].append(output)
                exec_status = "success"
            except:
                task_status = "failed"
                exec_status = "failed"

            end_time = datetime.now().isoformat()
            task_instance['execution_details'].append({"start": start_time, "end": end_time, "exec_id": exec_id, "status": exec_status})
            task_instance['executions'].append(exec_id)
            self.persist(task_instance)

        task_instance['status'] = task_status
        task_instance['exec_index'] = exec_index
        self.persist(task_instance)
