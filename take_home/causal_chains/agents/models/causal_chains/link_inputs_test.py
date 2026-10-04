from decimal import Decimal

from take_home.causal_chains.agents.models.causal_chains.input_variable import (
    InputVariable,
)
from take_home.causal_chains.agents.models.causal_chains.link_inputs import LinkInputs


def test_input_variable_schema_is_a_number_without_a_lookahead():
    schema = InputVariable.model_json_schema()
    value = schema["properties"]["value"]
    assert value["type"] == "number"
    assert value["minimum"] == 0
    assert value["maximum"] == 1
    assert "(?" not in str(schema)


def test_link_inputs_hold_values_and_not_a_probability():
    quoted = LinkInputs(
        inputs=[InputVariable(name="deal_odds", value=Decimal("0.08"))]
    )
    assert "p" not in LinkInputs.model_fields
    assert quoted.inputs[0].value == Decimal("0.08")
    assert (
        LinkInputs.model_json_schema()["properties"]["inputs"]["description"]
        == "Named values between 0 and 1 for a driver that could change the situation."
    )
