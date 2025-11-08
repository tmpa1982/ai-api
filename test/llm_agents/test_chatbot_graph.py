import ast

from llm_agents.chatbot_graph import ChatBotGraph

def test_invoke(mocker):
    evaluation_response = {"score": 10}
    llm = mock_llm(mocker, evaluation_response=evaluation_response)

    message = run_test(llm)

    dictionary = ast.literal_eval(message)
    assert dictionary == evaluation_response

def test_need_for_clarification(mocker):
    clarifying_question = "Need more info"
    llm = mock_llm(mocker, clarifying_question=clarifying_question)

    message = run_test(llm)

    assert message == clarifying_question

def test_interview_question(mocker):
    interview_question = "What is the meaning of life?"
    llm = mock_llm(mocker, interview_question=interview_question)

    message = run_test(llm)

    assert message == interview_question

def mock_llm(mocker, **kwargs):
    llm = mocker.Mock()

    def _with_structured_output(schema):
        model = mocker.Mock()
        name = getattr(schema, '__name__', None)

        resp = mocker.Mock()
        if name == 'infoGathering':
            clarifying_question = kwargs.get("clarifying_question", None)
            resp.need_clarification = clarifying_question is not None
            resp.verification = "Verified"
            resp.job_description = "Job description"
            resp.interview_type = "Technical"
            resp.company_description = "Company"
            resp.model_dump.return_value = {"triage": "ok"}
            resp.question = clarifying_question
        elif name == 'InterviewProcess':
            interview_question = kwargs.get("interview_question", "")
            resp.end_interview = interview_question == ""
            resp.question = interview_question
        elif name == 'EvaluatorScoreCard':
            resp.model_dump.return_value = kwargs.get("evaluation_response", {"score": 10})
        else:
            raise ValueError(f"Unexpected schema: {name}")

        model.invoke.return_value = resp
        return model

    llm.with_structured_output.side_effect = _with_structured_output
    return llm

def run_test(llm):
    sut = ChatBotGraph(llm)

    message = "Hello, how are you?"
    terminate = False
    thread_id = "test-thread-1"

    response = sut.invoke(message, terminate, thread_id)
    assert response.thread_id == thread_id
    return response.message
