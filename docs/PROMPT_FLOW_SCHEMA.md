# Prompt Flow Schema (Dynamic Pipeline)

This schema describes the full authoring pipeline, including optional branches for
variants and embedded entries. It is intentionally **dynamic**: any step that depends
on Markdown headings scales with the number of headers found in the input drafts
(e.g., more `###` groups or `####` variants yield more work items).

The schema is written as JSON Schema (Draft 2020-12) so it can be validated offline.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "botparts://schemas/prompt-flow.schema.json",
  "title": "Botparts Authoring Prompt Flow",
  "type": "object",
  "required": [
    "pipeline",
    "inputs",
    "outputs",
    "state"
  ],
  "properties": {
    "pipeline": {
      "type": "object",
      "required": [
        "mode",
        "steps"
      ],
      "properties": {
        "mode": {
          "type": "string",
          "enum": [
            "canonical",
            "variants"
          ],
          "description": "Authoring mode selected by the user."
        },
        "steps": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/step"
          },
          "description": "Ordered steps executed in the flow."
        }
      },
      "additionalProperties": false
    },
    "inputs": {
      "type": "object",
      "required": [
        "stagingDrafts",
        "prompts"
      ],
      "properties": {
        "stagingDrafts": {
          "type": "object",
          "required": [
            "path",
            "sections"
          ],
          "properties": {
            "path": {
              "type": "string",
              "description": "Selected staging drafts file path."
            },
            "sections": {
              "type": "array",
              "items": {
                "$ref": "#/$defs/headingSection"
              },
              "description": "Parsed headings from the staging drafts file."
            }
          },
          "additionalProperties": false
        },
        "prompts": {
          "type": "object",
          "required": [
            "elaborate",
            "extract_fields",
            "idiosyncrasy_module",
            "embedded_entries_auto",
            "embedded_entries_from_input",
            "rewrite_variants"
          ],
          "properties": {
            "elaborate": {
              "$ref": "#/$defs/promptTemplate"
            },
            "extract_fields": {
              "$ref": "#/$defs/promptTemplate"
            },
            "idiosyncrasy_module": {
              "$ref": "#/$defs/promptTemplate"
            },
            "tone": {
              "$ref": "#/$defs/promptTemplate"
            },
            "voice": {
              "$ref": "#/$defs/promptTemplate"
            },
            "style": {
              "$ref": "#/$defs/promptTemplate"
            },
            "embedded_entries_auto": {
              "$ref": "#/$defs/promptTemplate"
            },
            "embedded_entries_from_input": {
              "$ref": "#/$defs/promptTemplate"
            },
            "rewrite_variants": {
              "$ref": "#/$defs/promptTemplate"
            }
          },
          "additionalProperties": false
        }
      },
      "additionalProperties": false
    },
    "outputs": {
      "type": "object",
      "required": [
        "character",
        "runs",
        "embeddedEntries"
      ],
      "properties": {
        "character": {
          "type": "object",
          "required": [
            "slug",
            "displayName",
            "metaPath",
            "canonicalPaths"
          ],
          "properties": {
            "slug": {
              "type": "string"
            },
            "displayName": {
              "type": "string"
            },
            "metaPath": {
              "type": "string"
            },
            "canonicalPaths": {
              "type": "object",
              "required": [
                "specFieldsPath",
                "shortDescriptionPath"
              ],
              "properties": {
                "specFieldsPath": {
                  "type": "string"
                },
                "shortDescriptionPath": {
                  "type": "string"
                }
              },
              "additionalProperties": false
            }
          },
          "additionalProperties": false
        },
        "runs": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/runLog"
          }
        },
        "embeddedEntries": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/embeddedEntry"
          }
        },
        "variants": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/variantOutput"
          }
        }
      },
      "additionalProperties": false
    },
    "state": {
      "type": "object",
      "required": [
        "selectedSection",
        "progress"
      ],
      "properties": {
        "selectedSection": {
          "$ref": "#/$defs/headingSection"
        },
        "progress": {
          "type": "object",
          "required": [
            "currentStep",
            "completedSteps"
          ],
          "properties": {
            "currentStep": {
              "type": "string"
            },
            "completedSteps": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "additionalProperties": false
        }
      },
      "additionalProperties": false
    }
  },
  "$defs": {
    "step": {
      "type": "object",
      "required": [
        "id",
        "title",
        "status"
      ],
      "properties": {
        "id": {
          "type": "string",
          "description": "Stable identifier for the step."
        },
        "title": {
          "type": "string",
          "description": "Human-readable label for the step."
        },
        "status": {
          "type": "string",
          "enum": [
            "pending",
            "in_progress",
            "complete",
            "skipped",
            "error"
          ]
        },
        "inputs": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "outputs": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "promptRef": {
          "$ref": "#/$defs/promptTemplate"
        },
        "notes": {
          "type": "string"
        }
      },
      "additionalProperties": false
    },
    "headingSection": {
      "type": "object",
      "required": [
        "title",
        "level",
        "content"
      ],
      "properties": {
        "title": {
          "type": "string"
        },
        "level": {
          "type": "integer",
          "minimum": 1
        },
        "content": {
          "type": "string"
        },
        "children": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/headingSection"
          },
          "description": "Nested headings (e.g., ### groups with #### variants)."
        }
      },
      "additionalProperties": false
    },
    "promptTemplate": {
      "type": "object",
      "required": [
        "category",
        "file",
        "sha256"
      ],
      "properties": {
        "category": {
          "type": "string"
        },
        "file": {
          "type": "string"
        },
        "sha256": {
          "type": "string"
        }
      },
      "additionalProperties": false
    },
    "runLog": {
      "type": "object",
      "required": [
        "runId",
        "promptRefs",
        "promptCompiledPath",
        "modelPath",
        "inputHashPath",
        "outputPath"
      ],
      "properties": {
        "runId": {
          "type": "string"
        },
        "promptRefs": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/promptTemplate"
          }
        },
        "promptCompiledPath": {
          "type": "string"
        },
        "modelPath": {
          "type": "string"
        },
        "inputHashPath": {
          "type": "string"
        },
        "outputPath": {
          "type": "string"
        }
      },
      "additionalProperties": false
    },
    "embeddedEntry": {
      "type": "object",
      "required": [
        "entryType",
        "slug",
        "title",
        "description",
        "path"
      ],
      "properties": {
        "entryType": {
          "type": "string",
          "enum": [
            "locations",
            "items",
            "knowledge",
            "ideology",
            "relationships"
          ]
        },
        "slug": {
          "type": "string"
        },
        "title": {
          "type": "string"
        },
        "description": {
          "type": "string"
        },
        "path": {
          "type": "string"
        },
        "scopeLevelIndex": {
          "type": [
            "integer",
            "null"
          ],
          "description": "0=world, 1=character, 2=variant"
        }
      },
      "additionalProperties": false
    },
    "variantOutput": {
      "type": "object",
      "required": [
        "groupTitle",
        "variantTitle",
        "variantSlug",
        "description",
        "specPath",
        "runs"
      ],
      "properties": {
        "groupTitle": {
          "type": "string",
          "description": "Derived from ### headings in staging drafts."
        },
        "variantTitle": {
          "type": "string",
          "description": "Derived from #### headings in staging drafts."
        },
        "variantSlug": {
          "type": "string"
        },
        "description": {
          "type": "string",
          "description": "Body content under the #### heading."
        },
        "specPath": {
          "type": "string",
          "description": "variants/<variant_slug>/spec_v2_fields.md"
        },
        "runs": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/runLog"
          }
        },
        "embeddedEntries": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/embeddedEntry"
          }
        }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

## Notes on dynamic behavior

- **Maintenance reminder**: Whenever the prompt flow changes in the repository,
  update this schema to keep it aligned with actual CLI behavior and outputs.
- **Staging headings drive expansion**: more `#`/`##` sections create more candidates in
  `inputs.stagingDrafts.sections`. More `###` variant groups and `####` variants generate
  more items in `outputs.variants`.
- **Embedded entries are additive**: each generated entry becomes an item in
  `outputs.embeddedEntries` (canonical mode) or `variantOutput.embeddedEntries`
  (variants mode).
- **Run logs are per invocation**: each LLM call yields a `runLog` entry under
  `outputs.runs` or `variantOutput.runs`.

## Minimal 1-step creation template (staging drafts)

See `docs/Minimal_Staging_Draft_Template.md` for the single-step authoring template.
