schema = {
	"title": "Exercise",
	"type": "object",
	"required": [
		"name",
		"category",
		"equipment",
		"equipment_detail",
		"force",
		"instructions",
		"level",
		"mechanic",
		"origin",
		"primaryMuscles",
		"secondaryMuscles"
	],
	"properties": {
		"name": {
			"type": "string",
			"minLength": 4,
			"default": "",
			"propertyOrder": 1
		},
		"category": {
			"type": "string",
			"propertyOrder": 2,
			"enum": [
				"strength",
				"stretching",
				"warmup",
				"core",
				"mobility",
				"plyometrics",
				"strongman",
				"powerlifting",
				"cardio",
				"olympic_weightlifting",
				"crossfit",
				"weighted_bodyweight",
				"assisted_bodyweight"
			]
		},
		"equipment": {
			"type": "string",
			"propertyOrder": 3,
			"enum": [
				"bodyweight",
				"machine",
				"kettlebells",
				"dumbbell",
				"cable",
				"barbell",
				"bands",
				"medicine_ball",
				"exercise_ball",
				"e_z_curl_bar",
				"foam_roll"
			]
		},
		"equipment_detail": {
			"type": "string",
			"propertyOrder": 4,
			"default": ""
		},
		"force": {
			"type": "string",
			"propertyOrder": 5,
			"enum": [
				"push",
				"pull",
				"static"
			]
		},
		"instructions": {
			"type": "string",
			"title": "instructions",
			"format": "textarea",
			"default": "",
			"propertyOrder": 6,
		},
		"level": {
			"type": "string",
			"propertyOrder": 7,
			"enum": [
				"beginner",
				"intermediate",
				"advanced",
				"expert"
			]
		},
		"mechanic": {
			"type": "string",
			"propertyOrder": 8,
			"enum": [
				"compound",
				"isolation"
			]
		},
		"origin": {
			"type": "string",
			"propertyOrder": 9,
			"default": "rich"
		},
		"primaryMuscles": {
			"type": "array",
			"title": "primaryMuscles",
            "format": "checkbox",
			"propertyOrder": 10,
			"items": {
				"type": "string",
				"enum": [
					"abdominals",
					"hamstrings",
					"calves",
					"shoulders",
					"adductors",
					"glutes",
					"quadriceps",
					"biceps",
					"forearms",
					"abductors",
					"triceps",
					"chest",
					"lower_back",
					"traps",
					"middle_back",
					"lats",
					"neck"
				]
			},
			"uniqueItems": True,
			"default": []
		},
		"secondaryMuscles": {
			"type": "array",
			"title": "secondaryMuscles",
            "format": "checkbox",
			"propertyOrder": 11,
			"items": {
				"type": "string",
				"enum": [
					"abdominals",
					"hamstrings",
					"calves",
					"shoulders",
					"adductors",
					"glutes",
					"quadriceps",
					"biceps",
					"forearms",
					"abductors",
					"triceps",
					"chest",
					"lower_back",
					"traps",
					"middle_back",
					"lats",
					"neck"
				]
			},
			"uniqueItems": True,
			"default": []
		},
		"setCompletionMeasure": {
			"type": "string",
			"propertyOrder": 12,
			"enum": [
				"reps",
				"time",
				"distance",
				"calories"
			]
		},
		"images": {
			"type": "array",
			"format": "table",
			"title": "Images",
			"uniqueItems": True,
			"propertyOrder": 13,
			"items": {
				"type": "object",
				"title": "Image",
				"properties": {
					"type": {
						"type": "string",
						"enum": [
							"start-of-movement",
							"end-of-movement"
						],
						"default": "start-of-movement"
					},
					"description": {
						"type": "string"
					},
					"url": {
						"type": "string",
						"format": "url",
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
		},
		"videos": {
			"type": "array",
			"format": "table",
			"title": "Videos",
			"uniqueItems": True,
			"propertyOrder": 14,
			"items": {
				"type": "object",
				"title": "Video",
				"properties": {
					"description": {
						"type": "string"
					},
					"url": {
						"type": "string",
						"format": "url",
						"options": {
							"upload": {
								"upload_handler": "realUploadHandler"
							}
						}
					}
				}
			}
		},
		"type": {
			"type": "string",
			"default": ""
		},
		"id": {
			"type": "string",
			"default": "",
            "readOnly": True,
		},
		"udf1": {
			"type": "string",
			"default": ""
		},
		"udf2": {
			"type": "string",
			"default": ""
		}
	}
}
