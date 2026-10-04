from take_home.causal_chains.agents.models.causal_chains.input_variable import (
    InputVariable,
)
from take_home.causal_chains.agents.models.causal_chains.link_inputs import LinkInputs


def test_input_variable_fields():
    schema = InputVariable.model_json_schema()
    properties = schema["properties"]
    probability_field = properties["probability"]
    assert probability_field["type"] == "number"
    assert probability_field["minimum"] == 0
    assert probability_field["maximum"] == 1
    assert "(?" not in str(schema)
    assert properties["name"]["description"] == "A short name for this input."
    assert (
        properties["desc"]["description"]
        == "What this input is, and why this driver could change the situation."
    )
    assert (
        probability_field["description"]
        == "A number between 0 and 1 for a driver that could change the situation."
    )


def test_link_inputs_hold_values_and_not_a_probability():
    quoted = LinkInputs(
        inputs=[
            InputVariable(
                name="deal_odds",
                desc="Odds of a deal.",
                probability=0.08,
            )
        ]
    )
    assert "p" not in LinkInputs.model_fields
    assert quoted.inputs[0].probability == 0.08
    assert (
        LinkInputs.model_json_schema()["properties"]["inputs"]["description"]
        == "Named values between 0 and 1 for a driver that could change the situation."
    )
