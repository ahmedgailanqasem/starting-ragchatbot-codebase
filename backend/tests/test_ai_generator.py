"""
Tests for AIGenerator and its tool calling behavior
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from ai_generator import AIGenerator


class TestAIGeneratorBasics:
    """Basic tests for AIGenerator initialization and configuration"""

    def test_initialization(self):
        """Test AIGenerator initializes correctly"""
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

        assert generator.model == "claude-sonnet-4-20250514"
        assert generator.base_params["model"] == "claude-sonnet-4-20250514"
        assert generator.base_params["temperature"] == 0
        assert generator.base_params["max_tokens"] == 800

    def test_system_prompt_exists(self):
        """Test that system prompt is defined"""
        assert hasattr(AIGenerator, 'SYSTEM_PROMPT')
        assert len(AIGenerator.SYSTEM_PROMPT) > 0
        assert "course" in AIGenerator.SYSTEM_PROMPT.lower()


class TestAIGeneratorToolCalling:
    """Tests for AIGenerator tool calling behavior"""

    @patch('anthropic.Anthropic')
    def test_generate_response_without_tools(self, mock_anthropic):
        """Test generating response without tools"""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Create generator and test
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        response = generator.generate_response(query="What is RAG?")

        # Verify
        assert response == "Test response"
        assert mock_client.messages.create.called
        call_args = mock_client.messages.create.call_args[1]
        assert "tools" not in call_args

    @patch('anthropic.Anthropic')
    def test_generate_response_with_tools_provided(self, mock_anthropic):
        """Test that tools are passed to API when provided"""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Create generator and test
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        tools = [{"name": "test_tool", "description": "A test tool"}]
        response = generator.generate_response(
            query="What is RAG?",
            tools=tools
        )

        # Verify tools were passed
        call_args = mock_client.messages.create.call_args[1]
        assert "tools" in call_args
        assert call_args["tools"] == tools
        assert "tool_choice" in call_args
        assert call_args["tool_choice"] == {"type": "auto"}

    @patch('anthropic.Anthropic')
    def test_tool_use_triggers_execution(self, mock_anthropic):
        """Test that tool_use stop_reason triggers tool execution"""
        # Setup mock for initial response with tool use
        mock_client = Mock()

        # First response - tool use
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_course_content"
        mock_tool_block.id = "tool_123"
        mock_tool_block.input = {"query": "What is RAG?"}

        initial_response = Mock()
        initial_response.content = [mock_tool_block]
        initial_response.stop_reason = "tool_use"

        # Second response - final answer
        final_response = Mock()
        final_response.content = [Mock(text="Final answer")]
        final_response.stop_reason = "end_turn"

        # Configure mock to return different responses
        mock_client.messages.create.side_effect = [initial_response, final_response]
        mock_anthropic.return_value = mock_client

        # Create mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        # Test
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        tools = [{"name": "search_course_content"}]
        response = generator.generate_response(
            query="What is RAG?",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Verify tool was executed
        assert mock_tool_manager.execute_tool.called
        assert response == "Final answer"
        assert mock_client.messages.create.call_count == 2

    @patch('anthropic.Anthropic')
    def test_tool_execution_params_passed_correctly(self, mock_anthropic):
        """Test that tool parameters are passed correctly to tool manager"""
        # Setup mocks
        mock_client = Mock()

        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_course_content"
        mock_tool_block.id = "tool_123"
        mock_tool_block.input = {
            "query": "What is RAG?",
            "course_name": "Test Course"
        }

        initial_response = Mock()
        initial_response.content = [mock_tool_block]
        initial_response.stop_reason = "tool_use"

        final_response = Mock()
        final_response.content = [Mock(text="Final answer")]
        final_response.stop_reason = "end_turn"

        mock_client.messages.create.side_effect = [initial_response, final_response]
        mock_anthropic.return_value = mock_client

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        # Test
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        tools = [{"name": "search_course_content"}]
        generator.generate_response(
            query="Test query",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Verify tool was called with correct params
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content",
            query="What is RAG?",
            course_name="Test Course"
        )

    @patch('anthropic.Anthropic')
    def test_conversation_history_included(self, mock_anthropic):
        """Test that conversation history is included in API call"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Test
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        history = "Previous conversation context"
        generator.generate_response(
            query="What is RAG?",
            conversation_history=history
        )

        # Verify history was included in system prompt
        call_args = mock_client.messages.create.call_args[1]
        assert "system" in call_args
        assert history in call_args["system"]

    @patch('anthropic.Anthropic')
    def test_tool_results_added_to_messages(self, mock_anthropic):
        """Test that tool results are properly added to message history"""
        mock_client = Mock()

        # Tool use response
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_course_content"
        mock_tool_block.id = "tool_123"
        mock_tool_block.input = {"query": "test"}

        initial_response = Mock()
        initial_response.content = [mock_tool_block]
        initial_response.stop_reason = "tool_use"

        # Final response
        final_response = Mock()
        final_response.content = [Mock(text="Final")]
        final_response.stop_reason = "end_turn"

        mock_client.messages.create.side_effect = [initial_response, final_response]
        mock_anthropic.return_value = mock_client

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Search results here"

        # Test
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        generator.generate_response(
            query="test",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Check second API call (final response)
        second_call_args = mock_client.messages.create.call_args_list[1][1]
        messages = second_call_args["messages"]

        # Should have: [user message, assistant tool use, user tool result]
        assert len(messages) >= 3
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"

        # Tool result should be in the last message
        tool_result = messages[2]["content"][0]
        assert tool_result["type"] == "tool_result"
        assert tool_result["tool_use_id"] == "tool_123"
        assert tool_result["content"] == "Search results here"

    @patch('anthropic.Anthropic')
    def test_tools_available_until_claude_finishes(self, mock_anthropic):
        """Test that tools remain available until Claude naturally finishes"""
        mock_client = Mock()

        # Tool use response
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_course_content"
        mock_tool_block.id = "tool_123"
        mock_tool_block.input = {"query": "test"}

        initial_response = Mock()
        initial_response.content = [mock_tool_block]
        initial_response.stop_reason = "tool_use"

        final_response = Mock()
        final_response.content = [Mock(text="Final")]
        final_response.stop_reason = "end_turn"

        mock_client.messages.create.side_effect = [initial_response, final_response]
        mock_anthropic.return_value = mock_client

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Results"

        # Test
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        result = generator.generate_response(
            query="test",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # With new sequential calling, tools remain available in the second call
        # Claude can decide to use them again or finish
        second_call_args = mock_client.messages.create.call_args_list[1][1]
        assert "tools" in second_call_args, "Tools should be available for potential second round"
        assert result == "Final"


class TestAIGeneratorEdgeCases:
    """Edge case tests for AIGenerator"""

    @patch('anthropic.Anthropic')
    def test_multiple_tool_calls_in_response(self, mock_anthropic):
        """Test handling multiple tool calls in single response"""
        mock_client = Mock()

        # Response with multiple tool uses
        mock_tool_1 = Mock()
        mock_tool_1.type = "tool_use"
        mock_tool_1.name = "search_course_content"
        mock_tool_1.id = "tool_1"
        mock_tool_1.input = {"query": "test1"}

        mock_tool_2 = Mock()
        mock_tool_2.type = "tool_use"
        mock_tool_2.name = "get_course_outline"
        mock_tool_2.id = "tool_2"
        mock_tool_2.input = {"course_name": "test"}

        initial_response = Mock()
        initial_response.content = [mock_tool_1, mock_tool_2]
        initial_response.stop_reason = "tool_use"

        final_response = Mock()
        final_response.content = [Mock(text="Final")]
        final_response.stop_reason = "end_turn"

        mock_client.messages.create.side_effect = [initial_response, final_response]
        mock_anthropic.return_value = mock_client

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Result"

        # Test
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        generator.generate_response(
            query="test",
            tools=[{"name": "search_course_content"}, {"name": "get_course_outline"}],
            tool_manager=mock_tool_manager
        )

        # Both tools should be executed
        assert mock_tool_manager.execute_tool.call_count == 2

    @patch('anthropic.Anthropic')
    def test_tool_use_without_tool_manager(self, mock_anthropic):
        """Test that tool_use without tool_manager doesn't crash"""
        mock_client = Mock()

        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_course_content"
        mock_tool_block.id = "tool_123"
        mock_tool_block.input = {"query": "test"}

        response = Mock()
        response.content = [mock_tool_block]
        response.stop_reason = "tool_use"

        mock_client.messages.create.return_value = response
        mock_anthropic.return_value = mock_client

        # Test without tool_manager - should not crash
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        result = generator.generate_response(
            query="test",
            tools=[{"name": "search_course_content"}]
            # Note: no tool_manager provided
        )

        # Should handle gracefully (returns content from tool_use response)
        assert result is not None


class TestSequentialToolCalling:
    """Tests for sequential/multi-round tool calling"""

    @patch('anthropic.Anthropic')
    def test_two_sequential_tool_calls(self, mock_anthropic):
        """Test that Claude can make 2 sequential tool calls"""
        mock_client = Mock()

        # Round 1: First tool use
        tool_1 = Mock()
        tool_1.type = "tool_use"
        tool_1.name = "get_course_outline"
        tool_1.id = "tool_1"
        tool_1.input = {"course_name": "RAG"}

        response_1 = Mock()
        response_1.content = [tool_1]
        response_1.stop_reason = "tool_use"

        # Round 2: Second tool use after seeing first results
        tool_2 = Mock()
        tool_2.type = "tool_use"
        tool_2.name = "search_course_content"
        tool_2.id = "tool_2"
        tool_2.input = {"query": "lesson 3"}

        response_2 = Mock()
        response_2.content = [tool_2]
        response_2.stop_reason = "tool_use"

        # Final: Text response
        final_response = Mock()
        final_response.content = [Mock(text="Final answer with both tool results")]
        final_response.stop_reason = "end_turn"

        mock_client.messages.create.side_effect = [response_1, response_2, final_response]
        mock_anthropic.return_value = mock_client

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        # Test
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        result = generator.generate_response(
            query="What's in lesson 3 of RAG course?",
            tools=[{"name": "get_course_outline"}, {"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Verify both tools executed
        assert mock_tool_manager.execute_tool.call_count == 2
        assert result == "Final answer with both tool results"

        # Verify API called 3 times (round 1, round 2, final)
        assert mock_client.messages.create.call_count == 3

    @patch('anthropic.Anthropic')
    def test_single_tool_call_still_works(self, mock_anthropic):
        """Test that single tool call path still works (backward compatible)"""
        mock_client = Mock()

        # Single tool use
        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.name = "search_course_content"
        tool_block.id = "tool_1"
        tool_block.input = {"query": "RAG"}

        response_1 = Mock()
        response_1.content = [tool_block]
        response_1.stop_reason = "tool_use"

        # Immediate final answer
        final_response = Mock()
        final_response.content = [Mock(text="Answer about RAG")]
        final_response.stop_reason = "end_turn"

        mock_client.messages.create.side_effect = [response_1, final_response]
        mock_anthropic.return_value = mock_client

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "RAG info"

        # Test
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        result = generator.generate_response(
            query="What is RAG?",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Only one tool executed
        assert mock_tool_manager.execute_tool.call_count == 1
        assert result == "Answer about RAG"
        # Only 2 API calls (tool request + final answer)
        assert mock_client.messages.create.call_count == 2

    @patch('anthropic.Anthropic')
    def test_max_rounds_enforced(self, mock_anthropic):
        """Test that max rounds limit is enforced"""
        mock_client = Mock()

        # Claude keeps requesting tools (simulate infinite loop)
        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.name = "search_course_content"
        tool_block.id = "tool_x"
        tool_block.input = {"query": "test"}

        tool_response = Mock()
        tool_response.content = [tool_block]
        tool_response.stop_reason = "tool_use"

        # Final forced response
        final_response = Mock()
        final_response.content = [Mock(text="Forced final answer")]
        final_response.stop_reason = "end_turn"

        # Return tool_use 3 times, then final (should be cut off at 2)
        mock_client.messages.create.side_effect = [
            tool_response,  # Round 1
            tool_response,  # Round 2
            final_response  # Forced final (no tools)
        ]
        mock_anthropic.return_value = mock_client

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Result"

        # Test
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        result = generator.generate_response(
            query="test",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Should execute tools exactly 2 times (max_rounds)
        assert mock_tool_manager.execute_tool.call_count == 2
        # Should make 3 API calls (round 1, round 2, forced final)
        assert mock_client.messages.create.call_count == 3
        assert result == "Forced final answer"

    @patch('anthropic.Anthropic')
    def test_tools_available_during_rounds(self, mock_anthropic):
        """Test that tools remain available during iterative rounds"""
        mock_client = Mock()

        # Two rounds of tool use
        tool_1 = Mock()
        tool_1.type = "tool_use"
        tool_1.name = "search_course_content"
        tool_1.id = "tool_1"
        tool_1.input = {"query": "test1"}

        response_1 = Mock()
        response_1.content = [tool_1]
        response_1.stop_reason = "tool_use"

        tool_2 = Mock()
        tool_2.type = "tool_use"
        tool_2.name = "search_course_content"
        tool_2.id = "tool_2"
        tool_2.input = {"query": "test2"}

        response_2 = Mock()
        response_2.content = [tool_2]
        response_2.stop_reason = "tool_use"

        final_response = Mock()
        final_response.content = [Mock(text="Done")]
        final_response.stop_reason = "end_turn"

        mock_client.messages.create.side_effect = [response_1, response_2, final_response]
        mock_anthropic.return_value = mock_client

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Result"

        # Test
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        generator.generate_response(
            query="test",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Check that tools were in the second API call
        second_call_args = mock_client.messages.create.call_args_list[1][1]
        assert "tools" in second_call_args
        assert second_call_args["tools"] == [{"name": "search_course_content"}]

    @patch('anthropic.Anthropic')
    def test_tool_execution_error_terminates(self, mock_anthropic):
        """Test that tool execution error terminates the loop"""
        mock_client = Mock()

        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.name = "search_course_content"
        tool_block.id = "tool_1"
        tool_block.input = {"query": "test"}

        response = Mock()
        response.content = [tool_block]
        response.stop_reason = "tool_use"

        mock_client.messages.create.return_value = response
        mock_anthropic.return_value = mock_client

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = Exception("Tool failed")

        # Test
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        result = generator.generate_response(
            query="test",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Should return error message
        assert "Error executing tool" in result
        assert "Tool failed" in result

    @patch('anthropic.Anthropic')
    def test_message_accumulation_across_rounds(self, mock_anthropic):
        """Test that messages accumulate correctly across rounds"""
        mock_client = Mock()

        # Round 1
        tool_1 = Mock()
        tool_1.type = "tool_use"
        tool_1.name = "get_course_outline"
        tool_1.id = "tool_1"
        tool_1.input = {"course_name": "test"}

        response_1 = Mock()
        response_1.content = [tool_1]
        response_1.stop_reason = "tool_use"

        # Round 2
        tool_2 = Mock()
        tool_2.type = "tool_use"
        tool_2.name = "search_course_content"
        tool_2.id = "tool_2"
        tool_2.input = {"query": "test"}

        response_2 = Mock()
        response_2.content = [tool_2]
        response_2.stop_reason = "tool_use"

        # Final
        final_response = Mock()
        final_response.content = [Mock(text="Done")]
        final_response.stop_reason = "end_turn"

        mock_client.messages.create.side_effect = [response_1, response_2, final_response]
        mock_anthropic.return_value = mock_client

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Result"

        # Test
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
        generator.generate_response(
            query="test query",
            tools=[{"name": "get_course_outline"}, {"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Check final API call has all messages
        final_call_args = mock_client.messages.create.call_args_list[2][1]
        messages = final_call_args["messages"]

        # Should have: user_query, assistant_tool1, user_results1, assistant_tool2, user_results2
        assert len(messages) >= 5
        assert messages[0]["role"] == "user"  # Original query
        assert messages[1]["role"] == "assistant"  # Tool use 1
        assert messages[2]["role"] == "user"  # Tool results 1
        assert messages[3]["role"] == "assistant"  # Tool use 2
        assert messages[4]["role"] == "user"  # Tool results 2
