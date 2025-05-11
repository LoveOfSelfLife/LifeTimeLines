member_schema = {
	"title": "Member",
	"type": "object",
	"required": [
		"id",
        "name",
        "level",
        "short_name",
        "email",
        "mobile",
        "sms_consent",
        "email_consent",
        "image_url"
	],
	"properties": {
		"id": {
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
		"level": {
			"type": "integer",
			"propertyOrder": 2,
			"range": [0, 10]
		},
        "short_name": {
            "type": "string",
            "minLength": 1,
            "default": "",
            "propertyOrder": 3
        },
        "email": {
            "type": "string",
            "format": "email",
            "propertyOrder": 4
        },
        "mobile": {
            "type": "string",
            "format": "tel",
            "propertyOrder": 5
        },
        "sms_consent": {
            "type": "boolean",
            "propertyOrder": 6
        },
        "email_consent": {
            "type": "boolean",
            "propertyOrder": 7
        },
        "image_url": {
            "type": "string",
            "format": "url",
            "propertyOrder": 8,
            "options": {
                "upload": {
                    "upload_handler": "realUploadHandler"
                }
            },
            "links": [
                {
                "href": "{{self}}",
                "rel": "view"
                }
            ]
        }
    }
}
