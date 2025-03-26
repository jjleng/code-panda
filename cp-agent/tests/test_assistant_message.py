"""Tests for assistant message parsing."""

import pytest

from cp_agent.types import (
    AggressiveStreamingAssistantMessageParser,
    StreamingAssistantMessageParser,
    parse_assistant_message,
)
from cp_agent.types.assistant_message import TextEvent, ThinkingEvent, ToolEvent


def test_parse_simple_text() -> None:
    """Test parsing simple text content."""
    message = "Hello world"
    result = parse_assistant_message(message)

    assert len(result) == 1
    assert result[0]["type"] == "text"
    assert result[0]["content"] == "Hello world"
    assert result[0]["partial"] == True


def test_parse_empty_text() -> None:
    """Test parsing text content that becomes empty after trimming."""
    message = "   \n  \t  "
    result = parse_assistant_message(message)

    assert len(result) == 1
    assert result[0]["type"] == "text"
    assert result[0]["content"] == ""
    assert result[0]["partial"] == True


def test_parse_simple_tool_use() -> None:
    """Test parsing a simple tool use with one parameter."""
    message = "<read-file><path>test.txt</path></read-file>"
    result = parse_assistant_message(message)

    assert len(result) == 2  # Empty text + tool use
    assert result[0]["type"] == "text"
    assert result[0]["content"] == ""
    assert result[0]["partial"] == False
    assert result[1]["type"] == "tool_use"
    assert result[1]["name"] == "read-file"
    assert result[1]["params"] == {"path": "test.txt"}
    assert result[1]["partial"] == False


def test_parse_tool_use_multiple_params() -> None:
    """Test parsing a tool use with multiple parameters."""
    message = "<search-files><path>src</path><regex>test.*</regex><file-pattern>*.py</file-pattern></search-files>"
    result = parse_assistant_message(message)

    assert len(result) == 2  # Empty text + tool use
    assert result[0]["type"] == "text"
    assert result[0]["content"] == ""
    assert result[0]["partial"] == False
    assert result[1]["type"] == "tool_use"
    assert result[1]["name"] == "search-files"
    assert result[1]["params"] == {
        "path": "src",
        "regex": "test.*",
        "file-pattern": "*.py",
    }
    assert result[1]["partial"] == False


def test_parse_write_to_file_content() -> None:
    """Test parsing write-to-file with multiline content."""
    message = """<write-to-file>
<path>test.py</path>
<content>
def hello():
    print("Hello world")

if __name__ == "__main__":
    hello()
</content></write-to-file>"""
    result = parse_assistant_message(message)

    assert len(result) == 2  # Empty text + tool use
    assert result[0]["type"] == "text"
    assert result[0]["content"] == ""
    assert result[0]["partial"] == False
    assert result[1]["type"] == "tool_use"
    assert result[1]["name"] == "write-to-file"
    assert result[1]["params"]["path"] == "test.py"
    assert (
        result[1]["params"]["content"].strip()
        == """def hello():
    print("Hello world")

if __name__ == "__main__":
    hello()"""
    )
    assert result[1]["partial"] == False


def test_parse_mixed_content() -> None:
    """Test parsing a message with both text and tool use."""
    message = """Here's the content of the file:
<read-file><path>example.txt</path></read-file>
And here's what we'll do with it."""
    result = parse_assistant_message(message)

    assert len(result) == 3
    assert result[0]["type"] == "text"
    assert result[0]["content"] == "Here's the content of the file:"
    assert result[1]["type"] == "tool_use"
    assert result[1]["name"] == "read-file"
    assert result[2]["type"] == "text"
    assert result[2]["content"] == "And here's what we'll do with it."


def test_parse_empty_message() -> None:
    """Test parsing an empty message."""
    message = ""
    result = parse_assistant_message(message)

    assert len(result) == 0


def test_parse_invalid_tool_use() -> None:
    """Test parsing an invalid tool use format."""
    message = "<invalid-tool><param>value</param></invalid-tool>"
    result = parse_assistant_message(message)

    assert len(result) == 1
    assert result[0]["type"] == "text"
    assert result[0]["content"] == message
    assert result[0]["partial"] == True


def test_streaming_simple_text() -> None:
    """Test streaming parser with simple text content."""
    parser = StreamingAssistantMessageParser()

    results = list(parser("Hello "))
    assert len(results) == 1
    assert results[0]["type"] == "text"
    assert results[0]["content"] == "Hello "

    results = list(parser("world"))
    assert len(results) == 1
    assert results[0]["type"] == "text"
    assert results[0]["content"] == "world"


def test_streaming_thinking_block() -> None:
    """Test streaming parser with thinking blocks."""
    parser = StreamingAssistantMessageParser()

    results = list(parser("Let's analyze <thinking>"))
    assert len(results) == 1
    assert results[0]["type"] == "text"
    assert results[0]["content"] == "Let's analyze "

    results = list(parser("processing code"))
    assert len(results) == 0

    results = list(parser("</thinking>Done"))
    assert len(results) == 2
    assert results[0]["type"] == "thinking"
    assert results[0]["content"] == "processing code"
    assert results[1]["type"] == "text"
    assert results[1]["content"] == "Done"


def test_streaming_split_thinking_tags() -> None:
    """Test streaming parser with thinking tags split across chunks."""
    parser = StreamingAssistantMessageParser()

    results = list(parser("Start <think"))
    assert len(results) == 1
    assert results[0]["type"] == "text"
    assert results[0]["content"] == "Start "

    results = list(parser("ing>analyzing</thi"))
    assert len(results) == 0  # Partial tag

    results = list(parser("nking>End")) + list(parser(None))
    assert len(results) == 2
    assert results[0]["type"] == "thinking"
    assert results[0]["content"] == "analyzing"
    assert results[1]["type"] == "text"
    assert results[1]["content"] == "End"


def test_streaming_tool_use() -> None:
    """Test streaming parser with tool use sections."""
    parser = StreamingAssistantMessageParser()

    results = list(parser("Before <read-file>"))
    assert len(results) == 1
    assert results[0]["type"] == "text"
    assert results[0]["content"] == "Before "

    results = list(parser("<path>test.txt</path></read-file>"))
    assert len(results) == 0  # Tool use sections are ignored

    results = list(parser(" After"))
    assert len(results) == 1
    assert results[0]["type"] == "text"
    assert results[0]["content"] == " After"


def test_streaming_mixed_content() -> None:
    """Test streaming parser with mixed content types."""
    parser = StreamingAssistantMessageParser()

    all_results = []
    chunks = [
        "Let's see <thinking>Analyzing",
        " the file</thinking>Now",
        " <read-file><path>test.txt</path>",
        "</read-file> and <thinking>Processing",
        " results</thinking>Done",
    ]

    for chunk in chunks:
        results = list(parser(chunk))
        all_results.extend(results)

    assert len(all_results) == 7
    assert all_results[0]["type"] == "text"
    assert all_results[0]["content"] == "Let's see "
    assert all_results[1]["type"] == "thinking"
    assert all_results[1]["content"] == "Analyzing the file"
    assert all_results[2]["type"] == "text"
    assert all_results[2]["content"] == "Now"
    assert all_results[3]["type"] == "text"
    assert all_results[3]["content"] == " "
    assert all_results[4]["type"] == "text"
    assert all_results[4]["content"] == " and "
    assert all_results[5]["type"] == "thinking"
    assert all_results[5]["content"] == "Processing results"
    assert all_results[6]["type"] == "text"
    assert all_results[6]["content"] == "Done"


def test_streaming_empty_chunks() -> None:
    """Test streaming parser with empty chunks."""
    parser = StreamingAssistantMessageParser()

    results = list(parser(""))
    assert len(results) == 0

    results = list(parser("   "))
    assert len(results) == 1

    results = list(parser("\n\t"))
    assert len(results) == 1


def test_streaming_reset_state() -> None:
    """Test streaming parser state reset."""
    parser = StreamingAssistantMessageParser()

    # First message
    results = list(parser("<thinking>Analysis"))
    assert len(results) == 0

    # Reset state
    parser.reset_state()

    # Second message
    results = list(parser("New message"))
    assert len(results) == 1
    assert results[0]["type"] == "text"
    assert results[0]["content"] == "New message"


def test_aggressive_streaming_immediate_thinking() -> None:
    """Test aggressive streaming parser's immediate thinking content emission."""
    parser = AggressiveStreamingAssistantMessageParser()

    results = list(parser("<thinking>"))
    assert len(results) == 0

    results = list(parser("analyzing"))
    assert len(results) == 1
    assert isinstance(results[0], ThinkingEvent)
    assert results[0].text == "analyzing"

    results = list(parser(" code"))
    assert len(results) == 1
    assert isinstance(results[0], ThinkingEvent)
    assert results[0].text == " code"

    results = list(parser("</thinking>"))
    assert len(results) == 0


def test_aggressive_streaming_parameter_flushing() -> None:
    """Test aggressive streaming parser's parameter flushing behavior."""
    parser = AggressiveStreamingAssistantMessageParser()

    chunks = [
        "<read-file>",
        "<path>test.txt</path>",
        "<another-param>value</another-param>",
        "</read-file>",
    ]

    all_results = []
    for chunk in chunks:
        results = list(parser(chunk))
        all_results.extend(results)

    # First result should be ToolEvent with "started" status
    assert len(all_results) >= 1
    assert isinstance(all_results[0], ToolEvent)
    assert all_results[0].status == "started"
    assert all_results[0].tool_name == "read-file"

    # Last result should be ToolEvent with "executing" status
    assert isinstance(all_results[-1], ToolEvent)
    assert all_results[-1].status == "executing"


def test_aggressive_streaming_mixed_content_types() -> None:
    """Test aggressive streaming parser with mixed content types."""
    parser = AggressiveStreamingAssistantMessageParser()

    chunks = [
        "Let's analyze ",
        "<thinking>examining code</thinking>",
        " Now let's ",
        "<write-to-file><path>test.py</path>",
        "<content>print('hello')</content></write-to-file>",
        " Done",
    ]

    all_results = []
    for chunk in chunks:
        results = list(parser(chunk))
        all_results.extend(results)

    assert len(all_results) >= 7  # At least 7 events including tool events
    assert isinstance(all_results[0], TextEvent)
    assert all_results[0].text == "Let's analyze "
    assert isinstance(all_results[1], ThinkingEvent)
    assert all_results[1].text == "examining code"
    assert isinstance(all_results[2], TextEvent)
    assert all_results[2].text == " Now let's "

    # Find write-to-file events
    tool_events = [e for e in all_results if isinstance(e, ToolEvent)]
    assert len(tool_events) == 4  # started, partial(path), partial(content), executing
    assert tool_events[0].status == "started"
    assert tool_events[0].tool_name == "write-to-file"
    assert tool_events[0].params is None

    assert tool_events[1].status == "partial"
    assert tool_events[1].tool_name == "write-to-file"
    assert tool_events[1].params == {"path": "test.py"}

    assert tool_events[2].status == "partial"
    assert tool_events[2].tool_name == "write-to-file"
    assert tool_events[2].params == {"path": "test.py", "content": "print('hello')"}

    assert tool_events[3].status == "executing"
    assert tool_events[3].tool_name == "write-to-file"
    assert tool_events[3].params == {"path": "test.py", "content": "print('hello')"}

    assert isinstance(all_results[-1], TextEvent)
    assert all_results[-1].text == " Done"


def test_aggressive_streaming_split_thinking() -> None:
    """Test aggressive streaming parser with thinking content split across chunks."""
    parser = AggressiveStreamingAssistantMessageParser()

    chunks = [
        "<thinking>First ",
        "analyzing the ",
        "code structure",
        " and then ",
        "planning changes</thinking>",
    ]

    all_results = []
    for chunk in chunks:
        results = list(parser(chunk))
        all_results.extend(results)

    # Should have individual thinking chunks for each content piece
    assert len(all_results) == 5
    assert all(isinstance(chunk, ThinkingEvent) for chunk in all_results)

    # Now safe to check text since we've confirmed they're all ThinkingEvent
    thinking_events = [
        event for event in all_results if isinstance(event, ThinkingEvent)
    ]
    assert thinking_events[0].text == "First "
    assert thinking_events[1].text == "analyzing the "
    assert thinking_events[2].text == "code structure"
    assert thinking_events[3].text == " and then "
    assert thinking_events[4].text == "planning changes"


def test_aggressive_streaming_split_tool_tags() -> None:
    """Test aggressive streaming parser with tool and parameter tags split across chunks."""
    parser = AggressiveStreamingAssistantMessageParser()

    chunks = [
        "Let's write ",
        "<write-to",
        "-file><p",
        "ath>test.py</pat",
        "h><cont",
        "ent>print('hello')</co",
        "ntent></write-to-file>",
        " Done",
    ]

    all_results = []
    for chunk in chunks:
        results = list(parser(chunk))
        all_results.extend(results)

    assert len(all_results) >= 4  # At least text + started + partial + executing
    assert isinstance(all_results[0], TextEvent)
    assert all_results[0].text == "Let's write "

    # Find write-to-file events
    tool_events = [e for e in all_results if isinstance(e, ToolEvent)]
    assert len(tool_events) == 4  # started, partial(path), partial(content), executing
    assert tool_events[0].status == "started"
    assert tool_events[0].tool_name == "write-to-file"
    assert tool_events[0].params is None

    assert tool_events[1].status == "partial"
    assert tool_events[1].tool_name == "write-to-file"
    assert tool_events[1].params == {"path": "test.py"}

    assert tool_events[2].status == "partial"
    assert tool_events[2].tool_name == "write-to-file"
    assert tool_events[2].params == {"path": "test.py", "content": "print('hello')"}

    assert tool_events[3].status == "executing"
    assert tool_events[3].tool_name == "write-to-file"
    assert tool_events[3].params == {"path": "test.py", "content": "print('hello')"}

    assert isinstance(all_results[-1], TextEvent)
    assert all_results[-1].text == " Done"


def test_aggressive_streaming_non_tool_tags() -> None:
    """Test aggressive streaming parser correctly handles non-tool/non-thinking HTML-like tags."""
    parser = AggressiveStreamingAssistantMessageParser()

    chunks = [
        "Let's look at this ",
        "<div>HTML content</div>",
        " and also some ",
        "<span>inline elements</span>",
        " before <thinking>actual thinking</thinking>",
        " and <read-file><path>test.txt</path></read-file>",
    ]

    all_results = []
    for chunk in chunks:
        results = list(parser(chunk))
        all_results.extend(results)

    # Check text content is preserved with HTML tags
    text_events = [e for e in all_results if isinstance(e, TextEvent)]
    assert len(text_events) >= 4  # Should have multiple text segments
    assert text_events[0].text == "Let's look at this "
    assert text_events[1].text == "<div>HTML content</div>"
    assert text_events[2].text == " and also some "
    assert text_events[3].text == "<span>inline elements</span>"

    # Verify thinking block still works
    thinking_events = [e for e in all_results if isinstance(e, ThinkingEvent)]
    assert len(thinking_events) == 1
    assert thinking_events[0].text == "actual thinking"

    # Verify tool events still work
    tool_events = [e for e in all_results if isinstance(e, ToolEvent)]
    assert len(tool_events) >= 2  # At least started and executing states
    assert tool_events[0].tool_name == "read-file"
    assert tool_events[0].status == "started"


def test_aggressive_streaming_html_in_tool_params() -> None:
    """Test HTML-like tags within tool parameters are preserved."""
    parser = AggressiveStreamingAssistantMessageParser()

    chunks = [
        "<write-to-file><path>test.html</path><content>",
        "<div>Some content</div>",
        "<span>More content</span>",
        "</content></write-to-file>",
    ]

    all_results = []
    for chunk in chunks:
        results = list(parser(chunk))
        all_results.extend(results)

    # Find write-to-file events
    tool_events = [e for e in all_results if isinstance(e, ToolEvent)]
    assert len(tool_events) >= 3  # started, partial, executing
    assert tool_events[0].status == "started"
    assert tool_events[-1].status == "executing"

    # Check HTML tags are preserved in content parameter
    final_content = tool_events[-1].params["content"]  # type: ignore
    assert "<div>Some content</div>" in final_content
    assert "<span>More content</span>" in final_content


def test_aggressive_streaming_jsx_tags() -> None:
    """Test aggressive streaming parser correctly handles JSX-style tags."""
    parser = AggressiveStreamingAssistantMessageParser()

    chunks = [
        "Here's a route: ",
        '<Route path="/login" element={<Login />} />',
        " and in a tool: ",
        "<write-to-file><path>src/routes.tsx</path><content>",
        "export const Routes = () => (",
        "  <Router>",
        '    <Route path="/login" element={<Login />} />',
        '    <Route path="/home" element={<Home />} />',
        "  </Router>",
        ")",
        "</content></write-to-file>",
    ]

    all_results = []
    for chunk in chunks:
        results = list(parser(chunk))
        all_results.extend(results)

    # Verify JSX in regular text
    text_events = [e for e in all_results if isinstance(e, TextEvent)]
    assert len(text_events) >= 2
    assert text_events[0].text == "Here's a route: "
    assert text_events[1].text == '<Route path="/login" element={<Login />} />'

    # Verify JSX in tool parameters
    tool_events = [e for e in all_results if isinstance(e, ToolEvent)]
    assert len(tool_events) >= 2  # started and executing
    assert tool_events[-1].status == "executing"

    final_content = tool_events[-1].params["content"]  # type: ignore
    assert '<Route path="/login" element={<Login />} />' in final_content
    assert '<Route path="/home" element={<Home />} />' in final_content


def test_aggressive_streaming_split_className_tags() -> None:
    """Test aggressive streaming parser with HTML/JSX tags containing className split across chunks."""
    parser = AggressiveStreamingAssistantMessageParser()

    chunks = [
        '<p className="',
        "mb-8",
        "text-lg text",
        "-muted-",
        "fore",
        'ground">\n',
        "A",
        " modern",
        " web",
        " application template",
        " built with the",
        " latest technologies",
        "\n        </p>",
    ]

    all_results = []
    for chunk in chunks:
        results = list(parser(chunk))
        all_results.extend(results)

    # All chunks should be treated as text events since they're not tool or thinking blocks
    text_events = [e for e in all_results if isinstance(e, TextEvent)]

    # Verify the complete text matches the expected HTML/JSX
    combined_text = "".join(e.text for e in text_events)
    expected_text = '<p className="mb-8text-lg text-muted-foreground">\nA modern web application template built with the latest technologies\n        </p>'
    assert combined_text == expected_text
