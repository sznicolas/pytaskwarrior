# LLMs Data Transfer Objects (DTOs)

This document describes the Data Transfer Objects (DTOs) used by the LLMs service.

## Task DTOs

### TaskInputDTO
Used for creating and updating tasks. All fields except `description` are optional. The description field is required when creating a task, but optional when updating.

**Fields:**
- `description`: Task description (required when creating a task, optional when updating)
- `priority`: Task priority level (H, M, L, or None)
- `due`: Due date/time (ISO format or TaskWarrior expressions)
- `project`: Project name
- `tags`: List of tags
- `depends`: List of UUIDs of dependency tasks
- `parent`: UUID of parent recurring task template
- `recur`: Recurrence period for recurring tasks
- `scheduled`: Earliest date/time the task can be started
- `wait`: Date until which task is hidden
- `until`: Expiration date for recurring instances
- `annotations`: List of annotation strings
- `udas`: Dictionary of User Defined Attribute values

### TaskOutputDTO
Used for retrieving tasks. Includes all input fields plus read-only fields.

**Fields:**
- `description`: Task description
- `index`: Task ID number in the working set (alias: "id")
- `uuid`: Unique identifier for the task
- `status`: Current task status
- `priority`: Task priority level
- `due`: Due date/time as datetime object
- `entry`: Task creation timestamp (read-only)
- `start`: Timestamp when task was started (read-only)
- `end`: Timestamp when task was completed (read-only)
- `modified`: Last modification timestamp (read-only)
- `tags`: List of tags
- `project`: Project the task belongs to
- `depends`: List of UUIDs of dependency tasks
- `parent`: UUID of parent recurring task template
- `recur`: Recurrence period if recurring
- `scheduled`: Scheduled start date/time
- `wait`: Date until which task is hidden
- `until`: Expiration date for recurring instances
- `urgency`: Calculated urgency score (read-only)
- `annotations`: List of annotation objects with timestamps
- `udas`: Dictionary of User Defined Attribute values
- `imask`: Mask for recurring tasks or instance number
- `rtype`: Type of recurring task

## UDA DTOs

### UdaType
Data types for User Defined Attributes:
- `STRING`: Free-form text value
- `NUMERIC`: Numeric value (integer or float)
- `DATE`: Date/time value in TaskWarrior format
- `DURATION`: Duration value (e.g., "2hours", "1day")
- `UUID`: UUID reference to another task

### UdaConfig
Configuration for User Defined Attributes.

**Fields:**
- `name`: Unique name for the UDA
- `type`: Data type of the UDA value
- `label`: Human-readable label for display in reports
- `values`: List of allowed values (for string type with enumeration)
- `default`: Default value when not specified
- `coefficient`: Urgency coefficient

## Context DTO

### ContextDTO
Data Transfer Object for task contexts.

**Fields:**
- `name`: The unique name of the context
- `filter`: The TaskWarrior filter expression for this context
- `active`: Whether this context is currently active

## Annotation DTO

### AnnotationDTO
Data Transfer Object for task annotations.

**Fields:**
- `entry`: Timestamp when the annotation was created
- `description`: The annotation text content
