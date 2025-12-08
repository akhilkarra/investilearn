# mypy: disable-error-code="union-attr,index"
"""Prominent LLM Coach panel for main dashboard"""

import streamlit as st

from utils.llm_coach import get_coach


@st.dialog("💬 Investment Coach", width="large")
def render_coach_panel(company_context: dict | None = None, auto_prompt: str | None = None) -> None:
    """
    Render the LLM coach in a modal dialog with scrollable chat

    Args:
        company_context: Optional company/metric context for questions
        auto_prompt: Optional prompt to automatically ask on open
    """

    # Initialize chat history in session state
    if "coach_messages" not in st.session_state:
        st.session_state.coach_messages = []

    if "coach_model" not in st.session_state:
        st.session_state.coach_model = "qwen2.5:14b"

    # Check coach availability
    coach = get_coach(model=st.session_state.coach_model)
    available, status_msg = coach.check_availability()

    if not available:
        st.error(f"❌ Coach unavailable: {status_msg}")
        st.caption(
            "Make sure Ollama is running and the model is downloaded:\n"
            f"```bash\nollama pull {st.session_state.coach_model}\n```"
        )
        return

    st.success(f"✅ Ready ({st.session_state.coach_model})")

    # Confidence filter inside dialog for real-time updates
    st.markdown("**🔍 Confidence Filter:**")
    confidence_display = st.select_slider(
        "Minimum confidence level",
        options=["Any (show all)", "Medium or higher", "High only"],
        value="Medium or higher",
        help="Filter responses based on AI confidence",
        label_visibility="collapsed",
        key="coach_confidence_filter",
    )

    # Map display values to internal values
    confidence_map = {"Any (show all)": "low", "Medium or higher": "medium", "High only": "high"}
    user_threshold = confidence_map.get(confidence_display, "medium")
    confidence_levels = {"low": 0, "medium": 1, "high": 2}
    threshold_level = confidence_levels.get(user_threshold, 0)

    st.divider()

    # Scrollable chat container
    chat_container = st.container(height=400)

    with chat_container:
        # Display chat history with dynamic filtering
        for msg in st.session_state.coach_messages:
            with st.chat_message(msg["role"]):
                # For user messages, just show the content
                if msg["role"] == "user":
                    st.markdown(msg["content"])

                # For assistant messages, check threshold
                elif msg["role"] == "assistant" and "confidence" in msg:
                    confidence = msg["confidence"]
                    response_level = confidence_levels.get(confidence, 0)

                    # Check if this message meets current threshold
                    if response_level < threshold_level:
                        # Show filtered message
                        st.error(
                            f"🚨 **FILTERED: {confidence.upper()} confidence** "
                            f"(your filter: {user_threshold.upper()}+)"
                        )
                        with st.expander("⚠️ Show filtered response"):
                            st.markdown(msg["content"])
                            if "confidence_explanation" in msg:
                                with st.expander("❓ Why this confidence level?"):
                                    st.caption(msg["confidence_explanation"])
                    else:
                        # Show message normally
                        st.markdown(msg["content"])

                        # Confidence badge
                        if confidence == "high":
                            st.success("🟢 **High Confidence** - Reliable information")
                        elif confidence == "medium":
                            st.warning("🟡 **Medium Confidence** - Consider verifying")
                        elif confidence == "low":
                            st.error("🔴 **Low Confidence** - Consult additional sources")

                        # "Why this confidence?" explanation
                        if "confidence_explanation" in msg:
                            with st.expander("❓ Why this confidence level?"):
                                st.caption(msg["confidence_explanation"])

    # Handle auto-prompt if provided
    auto_prompt_to_process = None
    if auto_prompt:
        auto_prompt_to_process = auto_prompt
    elif "coach_auto_prompt" in st.session_state:
        auto_prompt_to_process = st.session_state.coach_auto_prompt
        st.session_state.pop("coach_auto_prompt", None)

    # Chat input
    prompt = st.chat_input("Ask about investing concepts...", key="coach_input")

    # Process either manual prompt or auto prompt
    if prompt or auto_prompt_to_process:
        prompt_to_use: str = prompt if prompt else auto_prompt_to_process  # type: ignore[assignment]

        # Add user message
        st.session_state.coach_messages.append({"role": "user", "content": prompt_to_use})

        # Display user message immediately
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt_to_use)

                # Show article attachment if present
                if company_context and "article_title" in company_context:
                    with st.expander("📎 Attached Article", expanded=False):
                        st.markdown(f"**{company_context['article_title']}**")
                        st.caption(
                            f"{company_context['article_publisher']} • "
                            f"{company_context['article_date']}"
                        )
                        if company_context.get("article_url"):
                            st.markdown(f"[Read full article →]({company_context['article_url']})")

        # Generate coach response with staged verification
        with chat_container:
            with st.chat_message("assistant"):
                status_placeholder = st.empty()
                response_placeholder = st.empty()
                stop_button_placeholder = st.empty()
                full_response: str = ""

                # Stage 1: Generating
                status_placeholder.info("✍️ Generating response (subject to verification)...")

                # Initialize stop flag
                if "stop_generation" not in st.session_state:
                    st.session_state.stop_generation = False

                # Show stop button
                stop_clicked = stop_button_placeholder.button(
                    "⏹️ Stop Generating", key="stop_gen_btn", type="secondary"
                )

                if stop_clicked:
                    st.session_state.stop_generation = True

                # Get streaming response
                try:
                    stream = coach.ask(
                        question=prompt_to_use,
                        context=company_context,
                        conversation_history=st.session_state.coach_messages[:-1],
                        stream=True,
                    )

                    # Collect the full response with blurred streaming display
                    chunk_count = 0
                    for chunk in stream:
                        chunk_count += 1

                        if st.session_state.get("stop_generation", False):
                            full_response += "\n\n*[Generation stopped by user]*"
                            break

                        # Extract content from ChatResponse object
                        if hasattr(chunk, "message"):
                            message_content = chunk.message.content
                            if message_content:
                                full_response += str(message_content)
                                # Show heavily blurred during generation
                                response_placeholder.markdown(
                                    f'<div style="filter: blur(8px); '
                                    f"user-select: none; "
                                    f'color: #666;">'
                                    f"{full_response}</div>",
                                    unsafe_allow_html=True,
                                )
                finally:
                    # Always clear stop button and reset flag
                    stop_button_placeholder.empty()
                    st.session_state.stop_generation = False

                # Stage 2: Verifying
                status_placeholder.info("🔍 Verifying confidence level...")

                # Calculate confidence
                confidence = coach._estimate_confidence(full_response, company_context)

                # Check if response meets confidence threshold
                # Use the filter value from the dialog
                response_level = confidence_levels.get(confidence, 0)

                # Clear status
                status_placeholder.empty()

                # Decide whether to show response based on verification
                threshold_level = confidence_levels.get(user_threshold, 0)

                # If response doesn't meet threshold, hide it and show warning
                if response_level < threshold_level:
                    # Clear the response
                    response_placeholder.empty()

                    st.error(
                        f"🚨 **RESPONSE FILTERED: Below Your Confidence Threshold**\n\n"
                        f"This response has **{confidence.upper()}** confidence, "
                        f"but you've set your filter to "
                        f"**{user_threshold.upper()} or higher**.\n\n"
                        f"**The AI response has been hidden to protect you from "
                        f"potentially unreliable information.**"
                    )

                    st.info(
                        "**💡 To see this response, you can:**\n"
                        "- Lower your confidence filter in the sidebar\n"
                        "- Rephrase your question with more specific details\n"
                        "- Ask about a different topic"
                    )

                    # Show response in collapsed expander for reference
                    with st.expander("⚠️ Show filtered response (use with caution)"):
                        st.markdown(full_response)
                        st.caption(
                            "⚠️ This response was filtered due to low confidence. "
                            "Use this information with extreme caution and verify "
                            "with authoritative sources."
                        )
                else:
                    # Response meets threshold - show it with confidence badge
                    response_placeholder.markdown(full_response)

                    # Show confidence badge
                    if confidence == "high":
                        st.success("🟢 **High Confidence** - Reliable information")
                    elif confidence == "medium":
                        st.warning("🟡 **Medium Confidence** - Consider verifying")
                    elif confidence == "low":
                        st.error("🔴 **Low Confidence** - Consult additional sources")

                    # Generate confidence explanation
                    confidence_explanation = _generate_confidence_explanation(
                        confidence,
                        company_context is not None,
                        company_context,
                    )

                    # "Why this confidence?" explanation
                    with st.expander("❓ Why this confidence level?"):
                        st.markdown(confidence_explanation)

        # Generate confidence explanation for history (always needed)
        confidence_explanation = _generate_confidence_explanation(
            confidence,
            company_context is not None,
            company_context,
        )

        # Add assistant message to history
        st.session_state.coach_messages.append(
            {
                "role": "assistant",
                "content": full_response,
                "confidence": confidence,
                "confidence_explanation": confidence_explanation,
            }
        )

        # Note: We don't call st.rerun() here because:
        # 1. It would close the dialog (breaking the chat UX)
        # 2. The response is already visible above in the chat container
        # 3. On next interaction, the history will show all messages

    # Helpful tips when empty
    if len(st.session_state.coach_messages) == 0:
        st.info(
            """
            **💡 Try asking:**
            - "What does ROE mean?"
            - "Is a P/E of 30 high or low?"
            - "How do I read a cash flow statement?"
            - "What's the difference between debt and equity?"
            """
        )

    # Action buttons
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.coach_messages = []
        st.rerun()


def _generate_confidence_explanation(
    confidence: str, has_context: bool, context: dict | None
) -> str:
    """
    Generate explanation for why a specific confidence level was assigned

    Args:
        confidence: The confidence level (high/medium/low)
        has_context: Whether company context was available
        context: The context dict (if any)

    Returns:
        Human-readable explanation
    """
    explanations = []

    if confidence == "high":
        explanations.append("✓ Response uses confident, well-established terminology")
        if has_context and context:
            company = context.get("company_name", "the company")
            explanations.append(f"✓ Has specific context about {company}")
            if "metric_name" in context:
                metric = context["metric_name"]
                explanations.append(f"✓ Question relates to a specific metric ({metric})")
        explanations.append("✓ Answer follows standard financial education concepts")

    elif confidence == "medium":
        explanations.append(
            "⚠ Response contains some qualifiers or "
            "context-dependent statements\n\n"
            "⚠ No specific company context - answer is more general\n\n"
            "⚠ Topic may require additional verification "
            "for your specific situation"
        )

    elif confidence == "low":
        explanations.append("⚠ Response contains significant uncertainty or caveats")
        explanations.append(
            "⚠ Question may be too complex or context-specific for a general answer"
        )
        if not has_context:
            explanations.append("⚠ Missing company/metric context makes answer less reliable")
        explanations.append("⚠ Strongly recommend consulting additional authoritative sources")

    else:
        explanations.append("? Unable to determine confidence level")

    return "\n".join(explanations)
