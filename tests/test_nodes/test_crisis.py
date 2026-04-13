"""Tests for the emergency_responder node (pure logic, no LLM)."""

from __future__ import annotations

from logic_graph.nodes.crisis import emergency_responder


class TestEmergencyResponder:
    def test_returns_dict_with_generated_response(self):
        result = emergency_responder({})
        assert isinstance(result, dict)
        assert "generated_response" in result

    def test_returns_emergency_text_field(self):
        result = emergency_responder({})
        assert "emergency_text" in result
        assert isinstance(result["emergency_text"], str)
        assert len(result["emergency_text"]) > 0

    def test_response_is_nonempty_string(self):
        result = emergency_responder({})
        assert isinstance(result["generated_response"], str)
        assert len(result["generated_response"]) > 0

    def test_response_contains_icbf_line_106(self):
        result = emergency_responder({})
        assert "106" in result["generated_response"]

    def test_response_contains_linea_de_la_vida_141(self):
        result = emergency_responder({})
        assert "141" in result["generated_response"]

    def test_response_contains_emergencias_123(self):
        result = emergency_responder({})
        assert "123" in result["generated_response"]

    def test_response_mentions_colombia_helplines(self):
        """Verify the response references Colombian context."""
        response = emergency_responder({})["generated_response"]
        assert "Colombia" in response

    def test_response_is_deterministic(self):
        """emergency_responder returns fixed text, so two calls with empty state match."""
        r1 = emergency_responder({})
        r2 = emergency_responder({})
        assert r1 == r2

    def test_appends_to_existing_generated_response(self):
        """When crisis_agent already set generated_response, its text is preserved."""
        prior = "Texto empático del crisis_agent."
        result = emergency_responder({"generated_response": prior})
        combined = result["generated_response"]
        assert combined.startswith(prior)
        assert "106" in combined
        assert result["emergency_text"] not in combined[:len(prior)]  # prior part intact
