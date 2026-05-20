# there are two types of parameters:  (1) value_parameters like F, T, D, and P, which each can have a value whose domain of values is
# determined by the corresponding unit parameter
# and (2) unit_parameters like Fu, Tu, Du, and Pu, whose domain of valid values is determined by the exercise definition.
# the standard domain of unit parameter values are:
# Fu (force units): ["kg", "lbs", "bands"]
# Tu (time units): ["sec", "min", "hour"]
# Du (distance units): ["meters", "yards", "miles"]
# Pu (pace units): ["rate", "tempo"]
# The value assigned to the unit parameter determines the type of the value parameters. 
# 
# For example, if Fu is "kg" or "lbs", then F would be a numeric parameter representing the amount of weight to use. 
# But if Fu is "bands", then F would be a dropdown with options like "light (yellow)", "medium (green)", and "heavy (black)". 
# So when we want to render an editor for a parameter, we first need to check the current value of the corresponding unit parameter 
# to determine what type of editor to render for the value parameter.

def get_editor_type_for_unit_parameter(unit_parameter, exerise_def):
    if unit_parameter == 'Fu':
        return { "type": "choice", "options": ["kg", "lbs", "bands"] }
    if unit_parameter == 'Tu':
        return { "type": "choice", "options": ["sec", "min", "hour"] }
    if unit_parameter == 'Du':
        return { "type": "choice", "options": ["meters", "kilometers", "feet", "yards", "miles"] }
    if unit_parameter == 'Pu':
        return { "type": "choice", "options": ["rate", "tempo"] }
    return { "type": "text" }

def get_editor_type_for_value_parameter(value_parameter, unit_parameter_value, exercise_def):
    if value_parameter == 'F':
        if unit_parameter_value in ["kg", "lbs"]:
            return { "type": "numeric" }
        elif unit_parameter_value == "bands":
            return { "type": "choice", "options": ["yellow", "green", "black"] }
    if value_parameter == 'T':
        if unit_parameter_value in ["sec", "min", "hour"]:
            return { "type": "numeric" }
    if value_parameter == 'D':
        if unit_parameter_value in ["meters", "kilometers", "feet", "yards", "miles"]:
            return { "type": "numeric" }    
    if value_parameter == 'P':
        if unit_parameter_value in ["rate", "tempo"]:
            return { "type": "text" }

    return { "type": "text" }
