# Minimal 1-step Staging Draft Template

Use this template as the minimum viable Markdown input for a single-step
canonical authoring run. Each section header represents the answer for one
authoring step or decision point in the flow.

```md
# Character concept (staging selection)
Paste the character concept you want to select here.

## Slug
Provide the slug the CLI should use.

## Display name
Provide the display name the CLI should use.

## Elaborate prompt notes
Optional notes to guide the elaboration prompt.

## Draft edits (manual)
Notes or edits to apply after elaboration.

## Extraction prompt notes
Optional notes to guide field extraction.

## Embedded entries
Optional notes for embedded entry generation.

Use `###` headings to declare the embedded entry type. Each `###` heading must
start with one of the allowed type words to satisfy the schema:
`Location`, `Item`, `Knowledge`, `Ideology`, or `Relationship`
(mapped to `locations`, `items`, `knowledge`, `ideology`, `relationships`).

Use `####` headings for each embedded entry title under the matching type, and
write the description content beneath the `####` heading.

Example:

### Location: Infirmary
#### Infirmary
Location: Her workplace, has everything she needs.

### Item: First-Aid Kit
#### First-Aid Kit
Item: Necessary for advanced stabilization operations.

### Relationship: Dr. Klein
#### Dr. Klein
Relationship: Her mentor and direct superior in the hospital.

## Audit notes
Optional notes or expected checks after audit.
```
