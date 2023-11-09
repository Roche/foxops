import pytest
from pydantic import ValidationError

from foxops.engine.models.template_config import (
    BooleanVariableDefinition,
    IntegerVariableDefinition,
    ObjectVariableDefinition,
    StringListVariableDefinition,
    StringVariableDefinition,
    TemplateConfig,
)

FENGINE_FILE = """
rendering:
    excluded_files:
        - "**/*.png"
        - "**/*.jpg"

variables:
    test_object_required:
        type: object
        description: test object

        children:
            test_string:
                type: string
                description: test string
            test_integer:
                type: integer
                description: test integer
            test_string_list:
                type: list
                element_type: string
                description: test list string
            test_object:
                type: object
                description: test object

                children:
                    test_string:
                        type: string
                        description: test string

    test_object_optional:
        type: object
        description: test object

        children:
            test_object:
                type: object
                description: test nested object

                children:
                    test_string:
                        type: string
                        description: test string
                        default: test

        default:
            test_object:
                test_string: override
"""


@pytest.mark.parametrize(
    "type_,element_type,default,expected_type",
    [
        ("str", None, None, StringVariableDefinition),
        ("string", None, None, StringVariableDefinition),
        ("str", None, "test", StringVariableDefinition),
        ("string", None, "test", StringVariableDefinition),
        ("int", None, None, IntegerVariableDefinition),
        ("integer", None, None, IntegerVariableDefinition),
        ("int", None, 1, IntegerVariableDefinition),
        ("integer", None, 1, IntegerVariableDefinition),
        ("boolean", None, None, BooleanVariableDefinition),
        ("boolean", None, True, BooleanVariableDefinition),
        ("list", "string", None, StringListVariableDefinition),
        ("list", "string", ["abc", "def"], StringListVariableDefinition),
    ],
)
def test_basic_variable_parsing(type_, element_type, default, expected_type):
    # GIVEN
    template_config = {
        "variables": {
            "varname": {
                "type": type_,
                "description": "testdescription",
            },
        }
    }
    if element_type is not None:
        template_config["variables"]["varname"]["element_type"] = element_type
    if default is not None:
        template_config["variables"]["varname"]["default"] = default

    # WHEN
    parsed = TemplateConfig.model_validate(template_config)

    # THEN
    assert isinstance(parsed.variables["varname"], expected_type)
    assert parsed.variables["varname"].description == "testdescription"
    assert parsed.variables["varname"].default == default


def test_object_variable_parsing():
    # GIVEN
    template_config = {
        "variables": {
            "varname": {
                "type": "object",
                "description": "testdescription",
                "children": {
                    "test_string": {
                        "type": "string",
                        "description": "testdescription",
                    },
                    "test_boolean": {
                        "type": "boolean",
                        "description": "testdescription",
                    },
                    "test_object": {
                        "type": "object",
                        "description": "testdescription",
                        "children": {
                            "test_string": {
                                "type": "string",
                                "description": "testdescription",
                            },
                        },
                    },
                },
            },
        },
    }

    # WHEN
    parsed = TemplateConfig.model_validate(template_config)

    # THEN
    assert isinstance(parsed.variables["varname"], ObjectVariableDefinition)
    assert isinstance(parsed.variables["varname"].children["test_string"], StringVariableDefinition)
    assert isinstance(parsed.variables["varname"].children["test_object"], ObjectVariableDefinition)
    assert isinstance(
        parsed.variables["varname"].children["test_object"].children["test_string"],
        StringVariableDefinition,
    )


def test_object_variable_parsing_fails_for_invalid_default():
    # GIVEN
    template_config = {
        "variables": {
            "varname": {
                "type": "object",
                "description": "testdescription",
                "children": {
                    "test_string": {
                        "type": "string",
                        "description": "testdescription",
                    },
                    "test_boolean": {
                        "type": "boolean",
                        "description": "testdescription",
                        "default": "abc",
                    },
                },
                "default": {
                    "wrong_string": "abc",
                },
            }
        }
    }
    with pytest.raises(ValidationError, match="Input should be a valid boolean"):
        TemplateConfig.model_validate(template_config)


def test_template_data_validation():
    # GIVEN
    template_config = TemplateConfig(
        variables={
            "test_string": StringVariableDefinition(
                description="test string",
            ),
            "test_integer": IntegerVariableDefinition(
                description="test integer",
            ),
            "test_string_list": StringListVariableDefinition(
                description="test list string",
            ),
            "test_object": ObjectVariableDefinition(
                description="test object",
                children={
                    "test_string": StringVariableDefinition(
                        description="test string",
                    ),
                },
            ),
        }
    )
    template_data = {
        "test_string": "test",
        "test_integer": 1,
        "test_string_list": ["abc", "def"],
        "test_object": {
            "test_string": "test",
        },
    }
    parsed_config = TemplateConfig.model_validate(template_config)

    # WHEN
    data_model = parsed_config.data_model()
    parsed_data = data_model.model_validate(template_data)

    # THEN
    assert parsed_data.test_string == "test"
    assert parsed_data.test_integer == 1
    assert parsed_data.test_string_list == ["abc", "def"]
    assert parsed_data.test_object.test_string == "test"


def test_basic_template_data_validation():
    # GIVEN
    template_config = TemplateConfig(
        variables={
            "test_string": StringVariableDefinition(
                description="test string",
            ),
            "test_string_optional": StringVariableDefinition(
                description="test string",
                default="test_default",
            ),
        }
    )
    template_data = {
        "test_string": "test",
    }
    parsed_config = TemplateConfig.model_validate(template_config)

    # WHEN
    data_model = parsed_config.data_model()
    parsed_data = data_model.model_validate(template_data)

    # THEN
    assert parsed_data.test_string == "test"
    assert parsed_data.test_string_optional == "test_default"


def test_template_config_rejects_invalid_variable_names():
    with pytest.raises(ValidationError):
        TemplateConfig(
            variables={
                "my-test-variable": StringVariableDefinition(description="test string"),
            }
        )
    with pytest.raises(ValidationError):
        TemplateConfig(
            variables={
                "nested": ObjectVariableDefinition(
                    description="test object",
                    children={
                        "nested-test": StringVariableDefinition(description="test string"),
                    },
                ),
            }
        )


def test_template_data_validation_for_nested_objects_with_defaults_inside():
    # GIVEN
    template_config = TemplateConfig(
        variables={
            "test_object": ObjectVariableDefinition(
                description="test object",
                children={
                    "test_string": StringVariableDefinition(
                        description="test string",
                        default="test",
                    ),
                },
            ),
        }
    )
    template_data = {}
    parsed_config = TemplateConfig.model_validate(template_config)

    # WHEN
    data_model = parsed_config.data_model()
    parsed_data = data_model.model_validate(template_data)

    # THEN
    assert parsed_data.test_object.test_string == "test"


def test_template_string_variables_accept_integer_inputs_and_converts_them():
    # GIVEN
    template_config = TemplateConfig(
        variables={
            "test_string": StringVariableDefinition(
                description="test string",
            ),
        }
    )
    template_data = {
        "test_string": 1,
    }
    parsed_config = TemplateConfig.model_validate(template_config)

    # WHEN
    data_model = parsed_config.data_model()
    parsed_data = data_model.model_validate(template_data)

    # THEN
    assert parsed_data.test_string == "1"
