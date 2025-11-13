import anthropic
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to tools for retrieving course information.

Tool Selection Guide:
- **Course outline queries** (structure, lessons, what's covered, course overview): Use `get_course_outline` tool
  - Returns course title, course link, instructor, and complete lesson list with titles and links
  - Use for questions like "What lessons are in X course?" or "What does the course cover?"
- **Specific content questions** (details about topics, concepts, explanations): Use `search_course_content` tool
  - Returns relevant content chunks from course materials
  - Use for questions about specific topics or concepts

Tool Usage Rules:
- **You can make up to TWO sequential tool calls per query if needed**
- **When to use multiple tools:**
  - First call: Get course outline to see lesson structure
  - Second call: Search specific lesson content based on outline
  - Or: First search for one aspect, then refine with second search for complementary information
  - Or: Search different lessons/courses to compare information
- **When to use single tool:**
  - Question is straightforward and answerable with one search
  - Outline alone is sufficient (for structure questions)
- **Always prefer fewer tool calls when possible** - if first tool gives you enough information, synthesize immediately
- After seeing tool results, decide:
  1. Make another tool call if you need complementary information
  2. Provide final answer if you have sufficient information
- Synthesize all tool results into accurate, fact-based responses
- If tool yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without using tools
- **Course outline questions**: Use get_course_outline, then present the complete lesson structure
  - Always include: course title, course link, total number of lessons, and all lesson titles with their numbers
- **Course content questions**: Use search_course_content (and optionally outline first), then answer based on retrieved content
- **No meta-commentary**:
  - Provide direct answers only — no reasoning process, tool usage explanations, or question-type analysis
  - Do not mention "based on the search results" or "using the tool"
  - Do not explain why you made multiple tool calls

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        
        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            
        Returns:
            Generated response as string
        """
        
        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }
        
        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}
        
        # Get response from Claude
        response = self.client.messages.create(**api_params)
        
        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution(response, api_params, tool_manager)
        
        # Return direct response
        return response.content[0].text
    
    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager, max_rounds: int = 2):
        """
        Handle execution of tool calls with support for sequential rounds.

        Supports up to max_rounds of tool calling, where Claude can:
        1. Make a tool call and see results
        2. Decide if another tool call is needed
        3. Make a second tool call (if needed)
        4. Generate final answer

        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools
            max_rounds: Maximum number of tool calling rounds (default: 2)

        Returns:
            Final response text after tool execution
        """
        # Start with existing messages
        messages = base_params["messages"].copy()

        # Track state across rounds
        current_round = 0
        current_response = initial_response

        # Iterative loop for multiple tool rounds
        while current_round < max_rounds:
            current_round += 1
            print(f"[Tool Round {current_round}/{max_rounds}]")

            # Add AI's tool use response to messages
            messages.append({"role": "assistant", "content": current_response.content})

            # Execute all tool calls in this round
            tool_results = []
            try:
                for content_block in current_response.content:
                    if content_block.type == "tool_use":
                        print(f"  Executing: {content_block.name}")
                        tool_result = tool_manager.execute_tool(
                            content_block.name,
                            **content_block.input
                        )

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": tool_result
                        })
            except Exception as e:
                # Tool execution error - terminate loop and return error
                print(f"  Error executing tool: {e}")
                return f"Error executing tool: {str(e)}"

            # Add tool results to messages
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

            # Prepare next API call - KEEP tools available
            next_params = {
                **self.base_params,
                "messages": messages,
                "system": base_params["system"],
                "tools": base_params.get("tools"),  # Tools still available
                "tool_choice": {"type": "auto"}
            }

            # Make next API call
            next_response = self.client.messages.create(**next_params)

            # Check if Claude wants to continue with tools
            if next_response.stop_reason != "tool_use":
                # Claude provided text answer - we're done!
                print(f"  Claude finished after {current_round} round(s)")
                return self._extract_text(next_response)

            # Check if we've hit max rounds
            if current_round >= max_rounds:
                # Max rounds reached - force final answer without tools
                print(f"  Max rounds reached - forcing final answer")
                break

            # Continue to next round
            current_response = next_response

        # If we exit the loop, make final call WITHOUT tools to force synthesis
        print(f"  Making forced final call without tools")
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"]
            # No tools parameter - forces text response
        }

        final_response = self.client.messages.create(**final_params)
        return self._extract_text(final_response)

    def _extract_text(self, response) -> str:
        """
        Extract text content from API response.

        Args:
            response: Anthropic API response object

        Returns:
            Text content from the response
        """
        if response.content and len(response.content) > 0:
            # Handle multiple content blocks (extract all text)
            text_parts = []
            for block in response.content:
                if hasattr(block, 'text'):
                    text_parts.append(block.text)
            return "\n".join(text_parts) if text_parts else "No response generated"
        return "No response generated"