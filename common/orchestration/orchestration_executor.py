import copy
import re
from datetime import datetime

from common.orchestration.orchestration_utils import OrchTaskDefDataStore



def execute_orchestration(orch_cmd, orch_data=None, token=None):
    """this method will execute the indicated orchestration intance
    orch_definition: ID of the orchestration intance, 
    auth token,
    arg will be the number of steps to push the orchestration forward.  By default, the orchestration engine will execute the next task that is defined 
    in the orchestration definion, and then it will cede control and post a message for the next task to execute.
    """
    # somewhere in this code or in the calling code, we need to check the status of all the task instances, 
    # and if they are all completed, then we need to mark the orchestration instance as completed
    command = orch_cmd['command']
    orch_instance_id = orch_cmd['orch_instance_id']
    arg = orch_cmd['arg']

    orch_data = OrchTaskDefDataStore() if orch_data is None else orch_data
    executor = OrchestrationExecutor(orch_data, orch_instance_id, token)
    if command == "execute":

        for step_id in executor.get_steps():
            step_status = executor.get_step_status(step_id)
            print(f'step_id: {step_id}, step_status: {step_status}')
            if step_status == "not_started" or step_status == "in-progress":
                run_tasks_in_step_status = executor.run_all_unfinished_tasks_in_step(step_id)
            elif step_status == "completed":
                continue
            else:
                print(f'step_id: {step_id} has failed tasks, so cannot finish the step')
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

    def get_steps(self):
        for step in self.orch_definition['flow']:
            yield step['step_id']
    
    def get_step_status(self, step_id):
        step = next((s for s in self.orch_definition['flow'] if s['step_id'] == step_id), None)
        task_statuses = [self.get_task_status(t) for t in step['tasks']]
        if all(s == "not_started" for s in task_statuses):
            return "not_started"
        elif all(s == "completed" for s in task_statuses):
            return "completed"
        elif any(s == "failed" for s in task_statuses):
            return "failed"
        else:
            return "in-progress"
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

    def validate_definition(self):
        pass

    def get_task_status(self, task_id):
        task = next((t for t in self.task_instances if t['task_id'] == task_id), None)
        return task['status']
    
    def find_next_step_to_run(self):
        for step in self.get_steps():
            step_status = self.get_step_status(step['step_id'])
            if step_status == "not_started" or step_status == "in-progress":
                return step
        return None
    
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
        if is_iter == None:
            return expression_str
        else:
            root_dict = self.create_root_dict(task_instance)
            res = root_dict
            for p in var_path:
                res = res[p]
            return res

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
        # TODO: this method will need to be updated to handle the case where
        # the output of a task is an input to the same task when it is repeated
        #
        task_def = self.get_task_def(task_instance)
        inputs = task_def['inputs']
        return self.resolve_variable_for_task(inputs, task_instance)

    def resolve_variable_for_task(self, inputs, task_instance):
        # TODO: this method will need to be updated to handle the case where
        # the output of a task is an input to the same task when it is repeated
        #
        new_inputs = {} 
        is_iterator = { "iterator" : False, "key": None, "val" : None}
        if isinstance(inputs, list):
            raise Exception("support for list value inputs not implememted")
        elif isinstance(inputs, str):
            # TODO: the code in this block is not correct.  
            # It needs to be updated to handle the iterator case
            # raise Exception("support for string value inputs not completely implememted yet")
            item = self.resolve(inputs, task_instance)            
            yield copy.deepcopy(item)

        elif isinstance(inputs, dict):
            # first verify that if there is an iterator, that there is only *one* iterator, and capture the iterator key and value
            for k,v in inputs.items():
                if self.test_if_iterator(v):
                    if is_iterator["iterator"]:
                        raise Exception('can only have one iterator')
                    else:
                        is_iterator = { "iterator": True, "key" : k, "val" : v }
            # then for each of the non-iterator items in the dictionary, resolve those items first
            for k,v in inputs.items():
                if k != is_iterator["key"]:
                    new_val = self.resolve(v, task_instance)
                    new_inputs[k] = new_val
            # then for the iterator item, if it is present, resolve the iterator by yielding each item one at a time
            if is_iterator['iterator']:
                for item in self.resolve(is_iterator['val'], task_instance):
                    new_inputs[is_iterator['key']] = item
                    yield copy.deepcopy(new_inputs)
            else:
                yield new_inputs
        else:
            raise Exception(f"support for inputs: {inputs} with type: {type(inputs)} - not implememted")
        
    def invoke_function(self, func, input):
        input['token'] = self.token
        result_tuple = func(**input)
        (result, status) = result_tuple
        return (result, status)

    def get_function(self, task_instance):
        import common.orchestration.executors    
        task_def = self.get_task_def(task_instance)
        func_str = task_def['worker']['pyfunc']
        func_callable = getattr(common.orchestration.executors, func_str)
        return func_callable
    
    def persist(self, instance):
        self.store.persist_instance(instance)

    def get_task_type(self, task_instance):
        task_def = self.get_task_def(task_instance)
        return task_def['type']
    

    def run_task_instance(self, task_instance):
        # this method should also update the status of each steps in the orchestration
        # when a task is started, the status of the step should be updated to "in-progress"
        # when a task is completed, the status of the step should be updated to "completed" if all tasks in the step are completed
        # otherwise, the status of the step should be updated to "in-progress"
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
        if task_type == "once":
            self.run_single_execution_task(task_instance)
        elif task_type == "iterator":
            self.run_iterator_task(task_instance)
        elif task_type == "repeat":
            self.run_repeat_task(task_instance)
        else:
            raise Exception(f"unsupported task type: {task_type}")

    def run_single_execution_task(self, task_instance):
        task_instance['status'] = 'starting'
        self.persist(task_instance)
        input = next(self.create_inputs_for_task(task_instance))

        the_function = self.get_function(task_instance)
        exec_index=task_instance.get('exec_index',0)
        exec_id = f"{task_instance['id']}-{exec_index}"
        exec_index += 1
        start_time = datetime.now().isoformat()
        task_status = "success"
        try:
            result_tuple = self.invoke_function(the_function, input)
            (output, function_status) = result_tuple
            task_instance['output'] = output

            # hist = task_instance.get('output_history', [])
            # hist.append(task_instance['output'])
            # task_instance['output_history'] = hist

            exec_status = "success"
        except Exception as e:
            print(f"exception: {e}")
            task_status = "failed"
            exec_status = "failed"

        end_time = datetime.now().isoformat()
        task_instance['execution_details'].append({"start": start_time, "end": end_time, "input": input, "output": output, "exec_id": exec_id, "status": exec_status})
        task_instance['executions'].append(exec_id)
        task_instance['status'] = task_status
        task_instance['exec_index'] = exec_index
        self.persist(task_instance)

        print(f"single execution task status: {task_instance['status']}")
        print("store: *******************************************************************")
        print(f"{self.store}")
        print("end **********************************************************************")

    def run_iterator_task(self, task_instance):
        task_instance['status'] = 'starting'
        self.persist(task_instance)
        input = next(self.create_inputs_for_task(task_instance))

        the_function = self.get_function(task_instance)
        exec_index=task_instance.get('exec_index',0)
        exec_id = f"{task_instance['id']}-{exec_index}"
        exec_index += 1
        start_time = datetime.now().isoformat()
        task_status = "success"

        inputs = list(self.create_inputs_for_task(task_instance))

        the_function = self.get_function(task_instance)
        for input in inputs:
            exec_index=task_instance.get('exec_index',0)
            exec_id = f"{task_instance['id']}-{exec_index}"
            exec_index += 1
            start_time = datetime.now().isoformat()

            task_status = "success"
            try:
                output, function_status = self.invoke_function(the_function, input)
                task_instance['output'] = output
                exec_status = "success"
            except:
                task_status = "failed"
                exec_status = "failed"

            end_time = datetime.now().isoformat()
            task_instance['execution_details'].append({"start": start_time, "end": end_time, "input" : input, "output": output, "exec_id": exec_id, "status": exec_status})
            task_instance['executions'].append(exec_id)

        task_instance['status'] = task_status
        task_instance['exec_index'] = exec_index
        self.persist(task_instance)
        print(f"iterator execution task status: {task_instance['status']}")
        print("store: *******************************************************************")
        print(f"{self.store}")
        print("end **********************************************************************")
        

    def run_repeat_task(self, task_instance):
        # TODO: Implement logic for a repeated task
        """_summary_

        # TODO:  seems like this is where we should be possibly adding output values for the task instance based on
        # the task definition for the output attribute

        # we should only do this for repeat tasks, and only if the output attribute of the task instance is None
        # if the output attribute of the task instance is not None, it means that the task has already been run
        # if the task instance has an output attribute that is None, and the task definition has an output attribute, then we should
        # resolve the output attribute and set the output attribute of the task instance to the resolved value

        """
        task_instance['status'] = 'starting'
        self.persist(task_instance)

        task_def = self.get_task_def(task_instance)
        output = task_def['output']
        done = False
        outval = next(self.resolve_variable_for_task(output, task_instance))
        task_instance['output'] = outval

        while not done:

            input = next(self.create_inputs_for_task(task_instance))

            the_function = self.get_function(task_instance)
            exec_index=task_instance.get('exec_index',0)
            exec_id = f"{task_instance['id']}-{exec_index}"
            exec_index += 1
            start_time = datetime.now().isoformat()
            task_status = "success"
            try:
                exec_status = "success"
                (output, function_status) = self.invoke_function(the_function, input)
                if function_status != 200:
                    done = True
                    continue

                task_instance['output'] = output

                # hist = task_instance.get('output_history', [])
                # hist.append(task_instance['output'])
                # task_instance['output_history'] = hist

            except Exception as e:
                print(f"exception: {e}")
                task_status = "failed"
                exec_status = "failed"

            end_time = datetime.now().isoformat()
            task_instance['execution_details'].append({"start": start_time, "end": end_time, "input": input, "output": output, "exec_id": exec_id, "status": exec_status})
            task_instance['executions'].append(exec_id)

        task_instance['status'] = task_status
        task_instance['exec_index'] = exec_index
        self.persist(task_instance)

        print(f"repeat execution task status: {task_instance['status']}")
        print("store: *******************************************************************")
        with open('test/orchestration/outtrade.json', "w") as jfd:
            print(f"{self.store}", file=jfd)
        print("end **********************************************************************")


