program_schema = {
	"title": "Member",
	"type": "object",
	"required": [
		"id",
        "member_id",
        "name",
        "description",
        "start_date",
        "end_date",
        "workouts"
    ],
	"properties": {
		"id": {
			"type": "string",
            "readOnly": True,
            "default": "",
		},
		"member_id": {
			"type": "string",
            "readOnly": True,
            "default": "",
		},
        "name": {
			"type": "string",
			"minLength": 1,
			"default": "",
			"propertyOrder": 1
		},
        "description": {
			"type": "string",
			"default": "",
			"propertyOrder": 2
		},
		"start_date":  {
            "type": "string",
            "format": "date",
            "propertyOrder": 3,
            "options": {
                "flatpickr": {}
            }
        },
		"end_date":  {
            "type": "string",
            "format": "date",
            "propertyOrder": 4,
            "options": {
                "flatpickr": {}
            }
        },
        "workouts": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "propertyOrder": 5
        }
    }
}
