import json
from typing import List, Optional

import requests
from ovos_plugin_manager.templates.solvers import AbstractSolver


class OobaboogaChatCompletionsSolver(AbstractSolver):
    api_url = "https://api.openai.com/v1/chat/completions"

    def __init__(self, config=None, name="OpenAI Chat"):
        super().__init__(name=name, priority=50, config=config, enable_cache=False, enable_tx=False)
        self.engine = self.config.get("model", None)
        self.api_url = self.config.get("api_url", None)
        self.timeout = self.config.get("timeout", 600)
        self.max_tokens = self.config.get("max_tokens", 300)
        self.temperature = self.config.get("temperature", 1)
        self.top_p = self.config.get("top_p", 1)
        self.n = self.config.get("n", 1)
        self.frequency_penalty = self.config.get("frequency_penalty", 0)
        self.presence_penalty = self.config.get("presence_penalty", 2)
        self.stop_token = "<|im_end|>"
        self.memory = config.get("enable_memory", True)
        self.max_utts = config.get("memory_size", 15)
        self.qa_pairs = []  # tuple of q+a
        self.current_q = None
        self.current_a = None
        self.initial_prompt = config.get("initial_prompt") or "You are a helpful assistant."
        if not self.api_url:
            raise ValueError("Missing API URL for Oobabooga text-generation-ui!")
        if not self.engine:
            raise ValueError("Missing LLM engine for Oobabooga text-generation-ui!")

    # OpenAI API integration
    def _do_api_request(self, messages: List[dict]) -> str:
        """Perform API request to text-generation-ui's openai extension API.

        Args:
            messages (_type_): A list of JSON dicts comprising the conversation so far.

        Returns:
            str: The LLM's response
        """
        headers = {"Content-Type": "application/json"}

        # https://platform.openai.com/docs/api-reference/completions/create
        payload = {
            "model": self.engine,
            "messages": messages,  # The conversation so far, including the user messages and bot messages.
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            # between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2
            # will make it more focused and deterministic.
            "top_p": self.top_p,
            # nucleus sampling alternative to temperature, the model considers the results of the tokens with top_p
            # probability mass. 0.1 means only tokens comprising top 10% probability mass are considered.
            "n": self.n,  # How many completions to generate for each prompt.
            "frequency_penalty": self.frequency_penalty,
            # Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency
            # in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
            "presence_penalty": self.presence_penalty,
            # Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the
            # text so far, increasing the model's likelihood to talk about new topics.
            "stop": self.stop_token,
        }
        response = requests.post(self.api_url, headers=headers, data=json.dumps(payload), timeout=30).json()
        return response["choices"][0]["message"]["content"]

    def get_chat_history(self, initial_prompt=None) -> List[dict]:
        """Get the chat history so far, including the user messages and bot messages.

        Args:
            initial_prompt (str, optional): The initial prompt to use. Defaults to None.

        Returns:
            list: A list of JSON dicts comprising the conversation so far.
        """
        qa = self.qa_pairs[-1 * self.max_utts :]
        initial_prompt = self.initial_prompt or "You are a helpful assistant."
        messages = [
            {"role": "system", "content": initial_prompt},
        ]
        for q, a in qa:
            messages.append({"role": "user", "content": q})
            messages.append({"role": "assistant", "content": a})
        return messages

    def get_prompt(self, utt: str, initial_prompt: Optional[str] = None) -> List[dict]:
        """Get the prompt to send to the LLM.

        Args:
            utt (str): The user's utterance.
            initial_prompt (str, optional): The initial prompt to use. Defaults to None.

        Returns:
            List[str]: The chat history.
        """
        self.current_q = None
        self.current_a = None
        messages = self.get_chat_history(initial_prompt)
        messages.append({"role": "user", "content": utt})
        return messages

    # officially exported Solver methods
    def get_spoken_answer(self, query: str, context: Optional[str] = None) -> Optional[str]:
        """Get the LLM's response to the user's query.

        Args:
            query (str): The user's query.
            context (str, optional): The message context. Defaults to None.

        Returns:
            str, optional: The LLM's response.
        """
        _ = context  # TODO: Implement context
        messages = self.get_prompt(query)
        response = self._do_api_request(messages)
        answer = response.strip()
        if not answer or not answer.strip("?") or not answer.strip("_"):
            return None
        if self.memory:
            self.qa_pairs.append((query, answer))
        return answer


class OobaboogaPersonaSolver(OobaboogaChatCompletionsSolver):
    """default "Persona" engine"""

    def __init__(self, config=None):
        super().__init__(name="OpenAI ChatGPT Persona", config=config)
        self.default_persona = config.get("persona") or "helpful, creative, clever, and very friendly."

    def get_chat_history(self, persona=None):
        qa = self.qa_pairs[-1 * self.max_utts :]
        persona = persona or self.default_persona
        initial_prompt = f"You are a helpful assistant. " f"You give short and factual answers. " f"You are {persona}"
        messages = [
            {"role": "system", "content": initial_prompt},
        ]
        for q, a in qa:
            messages.append({"role": "user", "content": q})
            messages.append({"role": "assistant", "content": a})
        return messages

    # officially exported Solver methods
    def get_spoken_answer(self, query, context=None):
        context = context or {}
        persona = context.get("persona") or self.default_persona
        messages = self.get_prompt(query, persona)
        response = self._do_api_request(messages)
        answer = response.strip()
        if not answer or not answer.strip("?") or not answer.strip("_"):
            return None
        if self.memory:
            self.qa_pairs.append((query, answer))
        return answer


if __name__ == "__main__":
    bot = OobaboogaPersonaSolver({"api_url": "http://100.118.163.108:7860/"})  # TODO: Right URL
    print(bot.get_spoken_answer("describe quantum mechanics in simple terms"))
    # Quantum mechanics is a branch of physics that deals with the behavior of particles on a very small scale,
    # such as atoms and subatomic particles. It explores the idea that particles can exist in multiple states at once
    # and that their behavior is not predictable in the traditional sense.
    print(bot.spoken_answer("Quem encontrou o caminho maritimo para o Brazil", {"lang": "pt-pt"}))
    # Explorador português Pedro Álvares Cabral é creditado com a descoberta do Brasil em 1500
