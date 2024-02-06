import re


class OrchestrationExecutor:
    def __init__(self, data_store, orch_instance_id):
        self.store = data_store
        self.orch_definition, self.orch_instance, self.task_instances = self.store.get_orch_data(orch_instance_id)

    def find_next_task_inst_to_run(self):
        flow = self.orch_definition['flow']
        task = None
        for step in flow:
            for taskid in step['tasks']:
                task_inst = next((t for t in self.task_instances if t['status'] == 'not_started'), None)
                if not task_inst:
                    continue
        return task_inst

    def test_if_iterator(self, expression_str):
        _, is_iter = self.extract_var(expression_str)
        return is_iter

    def extract_var(self, expression_str):
        var = None
        is_iterator = False
        PAT_ITERATOR =  '\$<\[(.*)\]>'
        PAT_SINGLE =  '\$<(.*)>'
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
        var_path, is_iter = self.extract_var(expression_str)
        if var_path:
            root_dict = self.create_root_dict(task_instance)
            res = root_dict
            for p in var_path:
                res = res[p]
            return res
        return expression_str

    def create_root_dict(self, task_instance):
        context1 = self.orch_definition['context'] if self.orch_definition['context'] else {}
        context2 = self.orch_instance['context'] if self.orch_instance['context'] else {}
        context3 = task_instance['context'] if task_instance['context'] else {}

        context = context1 | context2 | context3
        root = { "context" : context,
                 "tasks" : { t['task_id'] : t for t in self.task_instances },
                 "orch" : self.orch_instance
        }
        return root

    def get_task_def(self, task_instance):
        task_id = task_instance['task_id']
        task_def = next((t for t in self.orch_definition['tasks'] if t['taskId'] == task_id), None)
        return task_def

    def get_task_instance(self, taskdef_id):
        return next((task for task in self.task_instances if task['task_id'] == taskdef_id), None)

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
                    yield new_inputs
            else:
                yield new_inputs
        else:
            raise Exception(f"support for {type(inputs)} value inputs not implememted")
        
    def invoke_function(self, func, input):
        pass
    def get_function(self, task_instance):
        task_def = self.get_task_def(task_instance)
        return task_def['worker']['pyfunc']

    def persist(self, instance):
        self.store.persist_instance(instance)

    def run_task_instance(self, task_instance):
        task_instance['status'] = 'starting'
        self.store.persist_instance(task_instance)
        inputs, is_iterator = self.create_inputs_for_task(task_instance)

        the_function = self.get_function(task_instance)
        try:
            output = self.invoke_function(the_function, inputs)
            task_instance['output'] = output
            task_instance['status'] = 'success'
            self.store.persist_instance(task_instance)
        except:
            task_instance['status'] = 'failed'

        self.store.persist_instance(task_instance)